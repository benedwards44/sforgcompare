from __future__ import absolute_import
from celery import Celery
from django.conf import settings
from difflib import HtmlDiff
from django.core.mail import send_mail
from postmark import PMMail
from suds.client import Client
from base64 import b64decode
from zipfile import ZipFile
import os
import json	
import requests
import datetime
import time

# Celery config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sforgcompare.settings')
app = Celery('tasks', broker=os.environ.get('REDISTOGO_URL', 'redis://localhost'))

# Import models
from compareorgs.models import Job, Org, ComponentType, Component

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

			# set up the component type to query for components
			component = metadata_client.factory.create("ListMetadataQuery")
			component.type = component_type.xmlName

			# Add metadata to list
			component_list.append(component)

			# Run the metadata query only if the list has reached 3 (the max allowed to query)
			# at one time, or if there is less than 3 components left to query 
			if len(component_list) == 3 or (len(all_metadata[0]) - loop_counter) <= 3:

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
		for component_type in ComponentType.objects.filter(org = org):

			# Loop through child components of the component type
			for component in component_type.component_set.all():

				component_to_retrieve = metadata_client.factory.create('PackageTypeMembers')
				component_to_retrieve.members = component.name
				component_to_retrieve.name = component_type.name
				component_retrieve_list.append(component_to_retrieve)

		print 'HELLO3 ' + component_retrieve_list
				
		# The overall package to retrieve
		package_to_retrieve = metadata_client.factory.create('Package')
		package_to_retrieve.apiAccessLevel = None
		package_to_retrieve.types = component_retrieve_list

		# Add retrieve package to the retrieve request
		retrieve_request.unpackaged = package_to_retrieve

		print 'BEFORE JOB'

		# Start the async retrieve job
		retrieve_job = metadata_client.service.retrieve(retrieve_request)

		print 'AFTER JOB'

		print 'HELLO4 ' + retrieve_job

		# Set the retrieve result - should be unfinished initially
		retrieve_result = metadata_client.service.checkRetrieveStatus(retrieve_job.id)

		print 'HELLO5 ' + retrieve_result

		# Continue to query retrieve result until it's done
		while not retrieve_result.done:

			# check job status
			retrieve_result = metadata_client.service.checkRetrieveStatus(retrieve_job.id)

			# sleep job for 5 seconds
			time.sleep(5)

		if not retrieve_result.success:

			org.status = 'Error'
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
					component_record.name = component_name
					component_record.content = metadata.read(filename)
					component_record.save()

				# not in a folder (could be package.xml). Skip record
				except:
					continue

			org.status = 'Finished'

	except Exception as error:
		org.status = 'Error'
		org.error = 'Line: ' + sys.exc_info().tb_lineno + '\n\n' + error

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
		org.error = 'Line: ' + sys.exc_info().tb_lineno + '\n\n' + error

	org.save()

	# Check if both jobs are now finished
	check_overall_status(job)


