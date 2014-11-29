from django.contrib import admin
from compareorgs.models import Job

class JobAdmin(admin.ModelAdmin):
    list_display = ('created_date','status','error')

admin.site.register(Job, JobAdmin)