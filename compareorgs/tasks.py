from __future__ import absolute_import
from celery import Celery
import os
import json	
import requests
import datetime
import time
import sys
import sqlite3
import StringIO
import glob

# Celery config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sforgcompare.settings')
app = Celery('tasks', broker=os.environ.get('REDISTOGO_URL', 'redis://localhost'))

# Import models
from compareorgs.models import Job, Org, ComponentType, Component, ComponentListUnique, OfflineFileJob
from django.core.files.storage import default_storage as s3_storage
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.core.files import File
from django.conf import settings
from difflib import HtmlDiff
from django.core.mail import send_mail
from postmark import PMMail
from suds.client import Client
from base64 import b64decode
from zipfile import ZipFile
from django.template import RequestContext, Context, Template, loader
from boto.s3.connection import S3Connection
from boto.s3.key import Key

reload(sys)
sys.setdefaultencoding("utf-8")

# Downloading metadata using the Metadata API
# https://www.salesforce.com/us/developer/docs/api_meta/
@app.task
def download_metadata_metadata(job, org):

	org.status = 'Downloading Metadata'
	org.save()

	try:

		# instantiate the metadata WSDL
		metadata_client = Client('http://sforgcompare.herokuapp.com/static/metadata-32.xml')

		# URL for metadata API
		metadata_url = org.instance_url + '/services/Soap/m/' + str(settings.SALESFORCE_API_VERSION) + '.0/' + org.org_id

		# set the metadata url based on the login result
		metadata_client.set_options(location = metadata_url)

		# set the session id from the login result
		session_header = metadata_client.factory.create("SessionHeader")
		session_header.sessionId = org.access_token
		metadata_client.set_options(soapheaders = session_header)
		
		# query for the list of metadata types
		all_metadata = metadata_client.service.describeMetadata(settings.SALESFORCE_API_VERSION)

		# Components for listing metadata
		component_list = []
		loop_counter = 0;

		# loop through metadata types
		for component_type in all_metadata[0]:

			# create the component type record and save
			component_type_record = ComponentType()
			component_type_record.org = org
			component_type_record.name = component_type.xmlName
			component_type_record.save()

			# Component is a folder component - eg Dashboard, Document, EmailTemplate, Report
			if not component_type.inFolder:

				# set up the component type to query for components
				component = metadata_client.factory.create("ListMetadataQuery")
				component.type = component_type.xmlName

				# Add metadata to list
				component_list.append(component)
			
			else:

				# Append "Folder" keyword onto end of component type
				component = metadata_client.factory.create("ListMetadataQuery")

				# EmailTemplate = EmailFolder (for some reason)
				if component_type.xmlName == 'EmailTemplate':
					component.type = 'EmailFolder'
				else:
					component.type = component_type.xmlName + 'Folder'

				# All folders for specified metadata type
				all_folders = metadata_client.service.listMetadata([component], settings.SALESFORCE_API_VERSION)
				folder_list = []
				folder_loop_counter = 0

				# Loop through folders
				for folder in all_folders:

					# Create component for folder to query
					folder_component = metadata_client.factory.create("ListMetadataQuery")
					folder_component.type = component_type.xmlName
					folder_component.folder = folder.fullName

					folder_list.append(folder_component)

					if len(folder_list) >= 3 or (len(all_folders) - folder_loop_counter) <= 3:

						# Loop through folder components
						for folder_component in metadata_client.service.listMetadata(folder_list, settings.SALESFORCE_API_VERSION):

							# create the component record and save
							component_record = Component()
							component_record.component_type = component_type_record
							component_record.name = folder_component.fullName
							component_record.save()

						folder_list = []

					folder_loop_counter = folder_loop_counter + 1

			# Run the metadata query only if the list has reached 3 (the max allowed to query)
			# at one time, or if there is less than 3 components left to query 
			if len(component_list) >= 3 or (len(all_metadata[0]) - loop_counter) <= 3:

				# loop through the components returned from the component query
				for component in metadata_client.service.listMetadata(component_list, settings.SALESFORCE_API_VERSION):

					# Query database for parent component_type
					component_type_query = ComponentType.objects.filter(name = component.type, org = org.id)

					# Only add if found
					if component_type_query:

						# create the component record and save
						component_record = Component()
						component_record.component_type = component_type_query[0]
						component_record.name = component.fullName
						component_record.save()
		
				# clear list once done. This list will re-build to 3 components and re-query the service
				component_list = []

			loop_counter = loop_counter + 1;

		# If a component type has no child components, remove the component type altogether
		for component_type in ComponentType.objects.filter(org = org.id):
			if not Component.objects.filter(component_type = component_type.id):
				component_type.delete()

		# Create retrieve request
		retrieve_request = metadata_client.factory.create('RetrieveRequest')
		retrieve_request.apiVersion = settings.SALESFORCE_API_VERSION
		retrieve_request.singlePackage = True
		retrieve_request.packageNames = None
		retrieve_request.specificFiles = None

		component_retrieve_list = []

		# Now query through all components and download actual metadata
		for component_type in ComponentType.objects.filter(org = org.id):

			# Loop through child components of the component type
			for component in component_type.component_set.all():

				component_to_retrieve = metadata_client.factory.create('PackageTypeMembers')
				component_to_retrieve.members = component.name
				component_to_retrieve.name = component_type.name
				component_retrieve_list.append(component_to_retrieve)

		# The overall package to retrieve
		package_to_retrieve = metadata_client.factory.create('Package')
		package_to_retrieve.apiAccessLevel = None
		package_to_retrieve.types = component_retrieve_list

		# Add retrieve package to the retrieve request
		retrieve_request.unpackaged = package_to_retrieve

		# Start the async retrieve job
		retrieve_job = metadata_client.service.retrieve(retrieve_request)

		# Set the retrieve result - should be unfinished initially
		retrieve_result = metadata_client.service.checkRetrieveStatus(retrieve_job.id)

		# Continue to query retrieve result until it's done
		while not retrieve_result.done:

			# check job status
			retrieve_result = metadata_client.service.checkRetrieveStatus(retrieve_job.id)

			# sleep job for 5 seconds
			time.sleep(10)

		if not retrieve_result.success:

			org.status = 'Error'

			if 'errorMessage' in retrieve_result:
				org.error = retrieve_result.errorMessage
			elif 'messages' in retrieve_result:
				org.error = retrieve_result.messages[0]
			
		else:

			# Save the zip file result to server
			zip_file = open('metadata.zip', 'w+')
			zip_file.write(b64decode(retrieve_result.zipFile))
			zip_file.close()

			# Delete all existing components for package - they need to be renamed
			ComponentType.objects.filter(org = org.id).delete()

			# Open zip file
			metadata = ZipFile('metadata.zip', 'r')

			# Loop through files in the zip file
			for filename in metadata.namelist():

				try:

					# Set folder and component name
					folder_name = filename.split('/')[0]
					component_name = filename.split('/')[1]

					# Check if component type exists
					if ComponentType.objects.filter(org = org.id, name = folder_name):

						# If exists, use this as parent component type
						component_type_record = ComponentType.objects.filter(org = org.id, name = folder_name)[0]

					else:

						# create the component type record and save
						component_type_record = ComponentType()
						component_type_record.org = org
						component_type_record.name = folder_name
						component_type_record.save()

					# create the component record and save
					component_record = Component()
					component_record.component_type = component_type_record

					# If more / exist, append
					if len(filename.split('/')) > 2:
						component_record.name = component_name + '/' + filename.split('/')[2]
					else:
						component_record.name = component_name
					component_record.content = metadata.read(filename)
					component_record.save()

				# not in a folder (could be package.xml). Skip record
				except:
					continue

			# Delete zip file, no need to store
			os.remove('metadata.zip')

			org.status = 'Finished'

	except Exception as error:
		org.status = 'Error'
		org.error = error

	org.save()

	# Check if both jobs are now finished
	check_overall_status(job)

