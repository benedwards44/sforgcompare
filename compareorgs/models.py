from django.db import models

class Job(models.Model):
	random_id = models.CharField(db_index=True,max_length=255, blank=True)
	created_date = models.DateTimeField(null=True,blank=True)
	finished_date = models.DateTimeField(null=True,blank=True)
	password = models.CharField(max_length=255, blank=True)
	api_choice = models.CharField(max_length=255,null=True,blank=True)
	email_result = models.BooleanField()
	email = models.CharField(max_length=255,blank=True)
	contextual_diff = models.BooleanField(default=False)
	status = models.CharField(max_length=255, blank=True)
	error = models.TextField(blank=True)
	error_stacktrace = models.TextField(blank=True)
	zip_file = models.FileField(upload_to='/', blank=True, null=True)
	zip_file_error = models.TextField(blank=True, null=True)

	def sorted_orgs(self):
		return self.org_set.order_by('org_number')

	def sorted_component_list(self):
		return self.componentlistunique_set.order_by('order')

class Org(models.Model):
	job = models.ForeignKey(Job, blank=True, null=True)
	org_number = models.PositiveSmallIntegerField()
	access_token = models.CharField(max_length=255)
	instance_url = models.CharField(max_length=255)
	org_id = models.CharField(max_length=255)
	org_name = models.CharField(max_length=255, blank=True)
	username = models.CharField(max_length=255, blank=True)
	status = models.CharField(max_length=255, blank=True)
	error = models.TextField(blank=True)
	error_stacktrace = models.TextField(blank=True)

	def sorted_component_types(self):
		return self.componenttype_set.order_by('name')

class ComponentType(models.Model):
	org = models.ForeignKey(Org)
	name = models.CharField(max_length=255)

	def __str__(self):
		return '%s' % (self.name)

	def sorted_components(self):
		return self.component_set.order_by('name')

	def org_name(self):
		return self.org.org_name

class Component(models.Model):
	component_type = models.ForeignKey(ComponentType)
	name = models.CharField(max_length=255)
	content = models.TextField(blank=True, null=True)

	def __str__(self):
		return '%s' % (self.name)

class ComponentListUnique(models.Model):
	job = models.ForeignKey(Job)
	diff_html = models.TextField(blank=True, null=True)
	row_html = models.TextField(blank=True, null=True)
	order = models.PositiveSmallIntegerField()


class OfflineFileJob(models.Model):
	job = models.ForeignKey(Job)
	status = models.CharField(max_length=255)
	error = models.TextField(blank=True, null=True)
	error_stacktrace = models.TextField(blank=True)

	