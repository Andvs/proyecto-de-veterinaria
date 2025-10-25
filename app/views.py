from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q

from app.forms import RegistroForm, VeterinarioForm, ClienteForm, MascotaForm, RecepcionistaForm
from .models import Perfil, Mascota, Cliente, Recepcionista, Veterinario


# ============================================================
#             REGISTRO DE USUARIOS
# ============================================================

SESSION_KEY = "registro_parcial"

def _borrar_datos_sesion(request):
    if SESSION_KEY in request.session:
        del request.session[SESSION_KEY]
        request.session.modified = True

def registrar_paso1(request):
    if request.method == "POST":
        if "cancel" in request.POST:
            _borrar_datos_sesion(request)
            messages.info(request, "Registro cancelado.")
            return redirect("dashboard")

        form = RegistroForm(request.POST)
        if form.is_valid():
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
            elif data["tipo"] == "RECEPCIONISTA":
                return redirect("registrar_paso2_recep")
            else:
                return redirect("registrar_finalizar_sin_detalle")
    else:
        form = RegistroForm()

    return render(request, "usuario/registro.html", {"form": form})


def registrar_paso2_cli(request):
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
                user = User.objects.create_user(
                    username=datos["username"],
                    email=datos["email"],
                    password=datos["password1"]
                )
                perfil = Perfil.objects.create(
                    user=user,
                    tipo="CLIENTE",
                    rut=datos["rut"],
                    telefono=datos["telefono"]
                )
                cliente = form.save(commit=False)
                cliente.perfil = perfil
                cliente.save()

                _borrar_datos_sesion(request)
                messages.success(request, f"Usuario '{user.username}' registrado correctamente.")
                return redirect("dashboard")

            except Exception as e:
                messages.error(request, f"Ocurrió un error al registrar: {e}")
    else:
        form = ClienteForm()

    return render(request, "usuario/completar_cliente.html", {"form": form})


def registrar_paso2_recep(request):
    datos = request.session.get(SESSION_KEY)
    if not datos or datos.get("tipo") != "RECEPCIONISTA":
        messages.error(request, "Debes iniciar el registro desde el primer paso.")
        return redirect("registrar_paso1")

    if request.method == "POST":
        if "cancel" in request.POST:
            _borrar_datos_sesion(request)
            messages.info(request, "Registro cancelado.")
            return redirect("dashboard")

        form = RecepcionistaForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=datos["username"],
                    email=datos["email"],
                    password=datos["password1"],
                )
                perfil = Perfil.objects.create(
                    user=user,
                    tipo="RECEPCIONISTA",
                    rut=datos["rut"],
                    telefono=datos["telefono"],
                )
                recep = form.save(commit=False)
                recep.perfil = perfil
                recep.save()

                _borrar_datos_sesion(request)
                messages.success(request, f"Usuario '{user.username}' registrado correctamente.")
                return redirect("dashboard")
            except Exception as e:
                messages.error(request, f"Ocurrió un error al registrar: {e}")
    else:
        form = RecepcionistaForm()

    return render(request, "usuario/completar_recepcionista.html", {"form": form})


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
                user = User.objects.create_user(
                    username=datos["username"],
                    email=datos["email"],
                    password=datos["password1"]
                )
                perfil = Perfil.objects.create(
                    user=user,
                    tipo="VETERINARIO",
                    rut=datos["rut"],
                    telefono=datos["telefono"]
                )
                veterinario = form.save(commit=False)
                veterinario.perfil = perfil
                veterinario.save()

                _borrar_datos_sesion(request)
                messages.success(request, f"Usuario '{user.username}' registrado correctamente.")
                return redirect("dashboard")

            except Exception as e:
                messages.error(request, f"Ocurrió un error al registrar: {e}")
    else:
        form = VeterinarioForm()

    return render(request, "usuario/completar_veterinario.html", {"form": form})


def registrar_finalizar_sin_detalle(request):
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
        messages.success(request, f"Usuario '{user.username}' registrado correctamente.")
        return redirect("dashboard")

    except Exception as e:
        messages.error(request, f"Ocurrió un error: {e}")
        return redirect("registrar_paso1")


# ============================================================
#             LOGIN / LOGOUT / DASHBOARD
# ============================================================

