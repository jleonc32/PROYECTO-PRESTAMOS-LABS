from django.urls import path
from . import views

urlpatterns = [

    # Lista de usuarios
    path(
        '',
        views.lista_usuarios,
        name='lista_usuarios'
    ),

    # Crear usuario
    path(
        'crear/',
        views.crear_usuario,
        name='crear_usuario'
    ),

    # Registro público
    path(
        'registro/',
        views.registro,
        name='registro'
    ),

    # Asignar rol
    path(
        'asignar/<int:id>/',
        views.asignar_rol,
        name='asignar_rol'
    ),

]