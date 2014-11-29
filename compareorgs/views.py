from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from compareorgs.forms import LoginForm
from django.conf import settings
import json	
import requests
from time import sleep

def index(request):

	login_form = LoginForm()

	return render_to_response('index.html', RequestContext(request,{'login_form': login_form}))
