from django.contrib import admin
from compareorgs.models import Job, Org

class OrgInline(admin.TabularInline):
	fields = ['org_number','org_name', 'username', 'status', 'error']
	ordering = ['org_number']
	model = Org
	extra = 0

class JobAdmin(admin.ModelAdmin):
    list_display = ('created_date','status','error')
    inlines = [OrgInline]

admin.site.register(Job, JobAdmin)