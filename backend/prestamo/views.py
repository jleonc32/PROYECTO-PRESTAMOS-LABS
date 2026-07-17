from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from datetime import datetime

# ReportLab para PDFs
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Modelos y Formularios
from .models import Prestamo, Devolucion
from .forms import PrestamoForm, DevolucionForm

from django.http import JsonResponse


@login_required
def lista_prestamos(request):
    # --- CANDADO DE SEGURIDAD ---
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "Acceso denegado: Esta área es solo para el personal del laboratorio.")
        return redirect("dashboard")
    # ----------------------------

    # 1. Capturamos lo que el usuario escribe en el buscador y el filtro
    buscar = request.GET.get("buscar", "")
    estado = request.GET.get("estado", "")

    # 2. Traemos los préstamos ordenados por los más recientes
    prestamos = Prestamo.objects.select_related("usuario", "equipo").all().order_by('-fecha_prestamo')

    # 3. Aplicamos el buscador inteligente
    if buscar:
        prestamos = prestamos.filter(
            Q(usuario__username__icontains=buscar) |
            Q(usuario__first_name__icontains=buscar) |
            Q(usuario__last_name__icontains=buscar) |
            Q(equipo__nombre__icontains=buscar) |
            Q(equipo__codigo__icontains=buscar)
        )

    # 4. Aplicamos el filtro de estado (Activos / Devueltos)
    if estado:
        prestamos = prestamos.filter(estado=estado)

    context = {
        "prestamos": prestamos,
        "buscar": buscar,
        "estado": estado
    }

    return render(request, "prestamo/lista_prestamos.html", context)


@login_required
def procesar_devolucion(request, prestamo_id):
    # --- CANDADO DE SEGURIDAD ---
    if not request.user.groups.filter(name="Administrador").exists():
        return redirect("dashboard")
        
    if request.method == "POST":
        prestamo = get_object_or_404(Prestamo, id=prestamo_id)
        
        # Si el préstamo sigue activo, creamos la devolución
        if prestamo.estado == "Activo":
            # Al crear esto, el save() de Devolucion y Prestamo hacen todo el trabajo mágico
            Devolucion.objects.create(
                prestamo=prestamo, 
                observaciones="Equipo recibido desde el panel de control rápido."
            )
            messages.success(request, f"Equipo {prestamo.equipo.codigo} marcado como devuelto correctamente.")
            
    return redirect("lista_prestamos")


@login_required
def crear_prestamo(request):
    # Esta vista NO lleva candado porque los estudiantes sí deben poder entrar
    print(">>> CREAR PRESTAMO <<<")
    if request.method == "POST":
        print("=== Entró al POST ===")

        form = PrestamoForm(request.POST)

        if form.is_valid():
            print("=== Formulario válido ===")

            prestamo = form.save(commit=False)
            prestamo.usuario = request.user

            print("Equipo:", prestamo.equipo)
            print("Estado:", prestamo.equipo.estado)

            prestamo.save()
            print("=== Préstamo guardado ===")

            prestamo.equipo.estado = "Prestado"
            prestamo.equipo.save()

            # Si es estudiante, lo mandamos a "mis_prestamos", si es admin, a la lista general
            if request.user.groups.filter(name="Usuario").exists():
                return redirect("mis_prestamos")
            else:
                return redirect("lista_prestamos")
        else:
            print("=== Errores ===")
            print(form.errors)

    else:
        form = PrestamoForm()

    return render(request, "prestamo/crear_prestamo.html", {
        "form": form
    })

@login_required
def mis_prestamos(request):
    # Filtramos solo los equipos prestados por el usuario que inició sesión
    prestamos = Prestamo.objects.filter(usuario=request.user).order_by('-fecha_prestamo')
    
    return render(
        request, 
        'prestamo/mis_prestamos.html',
        {'prestamos': prestamos}
    )

@login_required
def crear_devolucion(request):
    # --- CANDADO DE SEGURIDAD ---
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "Acceso denegado: Solo el personal puede registrar devoluciones.")
        return redirect("dashboard")
    # ----------------------------

    if request.method == "POST":
        form = DevolucionForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("lista_prestamos")

    else:
        form = DevolucionForm()

    return render(request, "prestamo/crear_devolucion.html", {
        "form": form
    })

