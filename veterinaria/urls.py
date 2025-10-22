
from django.contrib import admin
from django.urls import path
from app import views as v

urlpatterns = [
    # Administración
    path('admin/', admin.site.urls),

    # Inicio de sesión / Dashboard
    path('', v.iniciarSesion, name="iniciarSesion"),      # página principal = login
    path('inicio/', v.dashboard, name="dashboard"),        # dashboard después de iniciar sesión

    # Registro de usuarios
    path('registro/', v.registrar_paso1, name="registrar_paso1"),
    path('registro/vet/', v.registrar_paso2_vet, name="registrar_paso2_vet"),
    path('registro/cli/', v.registrar_paso2_cli, name="registrar_paso2_cli"),
    path('registro/final/', v.registrar_finalizar_sin_detalle, name="registrar_finalizar_sin_detalle"),

    # --- Mascotas ---
    path('mascotas/', v.mascotas_list, name='mascotas_list'),
    path('mascotas/crear/', v.mascotas_crear, name='mascotas_crear'),
    path('mascotas/<int:pk>/editar/', v.mascotas_editar, name='mascotas_editar'),
    path('mascotas/<int:pk>/habilitar/', v.mascotas_habilitar, name='mascotas_habilitar'),
    path('mascotas/<int:pk>/deshabilitar/', v.mascotas_deshabilitar, name='mascotas_deshabilitar'),

    # --- Clientes ---
    path('clientes/', v.clientes_list, name='clientes_list'),
    path('clientes/<int:pk>/editar/', v.clientes_editar, name='clientes_editar'),
    path('clientes/<int:pk>/habilitar/', v.clientes_habilitar, name='clientes_habilitar'),
    path('clientes/<int:pk>/deshabilitar/', v.clientes_deshabilitar, name='clientes_deshabilitar'),

    # --- Veterinarios ---
    path('veterinarios/', v.veterinarios_list, name='veterinarios_list'),
    path('veterinarios/<int:pk>/editar/', v.veterinarios_editar, name='veterinarios_editar'),
    path('veterinarios/<int:pk>/habilitar/', v.veterinarios_habilitar, name='veterinarios_habilitar'),
    path('veterinarios/<int:pk>/deshabilitar/', v.veterinarios_deshabilitar, name='veterinarios_deshabilitar'),

    # --- Recepcionistas ---
    path('recepcionistas/', v.recepcionistas_list, name='recepcionistas_list'),
    path('recepcionistas/<int:pk>/editar/', v.recepcionistas_editar, name='recepcionistas_editar'),
    path('recepcionistas/<int:pk>/habilitar/', v.recepcionistas_habilitar, name='recepcionistas_habilitar'),
    path('recepcionistas/<int:pk>/deshabilitar/', v.recepcionistas_deshabilitar, name='recepcionistas_deshabilitar'),


]