# Downloading metadata using the Tooling API
# http://www.salesforce.com/us/developer/docs/api_tooling/index.htm
@app.task
def download_metadata_tooling(job, org):

	org.status = 'Downloading Metadata'
	org.save()
	
	try:
		
		tooling_url = org.instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/tooling/'
		headers = { 
			'Accept': 'application/json',
			'Authorization': 'Bearer ' + org.access_token
		}

		metadata_types = [
			'ApexClass',
			'ApexComponent',
			'ApexPage',
			'ApexTrigger',
		]

		for component_type in metadata_types:

			data_query = 'select+id+from+' + component_type
			metadata_records = requests.get(tooling_url + 'query/?q=' + data_query, headers = headers)
			
			# Only continue if records exist to query
			if 'records' in metadata_records.json():

				# create the component type record and save
				component_type_record = ComponentType()
				component_type_record.org = org
				component_type_record.name = component_type
				component_type_record.save()

				count_children = 0

				for component in metadata_records.json()['records']:

					metadata_url = org.instance_url + component['attributes']['url']

					record = requests.get(metadata_url, headers = headers)

					# Only take non package components
					if record.json()['NamespacePrefix'] == None:

						# create the component record and save
						component_record = Component()
						component_record.component_type = component_type_record
						
						if component_type == 'ApexPage' or component_type == 'ApexComponent':
							component_record.name = record.json()['Name']
							component_record.content = record.json()['Markup']

						#ApexClass or ApexTrigger
						else:
							component_record.name = record.json()['FullName']
							component_record.content = record.json()['Body']
							
						component_record.save()

						count_children += 1

				if count_children == 0:
					component_type_record.delete()

			org.status = 'Finished'

	except Exception as error:
		org.status = 'Error'
		org.error = error

	org.save()

	# Check if both jobs are now finished
	check_overall_status(job)


