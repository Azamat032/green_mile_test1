from django.urls import path
from main_app import views

app_name = 'main_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('reports/', views.reports, name='reports'),
    path('contact/', views.contact, name='contact'),
    path('certificate/', views.certificate, name='certificate'),
    path('history/', views.history, name='history'),
    path('faq/', views.faq, name='faq'),
    path('team/', views.team, name='team'),
    path('test/', views.test, name='test'),  # Fixed typo: 'teist' -> 'test'
    path('set-language/<str:lang>/', views.set_language, name='set_language'),
    path('api/create-certificate/', views.create_certificate,
         name='create_certificate'),
    path('api/payment-success/', views.payment_success, name='payment_success'),
    path('api/certificate-status/<str:certificate_id>/',
         views.certificate_status, name='certificate_status'),
    path('api/certificate/<str:certificate_id>/download/',
         views.download_certificate, name='download_certificate'),
    path('api/list-media-files/', views.list_media_files, name='list_media_files'),
]

# DO NOT ADD ANY static() or media configurations here!
