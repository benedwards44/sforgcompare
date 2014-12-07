from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from compareorgs.models import Job, Org, ComponentType, Component
from compareorgs.forms import JobForm
import json	
import requests
import datetime
from time import sleep
from compareorgs.tasks import download_metadata_metadata, download_metadata_tooling


def index(request):

	client_id = settings.SALESFORCE_CONSUMER_KEY
	redirect_uri = settings.SALESFORCE_REDIRECT_URI

	if request.POST:

		job_form = JobForm(request.POST)

		if job_form.is_valid():

			job = Job()
			job.created_date = datetime.datetime.now()
			job.status = 'Not Started'
			job.email = job_form.cleaned_data['email']
			if job_form.cleaned_data['email_choice'] == 'yes':
				job.email_result = True
			else:
				job.email_result = False
			job.save()

			org_one = Org.objects.get(pk = job_form.cleaned_data['org_one'])
			org_one.job = job
			org_one.save()

			org_two = Org.objects.get(pk = job_form.cleaned_data['org_two'])
			org_two.job = job
			org_two.save()

			return HttpResponseRedirect('/compare_orgs/' + str(job.id) + '/?api=' + job_form.cleaned_data['api_choice'])

	else:
		job_form = JobForm()

	return render_to_response('index.html', RequestContext(request,{'client_id': client_id, 'redirect_uri': redirect_uri, 'job_form': job_form}))

def oauth_response(request):

	error_exists = False
	error_message = ''
	username = ''
	email = ''
	org_name = ''
	org = Org()

	# On page load
	if request.GET:

		oauth_code = request.GET.get('code')
		environment = request.GET.get('state')[:-4]
		org_choice = request.GET.get('state')[-4:]
		access_token = ''
		instance_url = ''
		org_id = ''

		if 'Production' in environment:

			login_url = 'https://login.salesforce.com'
			
		else:

			login_url = 'https://test.salesforce.com'
		
		r = requests.post(login_url + '/services/oauth2/token', headers={ 'content-type':'application/x-www-form-urlencoded'}, data={'grant_type':'authorization_code','client_id': settings.SALESFORCE_CONSUMER_KEY,'client_secret':settings.SALESFORCE_CONSUMER_SECRET,'redirect_uri': settings.SALESFORCE_REDIRECT_URI,'code': oauth_code})
		auth_response = json.loads(r.text)

		if 'error_description' in auth_response:

			error_exists = True
			error_message = auth_response['error_description']

		else:

			access_token = auth_response['access_token']
			instance_url = auth_response['instance_url']
			user_id = auth_response['id'][-18:]
			org_id = auth_response['id'][:-19]
			org_id = org_id[-18:]

			# get username of the authenticated user
			r = requests.get(instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/sobjects/User/' + user_id + '?fields=Username,Email', headers={'Authorization': 'OAuth ' + access_token})
			
			if 'errorCode' in r.text:

				error_exists = True
				error_message = r.json()[0]['message']

			else:

				username = r.json()['Username']
				email = r.json()['Email']

				# get the org name of the authenticated user
				r = requests.get(instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/sobjects/Organization/' + org_id + '?fields=Name', headers={'Authorization': 'OAuth ' + access_token})
				
				if 'errorCode' in r.text:

					error_exists = True
					error_message = r.json()[0]['message']

				else:

					org_name = r.json()['Name']

					org = Org()
					org.access_token = access_token
					org.instance_url = instance_url
					org.org_id = org_id
					org.org_name = org_name
					org.username = username
					
					if org_choice == 'org1':

						org.org_number = 1

					else:

						org.org_number = 2

					org.save()
			
	return render_to_response('oauth_response.html', RequestContext(request,{'error': error_exists, 'error_message': error_message, 'username': username, 'org_name': org_name, 'org_choice':org_choice, 'org': org, 'email': email}))

# AJAX endpoint for page to constantly check if job is finished
def job_status(request, job_id):
	job = get_object_or_404(Job, pk = job_id)
	return HttpResponse(job.status + ':::' + job.error)

# Page for user to wait for job to run
def compare_orgs(request, job_id):

	job = get_object_or_404(Job, pk = job_id)

	if job.status == 'Not Started':

		job.status = 'Downloading Metadata'
		job.save()

		api_choice = request.GET.get('api')

		# Do logic for job
		for org in job.org_set.all():

			if api_choice == 'metadata':

				download_metadata_metadata.delay(job, org)

			else:

				download_metadata_tooling.delay(job, org)

	elif job.status == 'Finished':

		return HttpResponseRedirect('/compare_result/' + str(job.id))

	return render_to_response('loading.html', RequestContext(request, {'job': job}))	

# Page to display compare results
def compare_results(request, job_id):

	job = get_object_or_404(Job, pk = job_id)
	job_html = job.html
	return render_to_response('compare_results.html', RequestContext(request, {'job_html': job_html}))