@app.task
def create_offline_file(job, offline_job):

	offline_job.status = 'Running'
	offline_job.save()

	try:

		# Temp dir string 
		temp_dir = job.random_id

		# Create the directory
		os.mkdir(temp_dir)

		# Temp dir string
		temp_dir_string = temp_dir + '/'

		# Create sqlite database
		conn = sqlite3.connect(temp_dir_string + 'components.db')

		c = conn.cursor()

		# Create component diff table
		c.execute('''CREATE TABLE component_diff
	             (id integer, diff_html text)''')

		component_records = []

		# Add data to diff table
		for component in job.sorted_component_list():
			if component.diff_html:
				component_records.append((str(component.id), component.diff_html))

		# Insert into database
		c.executemany('INSERT INTO component_diff VALUES (?,?)', component_records)

		# Create component table
		c.execute('''CREATE TABLE component
	             (id integer, metadata text)''')

		component_records = []

		# Add data
		for component in Component.objects.filter(component_type__org__in = [job.sorted_orgs()[0],job.sorted_orgs()[1]]):
			component_records.append((str(component.id), component.content))

		# Insert into database
		c.executemany('INSERT INTO component VALUES (?,?)', component_records)

		# Save (commit) the changes
		conn.commit()

		# We can also close the connection if we are done with it.
		# Just be sure any changes have been committed or they will be lost.
		conn.close()

		# Create html file
		compare_result = open(temp_dir_string + 'compare_results_offline.html','w+')

		# Build the html using the template contentxt
		t = loader.get_template('compare_results_offline.html')
		c = Context({ 
			'org_left_username': job.sorted_orgs()[0].username, 
			'org_right_username': job.sorted_orgs()[1].username, 
			'html_rows': ''.join(list(job.sorted_component_list().values_list('row_html', flat=True)))
		})

		# Write template contents to file
		compare_result.write(t.render(c))
		compare_result.close()

		# Create zip file for all content
		zip_file = ZipFile(temp_dir_string + 'compare_results.zip', 'w')

		# Add database
		zip_file.write(temp_dir_string + 'components.db', 'data/components.db')

		# Add html file
		zip_file.write(temp_dir_string + 'compare_results_offline.html', 'compare_results_offline.html')

		# Add all static files
		for root, dirs, files in os.walk('staticfiles'):
			for file in files:
				zip_file.write(os.path.join(root, file))

		# Close the file
		zip_file.close()

		# Re-open the file
		zip_file = open(temp_dir_string + 'compare_results.zip')

		# Save file to model
		job.zip_file.save(temp_dir + '.zip', File(zip_file))
		job.save()

		# Close the file again
		zip_file.close()

		# Remove the files and directories
		for f in glob.glob(temp_dir_string + '*'):
			os.remove(f)
		os.rmdir(temp_dir)

		# Update status to finished
		offline_job.status = 'Finished'

	except Exception as error:

		offline_job.status = 'Error'
		offline_job.error = error

	offline_job.save()


