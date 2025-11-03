from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('test/', views.test_view, name='test'),
    path('start-scraping/', views.start_scraping, name='start_scraping'),
    path('start-scraping-all/', views.start_scraping_all, name='start_scraping_all'),
    path('progress/', views.get_progress, name='get_progress'),
    path('preview/<str:job_id>/', views.preview_products, name='preview_products'),
    path('download/<str:job_id>/', views.download_excel, name='download_excel'),
    path('job-status/<str:job_id>/', views.get_job_status, name='get_job_status'),
    path('list-jobs/', views.list_jobs, name='list_jobs'),
    path('site-stats/<str:job_id>/', views.get_site_statistics, name='get_site_statistics'),
    path('stop-scraping/<str:job_id>/', views.stop_scraping, name='stop_scraping'),
    path('supported-sites/', views.get_supported_sites, name='get_supported_sites'),
]