from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView, RedirectView
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'compareorgs.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
)
