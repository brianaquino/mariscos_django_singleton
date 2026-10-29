from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('acopio/', views.dashboard_acopio, name='dashboard_acopio'),
    path('restaurante/', views.dashboard_restaurante, name='dashboard_restaurante'),
    path('logout/', views.logout_view, name='logout'), 
    path('generar-pdf/', views.generar_reporte_pdf, name='generar_pdf'),
    path('diagnostico/', views.estado_bd, name='estado_bd'),
    path('registro/', views.registro_view, name='registro'),
]