def iniciarSesion(request):
    if request.method == "POST":
        uname = request.POST.get("username")
        passw = request.POST.get("password")
        user = authenticate(request, username=uname, password=passw)
        if user:
            login(request, user)
            messages.info(request, "Has iniciado sesión correctamente.")
            return redirect("dashboard")  # redirección simple
        messages.error(request, "Credenciales incorrectas.")
    return render(request, "usuario/login.html")


def cerrar_sesion(request):
    logout(request)  # elimina la sesión actual del usuario
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("iniciarSesion")


@login_required
def dashboard(request):
    return render(request, "usuario/dashboard.html")  # fallback


# ============================================================
#             FUNCIONES AUXILIARES PARA DESHABILITAR/HABILITAR
# ============================================================

def _cambiar_estado_usuario(perfil, activo: bool):
    user = perfil.user
    if user.is_active != activo:
        user.is_active = activo
        user.save()
    return user.is_active


# ============================================================
#             SECCIÓN MASCOTAS 🐾
# ============================================================

@login_required
def mascotas_list(request):
    """
    Recepcionista/Admin: ven todas las mascotas.
    Cliente: solo ve sus propias mascotas.
    """
    tipo = request.user.perfil.tipo
    q = request.GET.get('q', '').strip()

    if tipo == "CLIENTE":
        mascotas = Mascota.objects.filter(dueno__perfil=request.user.perfil).order_by('id')
    elif tipo in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        mascotas = Mascota.objects.select_related('dueno').order_by('id')
    else:
        messages.error(request, "No tienes permisos para ver mascotas.")
        return redirect("dashboard")

    if q:
        mascotas = mascotas.filter(
            Q(nombre__icontains=q) |
            Q(especie__icontains=q) |
            Q(raza__icontains=q) |
            Q(dueno__nombre__icontains=q) |
            Q(dueno__apellido__icontains=q)
        )
    page_obj = Paginator(mascotas, 10).get_page(request.GET.get('page'))
    return render(request, 'mascotas/lista.html', {'page_obj': page_obj, 'q': q})


@login_required
def mascotas_crear(request):
    """
    Recepcionista/Admin: pueden crear mascotas para cualquier cliente.
    Cliente: puede crear solo sus propias mascotas (forzamos el dueño).
    """
    tipo = request.user.perfil.tipo

    if tipo not in ["RECEPCIONISTA", "ADMINISTRADOR", "CLIENTE"]:
        messages.error(request, "No tienes permisos para registrar mascotas.")
        return redirect("dashboard")

    if request.method == 'POST':
        form = MascotaForm(request.POST)
        if form.is_valid():
            mascota = form.save(commit=False)
            if tipo == "CLIENTE":
                cliente = Cliente.objects.filter(perfil=request.user.perfil).first()
                if not cliente:
                    messages.error(request, "Tu perfil no está asociado a un cliente.")
                    return redirect('mascotas_list')
                mascota.dueno = cliente  # el cliente solo puede crear para sí mismo
            mascota.save()
            messages.success(request, 'Mascota registrada correctamente.')
            return redirect('mascotas_list')
    else:
        form = MascotaForm()
    return render(request, 'mascotas/form.html', {'form': form, 'titulo': 'Registrar Mascota'})


@login_required
def mascotas_editar(request, pk):
    """
    Recepcionista/Admin: pueden editar cualquier mascota.
    Cliente: solo puede editar mascotas propias y no puede cambiar el dueño.
    """
    tipo = request.user.perfil.tipo
    mascota = get_object_or_404(Mascota, pk=pk)

    if tipo == "CLIENTE":
        es_suya = (mascota.dueno and mascota.dueno.perfil_id == request.user.perfil.id)
        if not es_suya:
            messages.error(request, "No puedes editar mascotas que no son tuyas.")
            return redirect('mascotas_list')
    elif tipo not in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para editar mascotas.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = MascotaForm(request.POST, instance=mascota)
        if form.is_valid():
            mascota_edit = form.save(commit=False)
            if tipo == "CLIENTE":
                mascota_edit.dueno = mascota.dueno  # cliente no puede reasignar dueño
            mascota_edit.save()
            messages.success(request, 'Mascota actualizada correctamente.')
            return redirect('mascotas_list')
    else:
        form = MascotaForm(instance=mascota)
    return render(request, 'mascotas/form.html', {'form': form, 'titulo': 'Editar Mascota'})


