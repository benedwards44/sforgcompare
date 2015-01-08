from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView, RedirectView
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'compareorgs.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth_response/$', 'compareorgs.views.oauth_response', name='oauth_response'),
    url(r'^job_status/(?P<job_id>\d+)/$', 'compareorgs.views.job_status'),
    url(r'^compare_orgs/(?P<job_id>\d+)/$', 'compareorgs.views.compare_orgs'),
    url(r'^compare_result/(?P<job_id>\d+)/$', 'compareorgs.views.compare_results'),
    url(r'^get_metadata/(?P<component_id>\d+)/$', 'compareorgs.views.get_metadata'),
    url(r'^get_diffhtml/(?P<component_id>\d+)/$', 'compareorgs.views.get_diffhtml'),
)
