from django.contrib import admin
from compareorgs.models import Job, Org, Component, ComponentType

class OrgInline(admin.TabularInline):
	fields = ['org_number','org_name', 'username', 'access_token', 'status', 'error']
	ordering = ['org_number']
	model = Org
	extra = 0

class ComponentTypeInline(admin.TabularInline):
	fields = ['name', 'content']
	ordering = ['name']
	model = ComponentType
	extra = 0

class ComponentAdmin(admin.ModelAdmin):
	fields = ['org','name']
	inlines = [ComponentTypeInline]

class JobAdmin(admin.ModelAdmin):
    list_display = ('created_date','status','error')
    inlines = [OrgInline]

admin.site.register(Job, JobAdmin)
admin.site.register(Component, ComponentAdmin)