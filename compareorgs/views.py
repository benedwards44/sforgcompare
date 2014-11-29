from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import json	
import requests
from time import sleep

def index(request):

	client_id = settings.SALESFORCE_CONSUMER_KEY
	redirect_uri = settings.SALESFORCE_REDIRECT_URI

	return render_to_response('index.html', RequestContext(request,{'client_id': client_id, 'redirect_uri': redirect_uri}))