@login_required
def mascotas_habilitar(request, pk):
    """
    Operación administrativa: solo Recepcionista y Admin.
    """
    tipo = request.user.perfil.tipo
    if tipo not in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para habilitar mascotas.")
        return redirect('dashboard')

    mascota = get_object_or_404(Mascota, pk=pk)
    if not mascota.activo:
        mascota.activo = True
        mascota.save()
        messages.success(request, f'Mascota "{mascota.nombre}" habilitada.')
    else:
        messages.info(request, f'La mascota "{mascota.nombre}" ya estaba activa.')
    return redirect('mascotas_list')


@login_required
def mascotas_deshabilitar(request, pk):
    """
    Operación administrativa: solo Recepcionista y Admin.
    """
    tipo = request.user.perfil.tipo
    if tipo not in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para deshabilitar mascotas.")
        return redirect('dashboard')

    mascota = get_object_or_404(Mascota, pk=pk)
    if mascota.activo:
        mascota.activo = False
        mascota.save()
        messages.warning(request, f'Mascota "{mascota.nombre}" deshabilitada.')
    else:
        messages.info(request, f'La mascota "{mascota.nombre}" ya estaba inactiva.')
    return redirect('mascotas_list')


# ============================================================
#             SECCIÓN CLIENTES 👤
# ============================================================
@login_required
def clientes_list(request):
    """
    Solo Administrador y Recepcionista pueden ver la lista de clientes.
    """
    tipo = request.user.perfil.tipo
    if tipo not in ["ADMINISTRADOR", "RECEPCIONISTA"]:
        messages.error(request, "No tienes permisos para ver los clientes.")
        return redirect("dashboard")

    q = request.GET.get('q', '').strip()
    clientes = Cliente.objects.all().order_by('id')
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(direccion__icontains=q)
        )
    page_obj = Paginator(clientes, 10).get_page(request.GET.get('page'))
    return render(request, 'clientes/lista.html', {'page_obj': page_obj, 'q': q})


@login_required
def clientes_editar(request, pk):
    """
    Solo Administrador y Recepcionista pueden editar clientes.
    """
    tipo = request.user.perfil.tipo
    if tipo not in ["ADMINISTRADOR", "RECEPCIONISTA"]:
        messages.error(request, "No tienes permisos para editar clientes.")
        return redirect("dashboard")

    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('clientes_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/form.html', {'form': form, 'titulo': 'Editar Cliente'})


@login_required
def clientes_habilitar(request, pk):
    """
    Solo Administrador y Recepcionista pueden habilitar clientes.
    """
    tipo = request.user.perfil.tipo
    if tipo not in ["ADMINISTRADOR", "RECEPCIONISTA"]:
        messages.error(request, "No tienes permisos para habilitar clientes.")
        return redirect("dashboard")

    cliente = get_object_or_404(Cliente, pk=pk)
    user = cliente.perfil.user
    if not user.is_active:
        user.is_active = True
        user.save()
        messages.success(request, f'Cliente "{user.username}" habilitado.')
    else:
        messages.info(request, f'Cliente "{user.username}" ya estaba activo.')
    return redirect('clientes_list')


@login_required
def clientes_deshabilitar(request, pk):
    """
    Solo Administrador y Recepcionista pueden deshabilitar clientes.
    """
    tipo = request.user.perfil.tipo
    if tipo not in ["ADMINISTRADOR", "RECEPCIONISTA"]:
        messages.error(request, "No tienes permisos para deshabilitar clientes.")
        return redirect("dashboard")

    cliente = get_object_or_404(Cliente, pk=pk)
    user = cliente.perfil.user
    if user.is_active:
        user.is_active = False
        user.save()
        messages.warning(request, f'Cliente "{user.username}" deshabilitado.')
    else:
        messages.info(request, f'Cliente "{user.username}" ya estaba inactivo.')
    return redirect('clientes_list')


# ============================================================
#             SECCIÓN VETERINARIOS 🩺
# ============================================================

@login_required
def veterinarios_list(request):
    """
    Solo Administrador puede ver la lista completa de veterinarios.
    """
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "Solo el administrador puede gestionar veterinarios.")
        return redirect("dashboard")

    q = request.GET.get('q', '').strip()
    veterinarios = Veterinario.objects.all().order_by('id')
    if q:
        veterinarios = veterinarios.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(especialidad__icontains=q) |
            Q(licencia_profesional__icontains=q) |
            Q(telefono_laboral__icontains=q)
        )
    page_obj = Paginator(veterinarios, 10).get_page(request.GET.get('page'))
    return render(request, 'veterinarios/lista.html', {'page_obj': page_obj, 'q': q})


