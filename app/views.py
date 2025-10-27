from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from datetime import date

from app.forms import RegistroForm, VeterinarioForm, ClienteForm, MascotaForm, RecepcionistaForm, CitaForm, ConsultaForm
from .models import Perfil, Mascota, Cliente, Recepcionista, Veterinario, Cita, Consulta
from app.forms import RegistroClienteRecepForm

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


@login_required
def registrar_cliente_directo(request):
    """
    Permite al recepcionista registrar directamente un usuario tipo CLIENTE.
    El tipo se fija en la creación del Perfil (no se muestra en el formulario).
    """
    tipo = getattr(request.user.perfil, "tipo", None)
    if tipo != "RECEPCIONISTA":
        messages.error(request, "No tienes permisos para registrar clientes.")
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistroClienteRecepForm(request.POST)
        if form.is_valid():
            try:
                # 1) Crear usuario (con contraseña encriptada por UserCreationForm)
                user = form.save(commit=False)  # crea instancia User sin guardar
                user.email = form.cleaned_data["email"]
                user.save()

                # 2) Crear Perfil con tipo fijo "CLIENTE"
                perfil = Perfil.objects.create(
                    user=user,
                    tipo="CLIENTE",
                    rut=form.cleaned_data["rut"],
                    telefono=form.cleaned_data["telefono"],
                )

                # 3) Crear Cliente con datos del form
                Cliente.objects.create(
                    perfil=perfil,
                    nombre=form.cleaned_data["nombre"],
                    apellido=form.cleaned_data["apellido"],
                    direccion=form.cleaned_data["direccion"],
                )

                messages.success(request, f"Cliente '{user.username}' registrado correctamente.")
                return redirect("usuarios_list")
            except Exception as e:
                messages.error(request, f"Ocurrió un error al registrar el cliente: {e}")
    else:
        form = RegistroClienteRecepForm()

    return render(request, "usuario/registrar_cliente.html", {"form": form})


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

