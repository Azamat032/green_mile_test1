from django.urls import path
from main_app import views

app_name = 'main_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('volunteers/', views.volunteers, name='volunteers'),
    path('organizations/', views.organizations, name='organizations'),
    path('reports/', views.reports, name='reports'),
    path('history/', views.history, name='history'),
    path('faq/', views.faq, name='faq'),
    path('team/', views.team, name='team'),

    path('profile/', views.profile, name='profile'),
    path('set-language/<str:lang>/', views.set_language, name='set_language'),

    # Keep only one register URL - use the page for GET, API for POST
    path('register/', views.register_page,
         name='register'),  # For page display
    path('api/register/', views.register,
         name='register_api'),    # For API calls

    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('certificate/', views.certificate, name='certificate'),
    path('api/create-certificate/', views.create_certificate,
         name='create_certificate'),
    path('api/payment-success/', views.payment_success, name='payment_success'),
    path('api/certificate-status/<str:certificate_id>/',
         views.certificate_status, name='certificate_status'),
    path('certificate/success/<str:certificate_id>/',
         views.certificate_success, name='certificate_success'),
    path('api/certificate/<str:certificate_id>/download/',
         views.download_certificate, name='download_certificate'),
    path('api/list-media-files/', views.list_media_files, name='list_media_files'),
    path('api/volunteer-submit/', views.volunteer_submit, name='volunteer_submit'),
    path('api/organizer-submit/', views.organizer_submit, name='organizer_submit'),
    path('api/certificate/<str:certificate_id>/generate/',
         views.generate_certificate_pdf, name='generate_certificate_pdf'),

    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/change-email/', views.change_email, name='change_email'),
    path('profile/confidential-data/',
         views.get_user_confidential_data, name='confidential_data'),


    path('api/register/', views.register_api, name='register_api'),
    path('api/login/', views.login_api, name='login_api'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/change-email/', views.change_email, name='change_email'),
    path('profile/confidential-data/',
         views.get_user_confidential_data, name='confidential_data'),
]