@login_required
def veterinarios_editar(request, pk):
    """
    Solo Administrador puede editar veterinarios.
    """
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "No tienes permisos para editar veterinarios.")
        return redirect("dashboard")

    vet = get_object_or_404(Veterinario, pk=pk)
    if request.method == 'POST':
        form = VeterinarioForm(request.POST, instance=vet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veterinario actualizado correctamente.')
            return redirect('veterinarios_list')
    else:
        form = VeterinarioForm(instance=vet)
    return render(request, 'veterinarios/form.html', {'form': form, 'titulo': 'Editar Veterinario'})


@login_required
def veterinarios_habilitar(request, pk):
    """
    Solo Administrador puede habilitar veterinarios.
    """
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "No tienes permisos para habilitar veterinarios.")
        return redirect("dashboard")

    vet = get_object_or_404(Veterinario, pk=pk)
    user = vet.perfil.user
    if not user.is_active:
        user.is_active = True
        user.save()
        messages.success(request, f'Veterinario "{user.username}" habilitado.')
    else:
        messages.info(request, f'Veterinario "{user.username}" ya estaba activo.')
    return redirect('veterinarios_list')


@login_required
def veterinarios_deshabilitar(request, pk):
    """
    Solo Administrador puede deshabilitar veterinarios.
    """
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "No tienes permisos para deshabilitar veterinarios.")
        return redirect("dashboard")

    vet = get_object_or_404(Veterinario, pk=pk)
    user = vet.perfil.user
    if user.is_active:
        user.is_active = False
        user.save()
        messages.warning(request, f'Veterinario "{user.username}" deshabilitado.')
    else:
        messages.info(request, f'Veterinario "{user.username}" ya estaba inactivo.')
    return redirect('veterinarios_list')


# ============================================================
#             SECCIÓN RECEPCIONISTAS 🧾
# ============================================================

@login_required
def recepcionistas_list(request):
    """
    Solo Administrador puede ver la lista completa de recepcionistas.
    """
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "Solo el administrador puede gestionar recepcionistas.")
        return redirect("dashboard")

    q = request.GET.get('q', '').strip()
    recepcionistas = Recepcionista.objects.all().order_by('id')
    if q:
        recepcionistas = recepcionistas.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(telefono__icontains=q)
        )
    page_obj = Paginator(recepcionistas, 10).get_page(request.GET.get('page'))
    return render(request, 'recepcionistas/lista.html', {'page_obj': page_obj, 'q': q})


@login_required
def recepcionistas_editar(request, pk):
    """
    Solo Administrador puede editar recepcionistas.
    """
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "No tienes permisos para editar recepcionistas.")
        return redirect("dashboard")

    rec = get_object_or_404(Recepcionista, pk=pk)
    if request.method == 'POST':
        form = RecepcionistaForm(request.POST, instance=rec)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recepcionista actualizado correctamente.')
            return redirect('recepcionistas_list')
    else:
        form = RecepcionistaForm(instance=rec)
    return render(request, 'recepcionistas/form.html', {'form': form, 'titulo': 'Editar Recepcionista'})


@login_required
def recepcionistas_habilitar(request, pk):
    """
    Solo Administrador puede habilitar recepcionistas.
    """
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "No tienes permisos para habilitar recepcionistas.")
        return redirect("dashboard")

    rec = get_object_or_404(Recepcionista, pk=pk)
    user = rec.perfil.user
    if not user.is_active:
        user.is_active = True
        user.save()
        messages.success(request, f'Recepcionista "{user.username}" habilitado.')
    else:
        messages.info(request, f'Recepcionista "{user.username}" ya estaba activo.')
    return redirect('recepcionistas_list')


@login_required
def recepcionistas_deshabilitar(request, pk):
    """
    Solo Administrador puede deshabilitar recepcionistas.
    """
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "No tienes permisos para deshabilitar recepcionistas.")
        return redirect("dashboard")

    rec = get_object_or_404(Recepcionista, pk=pk)
    user = rec.perfil.user
    if user.is_active:
        user.is_active = False
        user.save()
        messages.warning(request, f'Recepcionista "{user.username}" deshabilitado.')
    else:
        messages.info(request, f'Recepcionista "{user.username}" ya estaba inactivo.')
    return redirect('recepcionistas_list')
