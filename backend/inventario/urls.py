from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path("equipos/", views.lista_equipos, name="lista_equipos"),
    path("equipos/nuevo/", views.crear_equipo, name="crear_equipo"),
    path("equipos/<int:pk>/editar/", views.editar_equipo, name="editar_equipo"),
    path("equipos/<int:pk>/eliminar/", views.eliminar_equipo, name="eliminar_equipo"),
    path("reporte/equipos/pdf/", views.reporte_equipos_pdf, name="reporte_equipos_pdf"),
    path("prueba/", views.dashboard),
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),
    path('categorias/editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('api/estadisticas/', views.api_estadisticas_dashboard, name='api_estadisticas'),
]