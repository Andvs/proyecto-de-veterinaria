from django.shortcuts import render, redirect
from app.forms import RegistroForm, VeterinarioForm, ClienteForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import Perfil
from django.contrib import messages
from django.contrib.auth.models import User

# Create your views here.

SESSION_KEY = "registro_parcial"

def _borrar_datos_sesion(request):
    """Limpia los datos guardados temporalmente"""
    if SESSION_KEY in request.session:
        del request.session[SESSION_KEY]
        request.session.modified = True
        

def registrar_paso1(request):
    """Paso 1: valida datos, pero NO guarda en la base de datos."""
    if request.method == "POST":
        if "cancel" in request.POST:
            _borrar_datos_sesion(request)
            messages.info(request, "Registro cancelado.")
            return redirect("dashboard")

        form = RegistroForm(request.POST)
        if form.is_valid():
            # Guardamos los datos en sesión (no en BD)
            data = form.cleaned_data
            request.session[SESSION_KEY] = {
                "username": data["username"],
                "email": data["email"],
                "password1": data["password1"],
                "tipo": data["tipo"],
                "rut": data["rut"],
                "telefono": data["telefono"],
            }
            request.session.modified = True

            if data["tipo"] == "VETERINARIO":
                return redirect("registrar_paso2_vet")
            elif data["tipo"] == "CLIENTE":
                return redirect("registrar_paso2_cli")
            else:
                return redirect("registrar_finalizar_sin_detalle")
    else:
        form = RegistroForm()

    return render(request, "usuario/registro.html", {"form": form})


def registrar_paso2_vet(request):
    """Paso 2: completar datos de veterinario. Se guarda todo solo si se completa correctamente."""
    datos = request.session.get(SESSION_KEY)
    if not datos or datos.get("tipo") != "VETERINARIO":
        messages.error(request, "Debes iniciar el registro desde el primer paso.")
        return redirect("registrar_paso1")

    if request.method == "POST":
        if "cancel" in request.POST:
            _borrar_datos_sesion(request)
            messages.info(request, "Registro cancelado.")
            return redirect("dashboard")

        form = VeterinarioForm(request.POST)
        if form.is_valid():
            try:
                # 1️⃣ Crear usuario
                user = User.objects.create_user(
                    username=datos["username"],
                    email=datos["email"],
                    password=datos["password1"]
                )
                # 2️⃣ Crear perfil
                perfil = Perfil.objects.create(
                    user=user,
                    tipo="VETERINARIO",
                    rut=datos["rut"],
                    telefono=datos["telefono"]
                )
                # 3️⃣ Crear veterinario
                veterinario = form.save(commit=False)
                veterinario.perfil = perfil
                veterinario.save()

                _borrar_datos_sesion(request)
                login(request, user)
                messages.success(request, "¡Registro completado con éxito!")
                return redirect("dashboard")

            except Exception as e:
                messages.error(request, f"Ocurrió un error al registrar: {e}")
    else:
        form = VeterinarioForm()

    return render(request, "usuario/completar_veterinario.html", {"form": form})


def registrar_paso2_cli(request):
    """Paso 2: completar datos de cliente."""
    datos = request.session.get(SESSION_KEY)
    if not datos or datos.get("tipo") != "CLIENTE":
        messages.error(request, "Debes iniciar el registro desde el primer paso.")
        return redirect("registrar_paso1")

    if request.method == "POST":
        if "cancel" in request.POST:
            _borrar_datos_sesion(request)
            messages.info(request, "Registro cancelado.")
            return redirect("dashboard")

        form = ClienteForm(request.POST)
        if form.is_valid():
            try:
                # 1️⃣ Crear usuario
                user = User.objects.create_user(
                    username=datos["username"],
                    email=datos["email"],
                    password=datos["password1"]
                )
                # 2️⃣ Crear perfil
                perfil = Perfil.objects.create(
                    user=user,
                    tipo="CLIENTE",
                    rut=datos["rut"],
                    telefono=datos["telefono"]
                )
                # 3️⃣ Crear cliente
                cliente = form.save(commit=False)
                cliente.perfil = perfil
                cliente.save()

                _borrar_datos_sesion(request)
                login(request, user)
                messages.success(request, "¡Registro completado con éxito!")
                return redirect("dashboard")

            except Exception as e:
                messages.error(request, f"Ocurrió un error al registrar: {e}")
    else:
        form = ClienteForm()

    return render(request, "usuario/completar_cliente.html", {"form": form})


def registrar_finalizar_sin_detalle(request):
    """Para tipos sin paso 2 (admin o recepcionista)."""
    datos = request.session.get(SESSION_KEY)
    if not datos:
        messages.error(request, "Debes iniciar el registro desde el primer paso.")
        return redirect("registrar_paso1")

    try:
        user = User.objects.create_user(
            username=datos["username"],
            email=datos["email"],
            password=datos["password1"]
        )
        Perfil.objects.create(
            user=user,
            tipo=datos["tipo"],
            rut=datos["rut"],
            telefono=datos["telefono"]
        )
        _borrar_datos_sesion(request)
        login(request, user)
        messages.success(request, "¡Registro completado!")
        return redirect("dashboard")

    except Exception as e:
        messages.error(request, f"Ocurrió un error: {e}")
        return redirect("registrar_paso1")


def iniciarSesion(request):
    if request.method == "GET":
        return render(request, "usuario/login.html")
        
    elif request.method == "POST":
        uname = request.POST.get("username")
        passw = request.POST.get("password")
        
        user = authenticate(request, username=uname, password=passw)
        
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "usuario/login.html", {"error": "Credenciales incorrectas"})

def dashboard(request):
    return render(request, "usuario/dashboard.html")
