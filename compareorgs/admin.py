from django.contrib import admin
from compareorgs.models import Job, Org, Component, ComponentType, ComponentListUnique, OfflineFileJob

class OrgInline(admin.TabularInline):
	fields = ['org_number','org_name', 'username', 'instance_url', 'access_token', 'status', 'error', 'error_stacktrace']
	ordering = ['org_number']
	model = Org
	extra = 0

class ComponentInline(admin.TabularInline):
	fields = ['name', 'content']
	ordering = ['name']
	model = Component
	extra = 0

class ComponentListUniqueInline(admin.TabularInline):
	fields = ['order','row_html','diff_html']
	ordering = ['order']
	model = ComponentListUnique
	extra = 0

class OfflineFileJobInline(admin.TabularInline):
	fields = ['status', 'error']
	model = OfflineFileJob
	extra = 0

class ComponentTypeAdmin(admin.ModelAdmin):
	list_display = ['org_name','name']
	ordering = ['org', 'name']
	inlines = [ComponentInline]

class JobAdmin(admin.ModelAdmin):
    list_display = ('created_date','finished_date','email','status','error')
    ordering = ['-created_date']
    inlines = [OrgInline, OfflineFileJobInline]


class OrgAdmin(admin.ModelAdmin):
    list_display = ('job','org_name','username','status')
    ordering = ['job']


admin.site.register(Job, JobAdmin)
admin.site.register(Org, OrgAdmin)
admin.site.register(ComponentType, ComponentTypeAdmin)