@login_required
def reporte_prestamos_pdf(request):
    # --- CANDADO DE SEGURIDAD ---
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")
    # ----------------------------

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_prestamos_UNEMI.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # --- COLORES INSTITUCIONALES ---
    azul_unemi = colors.HexColor("#002D62")

    # --- MEMBRETE OFICIAL ---
    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(azul_unemi)
    p.drawCentredString(width / 2, 750, "UNIVERSIDAD ESTATAL DE MILAGRO")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.darkgrey)
    p.drawCentredString(width / 2, 735, "Facultad de Ciencias e Ingenierías - Laboratorios")

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawCentredString(width / 2, 715, "REPORTE OFICIAL DE PRÉSTAMOS DE EQUIPOS")

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    p.setFont("Helvetica", 9)
    p.drawString(440, 695, f"Fecha Emisión: {fecha}")

    p.setStrokeColor(azul_unemi)
    p.setLineWidth(2)
    p.line(50, 685, 550, 685)

    # --- ENCABEZADO DE LA TABLA ---
    p.setFillColor(azul_unemi)
    p.rect(50, 660, 500, 20, fill=1, stroke=0)

    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.white)
    p.drawString(55, 666, "Usuario")
    p.drawString(150, 666, "Equipo")
    p.drawString(270, 666, "F. Préstamo")
    p.drawString(370, 666, "F. Devolución")
    p.drawString(480, 666, "Estado")

    # --- DATOS DE LA TABLA ---
    y = 640
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.black)

    prestamos = Prestamo.objects.select_related("usuario", "equipo")

    for pr in prestamos:
        fecha_prestamo_limpia = pr.fecha_prestamo.strftime('%Y-%m-%d %H:%M') if pr.fecha_prestamo else "---"
        fecha_devolucion_limpia = pr.fecha_devolucion.strftime('%Y-%m-%d %H:%M') if pr.fecha_devolucion else "---"

        p.drawString(55, y, str(pr.usuario.username).capitalize())
        p.drawString(150, y, str(pr.equipo.nombre).capitalize())
        p.drawString(270, y, fecha_prestamo_limpia)
        p.drawString(370, y, fecha_devolucion_limpia)
        
        estado = str(pr.estado)
        if estado == "Activo":
            p.setFillColor(colors.HexColor("#198754")) 
        elif estado == "Devuelto":
            p.setFillColor(colors.HexColor("#0d6efd"))
        else:
            p.setFillColor(colors.darkgrey)
            
        p.drawString(480, y, estado)
        p.setFillColor(colors.black)

        p.setStrokeColor(colors.lightgrey)
        p.setLineWidth(0.5)
        p.line(50, y - 5, 550, y - 5)

        y -= 20

        if y < 50:
            p.showPage()
            y = 750
            p.setFont("Helvetica", 9)
            p.setFillColor(colors.black)

    p.save()
    return response


@login_required
def dashboard(request):
    # Corregí el nombre de 'Admin' a 'Administrador' para que todo encaje perfecto
    is_admin = request.user.groups.filter(name="Administrador").exists()
    is_usuario = request.user.groups.filter(name="Usuario").exists()

    return render(request, "dashboard.html", {
        "is_admin": is_admin,
        "is_usuario": is_usuario,
    })
    
from django.http import JsonResponse

@login_required
def api_mis_prestamos(request):
    """
    Devuelve los estados de los préstamos del usuario actual en formato JSON.
    """
    # Buscamos los préstamos del usuario y sacamos solo el ID y el Estado
    prestamos = Prestamo.objects.filter(usuario=request.user).values('id', 'estado')
    
    # Convertimos a lista y lo enviamos como JSON
    return JsonResponse(list(prestamos), safe=False)

from django.http import JsonResponse
# Asegúrate de que el modelo Prestamo ya esté importado arriba

from django.http import JsonResponse
from .models import Prestamo # Asegúrate de que el modelo esté importado

def api_notificaciones(request):
    # Si no hay usuario logueado, devolvemos 0
    if not request.user.is_authenticated:
        return JsonResponse({'cantidad': 0, 'alertas': []})

    # Verificamos si es administrador
    if request.user.groups.filter(name="Administrador").exists() or request.user.is_superuser:
        alertas_db = Prestamo.objects.filter(estado="Activo").order_by('-id')[:5]
        es_admin = True
    else:
        # Si es usuario normal
        alertas_db = Prestamo.objects.filter(usuario=request.user, estado="Activo").order_by('fecha_devolucion')
        es_admin = False

    # Armamos una lista con los datos listos para Javascript
    datos_alertas = []
    for alerta in alertas_db:
        # Formateamos la fecha para que se vea bonita (ej: 16/07/2026 02:30 PM)
        fecha_str = alerta.fecha_devolucion.strftime("%d/%m/%Y %I:%M %p") if alerta.fecha_devolucion else "Sin fecha límite"
        
        datos_alertas.append({
            'usuario': alerta.usuario.username,
            'equipo': alerta.equipo.nombre,
            'fecha': fecha_str
        })

    return JsonResponse({
        'cantidad': alertas_db.count(),
        'alertas': datos_alertas,
        'es_admin': es_admin
    })