# Compare two Org's metadata and return results
def compare_orgs_task(job):

	job.status = 'Comparing'
	job.save()

	try:

		org_left = job.sorted_orgs()[0]
		org_right = job.sorted_orgs()[1]

		# Map of name to component
		component_type_map = {}
		component_map = {}

		# Create a list of the left component type names
		left_components = []
		for component_type in org_left.sorted_component_types():

			left_components.append(component_type.name)
			component_type_map['left' + component_type.name] = component_type

			# Append components
			for component in component_type.sorted_components():
				left_components.append(component_type.name + '***' + component.name)
				component_map['left' + component_type.name + '***' + component.name] = component

		# Create a list of the right component type names
		right_components = []
		for component_type in org_right.sorted_component_types():

			right_components.append(component_type.name)
			component_type_map['right' + component_type.name] = component_type
			
			for component in component_type.sorted_components():
				right_components.append(component_type.name + '***' + component.name)
				component_map['right' + component_type.name + '***' + component.name] = component

		# Start the unique list
		all_components_unique = list(left_components)

		# Add all right components that aren't in the list
		for component_type in right_components:

			if component_type not in all_components_unique:

				all_components_unique.append(component_type)

		# Sort alphabetically
		all_components_unique.sort()

		order_counter = 0

		# Start to build the HTML for the table
		for row_value in all_components_unique:

			order_counter = order_counter + 1

			component_result = ComponentListUnique()
			component_result.job = job
			component_result.order = order_counter
			component_result.save() # save now as we need ID

			# Generating HTML here to speed up page load performance on the front end
			row_html = ''

			if row_value in left_components and row_value not in right_components:

				if '***' not in row_value:

					row_html += '<tr class="type type_' + component_type_map['left' + row_value].name + '">'
					row_html += '<td>' + component_type_map['left' + row_value].name + '</td>'
					row_html += '<td></td>'
					row_html += '</tr>'

				else:

					row_html += '<tr class="component danger component_' + component_map['left' + row_value].component_type.name + '">'
					row_html += '<td id="' + str(component_map['left' + row_value].id) + '">' + component_map['left' + row_value].name + '</td>'
					row_html += '<td id="' + str(component_map['left' + row_value].id) + '"></td>'
					row_html += '</tr>'
					
			elif row_value not in left_components and row_value in right_components:
				
				if '***' not in row_value:

					row_html += '<tr class="type type_' + component_type_map['right' + row_value].name + '">'
					row_html += '<td></td>'
					row_html += '<td>' + component_type_map['right' + row_value].name + '</td>'
					row_html += '</tr>'

				else:

					row_html += '<tr class="component danger component_' + component_map['right' + row_value].component_type.name + '">'
					row_html += '<td id="' + str(component_map['right' + row_value].id) + '"></td>'
					row_html += '<td id="' + str(component_map['right' + row_value].id) + '">' + component_map['right' + row_value].name + '</td>'
					row_html += '</tr>'

			elif row_value in left_components and row_value in right_components:

				if '***' not in row_value:

					row_html += '<tr class="type type_' + component_type_map['left' + row_value].name + '">'
					row_html += '<td>' + component_type_map['left' + row_value].name + '</td>'
					row_html += '<td>' + component_type_map['right' + row_value].name + '</td>'
					row_html += '</tr>'

				else:

					# If diff exists
					if component_map['left' + row_value].content != component_map['right' + row_value].content:

						# Content for comparison
						left_content = component_map['left' + row_value].content.split('\n')
						right_content = component_map['right' + row_value].content.split('\n')

						# Instantiate Python diff tool
						diff_tool = HtmlDiff()

						# If contextual diff, compare results differently
						if job.contextual_diff:

							component_result.diff_html = diff_tool.make_table(left_content, right_content, context=True, numlines=5)

						# Otherwise, no contextual diff required
						else:

							component_result.diff_html = diff_tool.make_table(left_content, right_content)
				
						row_html += '<tr class="component warning component_' + component_map['left' + row_value].component_type.name + '">'
						row_html += '<td id="' + str(component_result.id) + '" class="diff">' + component_map['left' + row_value].name + '</td>'
						row_html += '<td id="' + str(component_result.id) + '" class="diff">' + component_map['right' + row_value].name + '</td>'
						row_html += '</tr>'

					else:

						row_html += '<tr class="component success component_' + component_map['left' + row_value].component_type.name + '">'
						row_html += '<td id="' + str(component_map['left' + row_value].id) + '" class="both_same">' + component_map['left' + row_value].name + '</td>'
						row_html += '<td id="' + str(component_map['right' + row_value].id) + '" class="both_same">' + component_map['right' + row_value].name + '</td>'
						row_html += '</tr>'

			component_result.row_html = row_html		
			component_result.save()

			job.status = 'Finished'

			email_body = 'Your Org compare job is complete:\n'
			email_body += 'https://sforgcompare.herokuapp.com/compare_result/' + str(job.random_id)
			email_body += '\n\nYour result will be deleted after one day in order to avoid storing any metadata.'

			email_subject = 'Your Salesforce Org Compare results are ready.'

	except Exception as error:

		job.status = 'Error'
		job.error = error

		send_error_email(job, error)


	job.finished_date = datetime.datetime.now()
	job.save()

	if job.email_result and job.status == 'Finished':
		#send_mail('Your Org Compare Results', email_body, 'ben@tquila.com', [job.email], fail_silently=False)
		message = PMMail(api_key = os.environ.get('POSTMARK_API_KEY'),
				subject = email_subject,
                sender = "ben@tquila.com",
                to = job.email,
                text_body = email_body,
                tag = "orgcompareemail")
		message.send()


