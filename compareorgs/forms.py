from django import forms

class JobForm(forms.Form):
	org_one = forms.IntegerField(required=False)
	org_two = forms.IntegerField(required=False)
	api_choice = forms.CharField()