from django import forms
from django.forms import ModelForm

class LoginForm(forms.Form):
	environment = forms.CharField(required=False);
	api_version = forms.IntegerField(required=False)
	access_token = forms.CharField(required=False)
	instance_url = forms.CharField(required=False)
	org_id = forms.CharField(required=False)