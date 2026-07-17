from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class CredencialBiometrica(models.Model):
    # Enlazamos la huella/rostro con el usuario específico
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credenciales_webauthn')
    
    # Para saber desde qué aparato se registró (Ej: "Laptop HP", "iPhone")
    nombre_dispositivo = models.CharField(max_length=255) 
    
    # Los datos criptográficos que nos entrega Windows Hello / TouchID
    credential_id = models.CharField(max_length=255, unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Llave de {self.usuario.username} ({self.nombre_dispositivo})"