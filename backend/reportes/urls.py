from django.urls import path
from . import views

urlpatterns = [
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]