@login_required
def usuarios_list(request):
    # Permisos: Admin y Recepcionista pueden ver la lista
    tipo = getattr(request.user.perfil, "tipo", None)
    if tipo not in ["ADMINISTRADOR", "RECEPCIONISTA"]:
        messages.error(request, "No tienes permisos para ver usuarios.")
        return redirect("dashboard")

    q = request.GET.get("q", "").strip()

    # Trae perfiles relacionados (siempre que existan)
    usuarios = (User.objects
                .select_related("perfil")
                .order_by("username"))

    if q:
        usuarios = usuarios.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(perfil__tipo__icontains=q) |
            Q(perfil__rut__icontains=q) |
            Q(perfil__telefono__icontains=q)
        )

    page_obj = Paginator(usuarios, 10).get_page(request.GET.get("page"))

    return render(request, "usuario/lista.html", {
        "page_obj": page_obj,
        "q": q,
    })
    
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
    tipo = request.user.perfil.tipo if hasattr(request.user, "perfil") else "DESCONOCIDO"
    ctx = {"tipo": tipo}

    now = timezone.localtime()
    hoy = now.date()

    inicio_hoy = timezone.make_aware(
        timezone.datetime.combine(hoy, timezone.datetime.min.time())
    )
    fin_hoy = timezone.make_aware(
        timezone.datetime.combine(hoy, timezone.datetime.max.time())
    )

    if tipo == "VETERINARIO":
        vet = Veterinario.objects.filter(perfil=request.user.perfil).first()
        citas_hoy = Cita.objects.filter(
            veterinario=vet, fecha_hora__range=(inicio_hoy, fin_hoy)
        ).order_by('fecha_hora') if vet else Cita.objects.none()
        ctx["citas_hoy"] = citas_hoy

    elif tipo == "RECEPCIONISTA":
        citas_programadas = Cita.objects.filter(
            estado='PROGRAMADO'
        ).order_by('fecha_hora')[:50]
        ctx["citas_programadas"] = citas_programadas

    elif tipo == "CLIENTE":
        cliente = Cliente.objects.filter(perfil=request.user.perfil).first()
        citas_proximas = Cita.objects.filter(
            mascota__dueno=cliente,
            fecha_hora__gte=now
        ).order_by('fecha_hora') if cliente else Cita.objects.none()
        ctx["citas_proximas"] = citas_proximas[:50]

    elif tipo == "ADMINISTRADOR":
        # Resumen
        stats = {
            "clientes": Cliente.objects.count(),
            "veterinarios": Veterinario.objects.count(),
            "recepcionistas": Recepcionista.objects.count(),
            "mascotas": Mascota.objects.count(),
            "citas_total": Cita.objects.count(),
            "citas_programadas": Cita.objects.filter(estado='PROGRAMADO').count(),
            "citas_completadas": Cita.objects.filter(estado='COMPLETADO').count(),
            "citas_canceladas": Cita.objects.filter(estado='CANCELADO').count(),
            "citas_hoy": Cita.objects.filter(fecha_hora__range=(inicio_hoy, fin_hoy)).count(),
        }

        # Semana actual (lunes-domingo)
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        inicio_semana_dt = timezone.make_aware(
            timezone.datetime.combine(inicio_semana, timezone.datetime.min.time())
        )
        fin_semana_dt = timezone.make_aware(
            timezone.datetime.combine(fin_semana, timezone.datetime.max.time())
        )
        stats["citas_semana"] = Cita.objects.filter(
            fecha_hora__range=(inicio_semana_dt, fin_semana_dt)
        ).count()

        ctx["stats"] = stats
        ctx["citas_proximas"] = Cita.objects.filter(
            estado='PROGRAMADO'
        ).order_by('fecha_hora')[:20]

    return render(request, "usuario/dashboard.html", ctx)


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
    tipo = request.user.perfil.tipo

    if tipo not in ["RECEPCIONISTA", "ADMINISTRADOR", "CLIENTE"]:
        messages.error(request, "No tienes permisos para registrar mascotas.")
        return redirect("dashboard")

    if request.method == 'POST':
        form = MascotaForm(request.POST, user=request.user)
        if form.is_valid():
            mascota = form.save(commit=False)
            if tipo == "CLIENTE":
                cliente = Cliente.objects.filter(perfil=request.user.perfil).first()
                if not cliente:
                    messages.error(request, "Tu perfil no está asociado a un cliente.")
                    return redirect('mascotas_list')
                mascota.dueno = cliente
            mascota.save()
            messages.success(request, 'Mascota registrada correctamente.')
            return redirect('mascotas_list')
    else:
        form = MascotaForm(user=request.user)
    return render(request, 'mascotas/form.html', {'form': form, 'titulo': 'Registrar Mascota'})


@login_required
def mascotas_editar(request, pk):
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
        form = MascotaForm(request.POST, instance=mascota, user=request.user)
        if form.is_valid():
            mascota_edit = form.save(commit=False)
            if tipo == "CLIENTE":
                mascota_edit.dueno = mascota.dueno
            mascota_edit.save()
            messages.success(request, 'Mascota actualizada correctamente.')
            return redirect('mascotas_list')
    else:
        form = MascotaForm(instance=mascota, user=request.user)
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
    # Solo admin puede deshabilitar
    tipo = request.user.perfil.tipo
    if tipo != "ADMINISTRADOR":
        messages.error(request, "No tienes permisos para deshabilitar veterinarios.")
        return redirect("dashboard")

    vet = get_object_or_404(Veterinario, pk=pk)
    user = vet.perfil.user

    # ❗ Bloquear si tiene citas PROGRAMADAS o consultas registradas
    tiene_programadas = Cita.objects.filter(veterinario=vet, estado='PROGRAMADO').exists()

    if tiene_programadas:
        messages.error(
            request,
            f'No puedes deshabilitar al veterinario "{user.username}" porque tiene citas programadas.'
        )
        return redirect('veterinarios_list')

    # Si pasa los chequeos, procede a deshabilitar
    if user.is_active:
        user.is_active = False
        user.save()
        messages.warning(request, f'Veterinario "{user.username}" deshabilitado.')
    else:
        messages.info(request, f'Veterinario "{user.username}" ya estaba inactivo.')
    return redirect('veterinarios_list')


