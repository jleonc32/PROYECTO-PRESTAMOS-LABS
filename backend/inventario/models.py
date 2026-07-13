from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Equipo(models.Model):

    ESTADOS = [
        ('Disponible', 'Disponible'),
        ('Prestado', 'Prestado'),
        ('Mantenimiento', 'Mantenimiento'),
    ]

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="equipos"
    )

    codigo = models.CharField(max_length=50, unique=True)

    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)

    ubicacion = models.CharField(max_length=100, blank=True, default="")

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Disponible'
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def save(self, *args, **kwargs):
        # 1. Guardamos los cambios del equipo en la base de datos
        super().save(*args, **kwargs)
        
        # 2. Si el estado del equipo cambió a 'Disponible', cerramos sus préstamos activos
        if self.estado == 'Disponible':
            # Se importa aquí adentro para evitar problemas de "importación circular"
            from prestamo.models import Prestamo 
            
            # Busca los préstamos de este equipo que sigan "Activos" y los cambia a "Devuelto"
            Prestamo.objects.filter(equipo=self, estado='Activo').update(estado='Devuelto')