def check_overall_status(job):

	# Check if both jobs are now finished
	all_orgs = Org.objects.filter(job = job)
	
	if len(all_orgs) == 2:

		if all_orgs[0].status == 'Error' or all_orgs[1].status == 'Error':

			if all_orgs[0].status == 'Error':

				job.status = 'Error'
				job.error = all_orgs[0].error
				job.save()

				send_error_email(job, job.error)

			if all_orgs[1].status == 'Error':

				job.status = 'Error'
				job.error = all_orgs[1].error
				job.save()

				send_error_email(job, job.error)

		elif all_orgs[0].status == 'Finished' and all_orgs[1].status == 'Finished':

			compare_orgs_task(job)

def send_error_email(job, error):

	if job.email_result:

		email_body = 'There was an error processing your job:\n'
		email_body += str(error)
		email_body += '\n\nPlease try again.'

		email_subject = 'Error running Salesforce Org Compare job.'

		#send_mail('Your Org Compare Results', email_body, 'ben@tquila.com', [job.email], fail_silently=False)
		message = PMMail(api_key = os.environ.get('POSTMARK_API_KEY'),
				subject = email_subject,
	            sender = "ben@tquila.com",
	            to = job.email,
	            text_body = email_body,
	            tag = "orgcompareemail")
		message.send()