@login_required
def agenda_veterinarios(request):
    """
    Admin y Recepcionista: ven tarjetas de veterinarios para abrir su agenda.
    """
    tipo = request.user.perfil.tipo
    if tipo not in ["ADMINISTRADOR", "RECEPCIONISTA"]:
        messages.error(request, "No tienes permisos para ver la agenda de veterinarios.")
        return redirect("dashboard")

    q = request.GET.get('q', '').strip()
    vets = Veterinario.objects.all().order_by('apellido', 'nombre')
    if q:
        vets = vets.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) |
            Q(especialidad__icontains=q) | Q(licencia_profesional__icontains=q)
        )

    return render(request, 'veterinarios/agenda_index.html', {
        'veterinarios': vets,
        'q': q,
    })


@login_required
def agenda_veterinario_detalle(request, vet_id):
    """
    Agenda de un veterinario: próximas citas, con filtro por hoy/semana/todas.
    """
    tipo = request.user.perfil.tipo
    if tipo not in ["ADMINISTRADOR", "RECEPCIONISTA"]:
        messages.error(request, "No tienes permisos para ver esta agenda.")
        return redirect("dashboard")

    vet = get_object_or_404(Veterinario, pk=vet_id)
    filtro = request.GET.get('filtro', 'hoy')  # hoy | semana | todas
    now = timezone.localtime()
    hoy = now.date()

    citas = Cita.objects.filter(veterinario=vet, estado='PROGRAMADO').order_by('fecha_hora')

    if filtro == 'hoy':
        inicio_dia = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.min.time()))
        fin_dia = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.max.time()))
        citas = citas.filter(fecha_hora__range=(inicio_dia, fin_dia))
    elif filtro == 'semana':
        inicio_sem = hoy - timedelta(days=hoy.weekday())
        fin_sem = inicio_sem + timedelta(days=6)
        inicio_sem_dt = timezone.make_aware(timezone.datetime.combine(inicio_sem, timezone.datetime.min.time()))
        fin_sem_dt = timezone.make_aware(timezone.datetime.combine(fin_sem, timezone.datetime.max.time()))
        citas = citas.filter(fecha_hora__range=(inicio_sem_dt, fin_sem_dt))
    # 'todas' no filtra adicional

    return render(request, 'veterinarios/agenda_detalle.html', {
        'vet': vet,
        'citas': citas,
        'filtro': filtro
    })

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


#Citas

