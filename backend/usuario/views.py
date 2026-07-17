import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from decouple import config

from .forms import UsuarioForm
from .models import CredencialBiometrica

# --- IMPORTACIONES COMPLETAS DE WEBAUTHN ---
from webauthn import (
    generate_registration_options, 
    verify_registration_response, 
    options_to_json,
    generate_authentication_options, 
    verify_authentication_response
)
from webauthn.helpers.parse_registration_credential_json import parse_registration_credential_json
from webauthn.helpers.parse_authentication_credential_json import parse_authentication_credential_json
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, PublicKeyCredentialType


RP_ID = config('DOMINIO_WEBAUTHN', default='localhost')
EXPECTED_ORIGIN = config('ORIGEN_WEBAUTHN', default='http://localhost:8000')

# ==========================================
# 1. VISTAS ESTÁNDAR DE USUARIOS
# ==========================================

@login_required
def lista_usuarios(request):
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos para acceder.")
        return redirect("dashboard_user")
    usuarios = User.objects.all()
    return render(request, "usuario/lista_usuarios.html", {"usuarios": usuarios})

@login_required
def crear_usuario(request):
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos para acceder.")
        return redirect("dashboard_user")
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("lista_usuarios")
    else:
        form = UsuarioForm()
    return render(request, "usuario/crear_usuario.html", {"form": form})

def registro(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = True
            usuario.save()
            grupo_usuario, created = Group.objects.get_or_create(name='Usuario')
            usuario.groups.add(grupo_usuario)
            login(request, usuario)
            messages.success(request, f"¡Bienvenido {usuario.username}! Tu cuenta está lista.")
            return redirect("dashboard") 
    else:
        form = UsuarioForm()
    return render(request, "usuario/registro.html", {"form": form})

@login_required
def asignar_rol(request, id):
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect("dashboard_user")
    usuario = get_object_or_404(User, id=id)
    if request.method == "POST":
        rol = request.POST.get("rol")
        usuario.groups.clear()
        grupo = Group.objects.get(name=rol)
        usuario.groups.add(grupo)
        messages.success(request, "Rol asignado correctamente.")
        return redirect("lista_usuarios")
    return render(request, "usuario/asignar_rol.html", {"usuario": usuario})


# ==========================================
# 2. VISTAS DE VINCULACIÓN (REGISTRO BIOMÉTRICO)
# ==========================================

@login_required
def vincular_huella(request):
    return render(request, 'usuario/vincular_huella.html')

@login_required
def generar_reto_biometrico(request):
    rp_id_dinamico = request.get_host().split(':')[0] 
    opciones = generate_registration_options(
        rp_id=rp_id_dinamico,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_id=str(request.user.id).encode(),
        user_name=request.user.username,
    )
    request.session['webauthn_challenge'] = opciones.challenge.hex()
    request.session.modified = True
    return JsonResponse(json.loads(options_to_json(opciones)))

@csrf_exempt
@login_required
def verificar_registro_biometrico(request):
    if request.method == 'POST':
        try:
            datos_json = json.loads(request.body)
            reto_guardado = request.session.get('webauthn_challenge')
            
            credencial = parse_registration_credential_json(datos_json)
            
            verificacion = verify_registration_response(
                credential=credencial,
                expected_challenge=bytes.fromhex(reto_guardado),
                expected_origin=f"{request.scheme}://{request.get_host()}",
                expected_rp_id=request.get_host().split(':')[0],
            )
            
            CredencialBiometrica.objects.create(
                usuario=request.user,
                nombre_dispositivo="Dispositivo Vinculado", 
                credential_id=verificacion.credential_id.hex(),
                public_key=verificacion.credential_public_key.hex(),
                sign_count=verificacion.sign_count
            )
            return JsonResponse({'status': 'ok', 'mensaje': '¡Huella/Rostro registrado con éxito!'})
        except Exception as e:
            print(f"Error Registro WebAuthn: {e}")
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)


# ==========================================
# 3. VISTAS DE LOGIN BIOMÉTRICO
# ==========================================

def login_biometrico(request):
    return render(request, 'usuario/login_biometrico.html')

@csrf_exempt
def generar_reto_login(request):
    try:
        # Nota: Por ahora usamos la última credencial para pruebas rápidas. 
        # En producción, pedirías el username primero y buscarías su credencial específica.
        ultima_credencial = CredencialBiometrica.objects.last() 
        if not ultima_credencial:
            return JsonResponse({'error': 'No hay biometría registrada en el sistema'}, status=400)
            
        domain = "localhost"
        
        opciones = generate_authentication_options(
            rp_id=request.get_host().split(':')[0],
            allow_credentials=[
                PublicKeyCredentialDescriptor(
                    id=bytes.fromhex(ultima_credencial.credential_id),
                    type=PublicKeyCredentialType.PUBLIC_KEY, # Solución del Enum aplicada aquí
                )
            ],
        )
        request.session['webauthn_login_challenge'] = opciones.challenge.hex()
        request.session['webauthn_login_userid'] = ultima_credencial.usuario.id
        return JsonResponse(json.loads(options_to_json(opciones)))
    except Exception as e:
        print(f"Error Generar Reto Login: {e}")
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def verificar_login_biometrico(request):
    if request.method == 'POST':
        try:
            datos_json = json.loads(request.body)
            reto_guardado = request.session.get('webauthn_login_challenge')
            usuario_id = request.session.get('webauthn_login_userid')
            
            credencial_login = parse_authentication_credential_json(datos_json)
            
            # --- AQUÍ ESTABA EL ERROR: Cambiamos .id por .raw_id ---
            credencial_db = CredencialBiometrica.objects.get(
                credential_id=credencial_login.raw_id.hex()
            )
            # -------------------------------------------------------
            
            verificacion = verify_authentication_response(
                credential=credencial_login,
                expected_challenge=bytes.fromhex(reto_guardado),
                expected_rp_id="localhost",
                expected_origin=f"{request.scheme}://{request.get_host()}",
                credential_public_key=bytes.fromhex(credencial_db.public_key),
                credential_current_sign_count=credencial_db.sign_count,
            )
            
            # Actualizamos el contador de firmas (medida de seguridad anti-clonación)
            credencial_db.sign_count = verificacion.new_sign_count
            credencial_db.save()
            
            # Iniciamos la sesión del usuario en Django
            usuario = User.objects.get(id=usuario_id)
            login(request, usuario)
            
            return JsonResponse({'status': 'ok', 'mensaje': '¡Bienvenido! Sesión iniciada correctamente.'})
        except Exception as e:
            print(f"Error Verificar Login: {e}")
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)