from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


def login_view(request):

    if request.user.is_authenticated:
        if request.user.groups.filter(name="Administrador").exists():
            return redirect("dashboard_admin")

        if request.user.groups.filter(name="Usuario").exists():
            return redirect("dashboard_user")

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, "login.html", {
                "error": "Usuario o contraseña incorrectos."
            })

        login(request, user)

        if user.groups.filter(name="Administrador").exists():
            return redirect("dashboard_admin")

        if user.groups.filter(name="Usuario").exists():
            return redirect("dashboard_user")

        logout(request)

        return render(request, "login.html", {
            "error": "El usuario no pertenece a ningún grupo."
        })

    return render(request, "login.html")


@login_required
def dashboard_admin(request):
    print(request.user.groups.all())
    return render(request, "dashboard_admin.html", {
        "rol": "Administrador"
    })


@login_required
def dashboard_user(request):
    print(request.user.groups.all())
    return render(request, "dashboard_user.html", {
        "rol": "Usuario"
    })

def logout_view(request):
    logout(request)
    return redirect("login")