@login_required
def citas_list(request):
    
    tipo = request.user.perfil.tipo
    q = request.GET.get('q', '').strip()
    filtro = request.GET.get('filtro', 'todas')  # ← NUEVO

    if tipo == "VETERINARIO":
        veterinario = Veterinario.objects.filter(perfil=request.user.perfil).first()
        if veterinario:
            citas = Cita.objects.filter(veterinario=veterinario).order_by('-fecha_hora')
        else:
            citas = Cita.objects.none()
    elif tipo == "CLIENTE":
        cliente = Cliente.objects.filter(perfil=request.user.perfil).first()
        if cliente:
            citas = Cita.objects.filter(mascota__dueno=cliente).order_by('-fecha_hora')
        else:
            citas = Cita.objects.none()
    elif tipo in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        citas = Cita.objects.all().order_by('-fecha_hora')
    else:
        messages.error(request, "No tienes permisos para ver las citas.")
        return redirect("dashboard")
    
    # ⬇️ ESTA ES LA PARTE NUEVA (filtros de fecha) ⬇️
    hoy = timezone.now().date()
    
    if filtro == 'hoy':
        inicio_dia = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.min.time()))
        fin_dia = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.max.time()))
        citas = citas.filter(fecha_hora__gte=inicio_dia, fecha_hora__lte=fin_dia)
    elif filtro == 'semana':
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        inicio_semana_dt = timezone.make_aware(timezone.datetime.combine(inicio_semana, timezone.datetime.min.time()))
        fin_semana_dt = timezone.make_aware(timezone.datetime.combine(fin_semana, timezone.datetime.max.time()))
        citas = citas.filter(fecha_hora__gte=inicio_semana_dt, fecha_hora__lte=fin_semana_dt)
    # ⬆️ HASTA AQUÍ LA PARTE NUEVA ⬆️

    if q:
        citas = citas.filter(
            Q(mascota__nombre__icontains=q) |
            Q(mascota__dueno__nombre__icontains=q) |
            Q(mascota__dueno__apellido__icontains=q) |
            Q(veterinario__nombre__icontains=q) |
            Q(veterinario__apellido__icontains=q) |
            Q(motivo__icontains=q)
        )

    page_obj = Paginator(citas, 10).get_page(request.GET.get('page'))
    return render(request, 'citas/lista.html', {
        'page_obj': page_obj,
        'q': q,
        'filtro': filtro  # ← NUEVO (pasamos el filtro al template)
    })


@login_required
def citas_crear(request):
    tipo = request.user.perfil.tipo
    if tipo not in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para agendar citas.")
        return redirect("dashboard")

    dueno_id = request.GET.get('dueno') or request.POST.get('dueno')
    
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            mascota_id = request.POST.get('mascota')
            cita.mascota_id = mascota_id
            try:
                cita.full_clean()  # <-- valida reglas del modelo
                cita.save()
                messages.success(request, 'Cita agendada correctamente.')
                return redirect('citas_list')
            except ValidationError as e:
                # Llevar errores al form y seguir mostrando
                for field, errs in e.message_dict.items():
                    for err in errs:
                        form.add_error(field if field in form.fields else None, err)
                messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = CitaForm()
    
    if dueno_id:
        mascotas = Mascota.objects.filter(activo=True, dueno_id=dueno_id)
    else:
        mascotas = Mascota.objects.none()
    
    clientes = Cliente.objects.all().order_by('apellido', 'nombre')
    
    return render(request, 'citas/form.html', {
        'form': form, 
        'titulo': 'Agendar Cita',
        'mascotas': mascotas,
        'clientes': clientes,
        'dueno_seleccionado': dueno_id
    })


@login_required
def citas_editar(request, pk):
    tipo = request.user.perfil.tipo
    if tipo not in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para editar citas.")
        return redirect("dashboard")

    cita = get_object_or_404(Cita, pk=pk)
    dueno_id = request.GET.get('dueno') or request.POST.get('dueno') or str(cita.mascota.dueno.id)
    
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            cita_edit = form.save(commit=False)
            mascota_id = request.POST.get('mascota')
            cita_edit.mascota_id = mascota_id
            try:
                cita_edit.full_clean()   # <-- valida reglas del modelo
                cita_edit.save()
                messages.success(request, 'Cita actualizada correctamente.')
                return redirect('citas_list')
            except ValidationError as e:
                for field, errs in e.message_dict.items():
                    for err in errs:
                        form.add_error(field if field in form.fields else None, err)
                messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = CitaForm(instance=cita)
    
    mascotas = Mascota.objects.filter(activo=True, dueno_id=dueno_id) if dueno_id else Mascota.objects.none()
    clientes = Cliente.objects.all().order_by('apellido', 'nombre')
    
    return render(request, 'citas/form.html', {
        'form': form, 
        'titulo': 'Editar Cita',
        'mascotas': mascotas,
        'clientes': clientes,
        'dueno_seleccionado': dueno_id,
        'mascota_seleccionada': cita.mascota.id
    })


