from __future__ import absolute_import
from celery import Celery
from django.conf import settings
import os
import json	
import requests

# Celery config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sforgcompare.settings')
app = Celery('tasks', broker=os.environ.get('REDISTOGO_URL', 'redis://localhost'))

# Import models
from compareorgs.models import Job, Org, ComponentType, Component

# Downloading metadata using the Tooling API
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
				for component in metadata_client.service.listMetadata(component_list,api_version):

					# Query database for parent component_type
					component_type_query = ComponentType.objects.filter(name = component.type, org = org.id)

					# Only add if found
					if component_type_query:

						# create the component record and save
						component_record = Component()
						component_record.component_type = component_type_query[0]
						component_record.name = component.fullName
						#component_record.content = #xxx
						component_record.save()
		
				# clear list once done. This list will re-build to 3 components and re-query the service
				component_list = []

			loop_counter = loop_counter + 1;

		# If a component type has no child components, remove the component type altogether
		for component_type in ComponentType.objects.filter(org = org.id):
			if not Component.objects.filter(component_type = component_type.id):
				component_type.delete()

		org.status = 'Finished'

	except Exception as error:
		org.status = 'Error'
		org.error = error

	org.save()

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

		metadata_types = []

		desribe_result = requests.get(tooling_url + 'sobjects/', headers = headers)

		# Success
		if desribe_result.status_code == requests.codes.ok:

			for component_type in requests.get(tooling_url + 'sobjects/', headers = headers).json()['sobjects']:
				
				# Only add retrieveable components
				if component_type['retrieveable'] == True:	
					metadata_types.append(component_type['name'])

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

						if 'Body' in record.json():

							# create the component record and save
							component_record = Component()
							component_record.component_type = component_type_record
							component_record.name = record.json()['FullName']
							component_record.content = record.json()['Body']
							component_record.save()

							count_children += 1

					if count_children == 0:
						component_type_record.delete()

			org.status = 'Finished'

		# Error in REST request
		else:

			org.status = 'Error'
			org.error = metadata_types.json()[0]['message']


	except Exception as error:
		org.status = 'Error'
		org.error = error

	org.save()


# Compare two Org's metadata and return results
@app.task
def compare_orgs(job):

	try:
		pass

	except Exception as error:
		job.status = 'Error'
		job.error = error

	job.save()


