from django.urls import path
from . import views

urlpatterns = [

    # Lista de usuarios
    path('',views.lista_usuarios,name='lista_usuarios'),
    # Crear usuario
    path('crear/',views.crear_usuario,name='crear_usuario'),
    # Registro público
    path('registro/',views.registro,name='registro'),
    # Asignar rol
    path('asignar/<int:id>/',views.asignar_rol,name='asignar_rol'),
    path('api/biometria/generar-reto/', views.generar_reto_biometrico, name='api_generar_reto'),
    path('api/biometria/verificar-registro/', views.verificar_registro_biometrico, name='api_verificar_registro'),
    # Añade esta línea a tu lista de urlpatterns
    path('mi-perfil/vincular-huella/', views.vincular_huella, name='vincular_huella'),
    # Añade estas líneas a tu urlpatterns en urls.py
    path('login-biometrico/', views.login_biometrico, name='login_biometrico'), # EL LINK PARA ENTRAR
    path('api/biometria/login/generar-reto/', views.generar_reto_login, name='generar_reto_login'),
    path('api/biometria/login/verificar/', views.verificar_login_biometrico, name='verificar_login_biometrico'),
]