@login_required
def citas_cancelar(request, pk):
    tipo = request.user.perfil.tipo
    if tipo not in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para cancelar citas.")
        return redirect("dashboard")

    cita = get_object_or_404(Cita, pk=pk)
    if cita.estado != 'CANCELADO':
        cita.estado = 'CANCELADO'
        cita.save()
        messages.warning(request, f'Cita cancelada correctamente.')
    else:
        messages.info(request, 'Esta cita ya estaba cancelada.')
    return redirect('citas_list')


@login_required
def citas_completar(request, pk):
    tipo = request.user.perfil.tipo
    if tipo not in ["VETERINARIO", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para completar citas.")
        return redirect("dashboard")

    cita = get_object_or_404(Cita, pk=pk)
    if cita.estado == 'PROGRAMADO':
        cita.estado = 'COMPLETADO'
        cita.save()
        messages.success(request, f'Cita marcada como completada.')
    else:
        messages.info(request, f'Esta cita ya estaba en estado {cita.estado}.')
    return redirect('citas_list')


@login_required
def cita_detalle(request, pk):
    tipo = request.user.perfil.tipo
    cita = get_object_or_404(Cita, pk=pk)
    
    if tipo == "VETERINARIO":
        veterinario = Veterinario.objects.filter(perfil=request.user.perfil).first()
        if not veterinario or cita.veterinario != veterinario:
            messages.error(request, "No puedes ver citas que no te corresponden.")
            return redirect("citas_list")
    elif tipo == "CLIENTE":
        cliente = Cliente.objects.filter(perfil=request.user.perfil).first()
        if not cliente or cita.mascota.dueno != cliente:
            messages.error(request, "No puedes ver citas que no son de tus mascotas.")
            return redirect("citas_list")
    elif tipo not in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para ver esta cita.")
        return redirect("dashboard")
    
    tiene_consulta = hasattr(cita, 'consulta')
    
    return render(request, 'citas/detalle.html', {
        'cita': cita,
        'tiene_consulta': tiene_consulta
    })


@login_required
def consulta_registrar(request, cita_id):
    tipo = request.user.perfil.tipo
    if tipo not in ["VETERINARIO", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para registrar consultas.")
        return redirect("dashboard")
    
    cita = get_object_or_404(Cita, pk=cita_id)
    
    if tipo == "VETERINARIO":
        veterinario = Veterinario.objects.filter(perfil=request.user.perfil).first()
        if not veterinario or cita.veterinario != veterinario:
            messages.error(request, "Solo puedes registrar consultas de tus propias citas.")
            return redirect("citas_list")
    
    if hasattr(cita, 'consulta'):
        messages.warning(request, "Esta cita ya tiene una consulta registrada.")
        return redirect('consulta_detalle', pk=cita.consulta.id)
    
    if cita.estado == 'CANCELADO':
        messages.error(request, "No se puede registrar consulta para una cita cancelada.")
        return redirect('cita_detalle', pk=cita_id)
    
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.cita = cita
            consulta.save()
            
            cita.estado = 'COMPLETADO'
            cita.save()
            
            # ⬇️ ESTA ES LA PARTE NUEVA ⬇️
            if consulta.proxima_cita:
                from datetime import datetime, time
                fecha_proxima = consulta.proxima_cita
                hora_sugerida = time(10, 0)
                fecha_hora_proxima = datetime.combine(fecha_proxima, hora_sugerida)
                
                nueva_cita = Cita(
                    mascota=cita.mascota,
                    veterinario=cita.veterinario,
                    fecha_hora=fecha_hora_proxima,
                    motivo=f"Control post: {consulta.diagnostico[:50]}",
                    observaciones=f"Cita de seguimiento sugerida en consulta del {consulta.fecha_consulta}",
                    estado='PROGRAMADO'
                )
                nueva_cita.save()
                messages.success(request, f'Consulta registrada y próxima cita agendada para el {fecha_proxima.strftime("%d/%m/%Y")} a las 10:00.')
            else:
                messages.success(request, 'Consulta registrada correctamente.')
            # ⬆️ HASTA AQUÍ LA PARTE NUEVA ⬆️
            
            return redirect('cita_detalle', pk=cita_id)
    else:
        from django.utils import timezone
        form = ConsultaForm(initial={'fecha_consulta': timezone.now().date()})
    
    return render(request, 'consultas/form.html', {
        'form': form,
        'cita': cita,
        'titulo': 'Registrar Consulta'
    })


@login_required
def consulta_detalle(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)
    cita = consulta.cita
    tipo = request.user.perfil.tipo
    
    if tipo == "VETERINARIO":
        veterinario = Veterinario.objects.filter(perfil=request.user.perfil).first()
        if not veterinario or cita.veterinario != veterinario:
            messages.error(request, "No puedes ver consultas que no te corresponden.")
            return redirect("citas_list")
    elif tipo == "CLIENTE":
        cliente = Cliente.objects.filter(perfil=request.user.perfil).first()
        if not cliente or cita.mascota.dueno != cliente:
            messages.error(request, "No puedes ver consultas que no son de tus mascotas.")
            return redirect("citas_list")
    elif tipo not in ["RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para ver esta consulta.")
        return redirect("dashboard")
    
    return render(request, 'consultas/detalle.html', {'consulta': consulta})


@login_required
def historial_medico(request, mascota_id):
    mascota = get_object_or_404(Mascota, pk=mascota_id)
    tipo = request.user.perfil.tipo
    
    if tipo == "CLIENTE":
        cliente = Cliente.objects.filter(perfil=request.user.perfil).first()
        if not cliente or mascota.dueno != cliente:
            messages.error(request, "No puedes ver el historial de mascotas que no son tuyas.")
            return redirect("mascotas_list")
    elif tipo not in ["VETERINARIO", "RECEPCIONISTA", "ADMINISTRADOR"]:
        messages.error(request, "No tienes permisos para ver historiales médicos.")
        return redirect("dashboard")
    
    consultas = Consulta.objects.filter(cita__mascota=mascota).order_by('-fecha_consulta')
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        consultas = consultas.filter(fecha_consulta__gte=fecha_desde)
    if fecha_hasta:
        consultas = consultas.filter(fecha_consulta__lte=fecha_hasta)
    
    page_obj = Paginator(consultas, 10).get_page(request.GET.get('page'))
    
    return render(request, 'consultas/historial.html', {
        'mascota': mascota,
        'page_obj': page_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta
    })

@login_required
def mis_mascotas_historial(request):
    tipo = request.user.perfil.tipo
    if tipo != "CLIENTE":
        messages.error(request, "Esta sección es solo para clientes.")
        return redirect("dashboard")
    
    cliente = Cliente.objects.filter(perfil=request.user.perfil).first()
    if not cliente:
        messages.error(request, "No se encontró información de cliente.")
        return redirect("dashboard")
    
    mascotas = Mascota.objects.filter(dueno=cliente, activo=True)
    
    hoy = date.today()
    mascotas_con_edad = []
    for m in mascotas:
        edad_texto = "—"
        if m.fecha_nacimiento:
            # cálculo de años
            anios = hoy.year - m.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (m.fecha_nacimiento.month, m.fecha_nacimiento.day)
            )
            if anios > 0:
                edad_texto = f"{anios} año{'s' if anios != 1 else ''}"
            else:
                # calcular diferencia en meses
                meses = (hoy.year - m.fecha_nacimiento.year) * 12 + (hoy.month - m.fecha_nacimiento.month)
                if hoy.day < m.fecha_nacimiento.day:
                    meses -= 1  # aún no cumple el mes completo
                edad_texto = f"{meses} mes{'es' if meses != 1 else ''}"
                if meses < 0:
                    edad_texto = "0 meses"
        mascotas_con_edad.append({
            "mascota": m,
            "edad": edad_texto,
        })
    
    return render(request, 'consultas/mis_mascotas_historial.html', {
        'mascotas_con_edad': mascotas_con_edad,
        'cliente': cliente
    })
