from django.urls import path
from .views import home
from . import views
urlpatterns = [
    path('',home, name="home"),
    path('registraion/',views.registration_detail,name="registration_detail"),
    path("api/register/", views.registration_store, name="register_api"),
    path('login/verify',views.login_verify,name="login_verify"),
    path('book/appointment/', views.book_appointment, name="book_appointment"),
    path('appointment/success',views.appointment_store,name="appointment_store"),
    path('adminpage/dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path("adminpage/update_status/<int:appointment_id>/<str:status>/", views.update_status, name="update_status"),
    path("adminpage/home/",views.admin_home,name="admin_home"),
    path("adminpage/logout/", views.adminpage_logout, name="adminpage_logout"),
    path('doctor/add/page/',views.doctor_add_page,name="doctor_add_page"),
    path("delete/doctor/<doctor_id>/",views.delete_doctor,name="delete_doctor"),
    path('adminpage/manage/doctors/',views.add_doctor,name="add_doctor"),
    path('patient/add/page/',views.patient_add_page,name="patient_add_page"),
    path('delete/patient/<patient_id>/',views.delete_patient,name="delete_patient"),
    path('add/patient/',views.add_patient,name="add_patient"),
    path('patient/homepage',views.patient_home,name="patient_home"),
    path('patinet/status/cheack/',views.patient_status,name="patient_status"),
    path("doctor/home/",views.doctor_home,name="doctor_home"),
    path("doctorpage/update_status_doctor/<int:appointment_id>/<str:status>/", views.update_status_doctor, name="update_status_doctor"),
    path('doctor/logout/',views.doctor_logout,name="doctor_logout"),

]
