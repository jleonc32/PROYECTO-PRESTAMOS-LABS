from django.utils import timezone
from prestamo.models import Prestamo

def notificaciones_campanita(request):
    if not request.user.is_authenticated:
        return {}

    # Si es Administrador
    if request.user.groups.filter(name="Administrador").exists() or request.user.is_superuser:
        # Busca los últimos 5 préstamos activos para avisarle al admin
        alertas = Prestamo.objects.filter(estado="Activo").order_by('-id')[:5]
        return {
            'alertas_notificaciones': alertas,
            'contador_notificaciones': alertas.count(),
            'es_admin_noti': True
        }
    
    # Si es un Estudiante/Usuario Normal
    else:
        # Busca los préstamos activos de este usuario específico
        alertas = Prestamo.objects.filter(usuario=request.user, estado="Activo").order_by('fecha_devolucion')
        return {
            'alertas_notificaciones': alertas,
            'contador_notificaciones': alertas.count(),
            'es_admin_noti': False
        }