from django.urls import path
from django.contrib import admin
from compareorgs import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('oauth_response/', views.oauth_response, name='oauth_response'),
    path('job_status/<str:job_id>/', views.job_status),
    path('compare_orgs/<str:job_id>/', views.compare_orgs),
    path('compare_result/<str:job_id>/', views.compare_results),
    path('compare_result/<str:job_id>/build_file/', views.build_file),
    path('re-run-job/<str:job_id>/', views.rerunjob),
    path('check_file_status/<str:job_id>/', views.check_file_status),
    path('get_metadata/<int:component_id>/', views.get_metadata),
    path('get_diffhtml/<int:component_id>/', views.get_diffhtml),
]
