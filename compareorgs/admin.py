from django.contrib import admin
from compareorgs.models import Job, Org, Component, ComponentType

class OrgInline(admin.TabularInline):
	fields = ['org_number','org_name', 'username', 'access_token', 'status', 'error']
	ordering = ['org_number']
	model = Org
	extra = 0

class ComponentInline(admin.TabularInline):
	fields = ['name', 'content']
	ordering = ['name']
	model = Component
	extra = 0

class ComponentTypeAdmin(admin.ModelAdmin):
	list_display = ['org_name','name']
	ordering = ['org', 'name']
	inlines = [ComponentInline]

class JobAdmin(admin.ModelAdmin):
    list_display = ('created_date','finished_date','status','error')
    ordering = ['-created_date']
    inlines = [OrgInline]

admin.site.register(Job, JobAdmin)
admin.site.register(ComponentType, ComponentTypeAdmin)