# Compare two Org's metadata and return results
def compare_orgs_task(job):

	job.status = 'Comparing'
	job.save()

	try:

		org_left = job.sorted_orgs()[0]
		org_right = job.sorted_orgs()[1]

		html_output = '<table class="table table-hover" id="compare_results_table">'
		html_output += '<thead>'
		html_output += '<tr>'
		html_output += '<th><h2>' + org_left.username  + ' (' + org_left.org_name + ')</h2></th>'
		html_output += '<th><h2>' + org_right.username + ' (' + org_right.org_name + ')</h2></th>'
		html_output += '</th>'
		html_output += '</thead>'
		html_output += '<tbody>'

		# Map of name to component
		component_map = {}

		# Create a list of the left component type names
		left_components = []
		for component_type in org_left.sorted_component_types():
			left_components.append(component_type.name)

			# Append components
			for component in component_type.sorted_components():
				left_components.append(component_type.name + '.' + component.name)
				component_map['left' + component_type.name + '.' + component.name] = component

		# Create a list of the right component type names
		right_components = []
		for component_type in org_right.sorted_component_types():
			right_components.append(component_type.name)
			
			for component in component_type.sorted_components():
				right_components.append(component_type.name + '.' + component.name)
				component_map['right' + component_type.name + '.' + component.name] = component

		# Start the unique list
		all_components_unique = list(left_components)

		# Add all right components that aren't in the list
		for component_type in right_components:
			if component_type not in all_components_unique:
				all_components_unique.append(component_type)

		# Sort alphabetically
		all_components_unique.sort()

		# Start to build the HTML for the table
		for row_value in all_components_unique:

			if row_value in left_components and row_value not in right_components:

				if '.' not in row_value:

					html_output += '<tr class="type type_' + row_value + '">'
					html_output += '<td>'
					html_output += row_value
					html_output += '</td>'
					html_output += '<td></td>'
					html_output += '</tr>'

				else:

					html_output += '<tr class="component danger component_' + row_value.split('.')[0] + '">'
					html_output += '<td id="' + row_value + '" class="left_only">'
					html_output += row_value.split('.')[1]
					html_output += '<textarea style="display:none;">' +  component_map['left' + row_value].content + '</textarea>'
					html_output += '</td>'
					html_output += '<td></td>'
					html_output += '</tr>'


			elif row_value not in left_components and row_value in right_components:

				if '.' not in row_value:

					html_output += '<tr class="type type_' + row_value + '">'
					html_output += '<td></td>'
					html_output += '<td>'
					html_output += row_value
					html_output += '</td>'
					html_output += '</tr>'

				else:

					html_output += '<tr class="component danger component_' + row_value.split('.')[0] + '">'
					html_output += '<td></td>'
					html_output += '<td id="' + row_value + '" class="right_only">'
					html_output += row_value.split('.')[1]
					html_output += '<textarea style="display:none;">' +  component_map['right' + row_value].content + '</textarea>'
					html_output += '</td>'
					html_output += '</tr>'

			elif row_value in left_components and row_value in right_components:

				if '.' not in row_value:

					html_output += '<tr class="type type_' + row_value + '">'
					html_output += '<td>'
					html_output += row_value
					html_output += '</td>'
					html_output += '<td>'
					html_output += row_value
					html_output += '</td>'
					html_output += '</tr>'

				else:

					# If identical 
					if component_map['left' + row_value].content == component_map['right' + row_value].content:

						html_output += '<tr class="component success component_' + row_value.split('.')[0] + '">'
						html_output += '<td id="' + row_value + '" class="both_same">'
						html_output += row_value.split('.')[1]
						html_output += '<textarea style="display:none;">' +  component_map['left' + row_value].content + '</textarea>'
						html_output += '</td>'
						html_output += '<td id="' + row_value + '" class="both_same">'
						html_output += row_value.split('.')[1]
						html_output += '</td>'
						html_output += '</tr>'

					# Files differ - time to compare
					else:

						print 'Start Diff'

						diff_tool = HtmlDiff()
						diff_html = diff_tool.make_table(component_map['left' + row_value].content.split('\n'), component_map['right' + row_value].content.split('\n'), context=True)

						html_output += '<tr class="component warning component_' + row_value.split('.')[0] + '">'
						html_output += '<td id="' + row_value + '" class="diff">'
						html_output += row_value.split('.')[1]
						html_output += '<textarea style="display:none;">' +  diff_html + '</textarea>'
						html_output += '</td>'
						html_output += '<td id="' + row_value + '" class="diff">'
						html_output += row_value.split('.')[1]
						html_output += '</td>'
						html_output += '</tr>'

						print 'End Diff'

		html_output += '</tbody>'
		html_output += '</table>'

		job.compare_result_html = html_output
		job.status = 'Finished'

		email_body = 'Your Org compare job is complete:\n'
		email_body += 'https://sforgcompare.herokuapp.com/compare_result/' + str(job.id)
		email_body += '\n\nYour result will be deleted in an hour, or when you view the result.'

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
		email_body += error
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

