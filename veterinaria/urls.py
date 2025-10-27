from django.contrib import admin
from django.urls import path
from app import views as v

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', v.iniciarSesion, name="iniciarSesion"),
    path('inicio/', v.dashboard, name="dashboard"),

    path('registro/', v.registrar_paso1, name="registrar_paso1"),
    path('registro/vet/', v.registrar_paso2_vet, name="registrar_paso2_vet"),
    path('registro/cli/', v.registrar_paso2_cli, name="registrar_paso2_cli"),
    path('registro/final/', v.registrar_finalizar_sin_detalle, name="registrar_finalizar_sin_detalle"),
    path("registro/recep/", v.registrar_paso2_recep, name="registrar_paso2_recep"),

    path('mascotas/', v.mascotas_list, name='mascotas_list'),
    path('mascotas/crear/', v.mascotas_crear, name='mascotas_crear'),
    path('mascotas/<int:pk>/editar/', v.mascotas_editar, name='mascotas_editar'),
    path('mascotas/<int:pk>/habilitar/', v.mascotas_habilitar, name='mascotas_habilitar'),
    path('mascotas/<int:pk>/deshabilitar/', v.mascotas_deshabilitar, name='mascotas_deshabilitar'),

    path('clientes/', v.clientes_list, name='clientes_list'),
    path('clientes/<int:pk>/editar/', v.clientes_editar, name='clientes_editar'),
    path('clientes/<int:pk>/habilitar/', v.clientes_habilitar, name='clientes_habilitar'),
    path('clientes/<int:pk>/deshabilitar/', v.clientes_deshabilitar, name='clientes_deshabilitar'),

    path('veterinarios/', v.veterinarios_list, name='veterinarios_list'),
    path('veterinarios/<int:pk>/editar/', v.veterinarios_editar, name='veterinarios_editar'),
    path('veterinarios/<int:pk>/habilitar/', v.veterinarios_habilitar, name='veterinarios_habilitar'),
    path('veterinarios/<int:pk>/deshabilitar/', v.veterinarios_deshabilitar, name='veterinarios_deshabilitar'),

    path('recepcionistas/', v.recepcionistas_list, name='recepcionistas_list'),
    path('recepcionistas/<int:pk>/editar/', v.recepcionistas_editar, name='recepcionistas_editar'),
    path('recepcionistas/<int:pk>/habilitar/', v.recepcionistas_habilitar, name='recepcionistas_habilitar'),
    path('recepcionistas/<int:pk>/deshabilitar/', v.recepcionistas_deshabilitar, name='recepcionistas_deshabilitar'),
    
    path('citas/', v.citas_list, name='citas_list'),
    path('citas/crear/', v.citas_crear, name='citas_crear'),
    path('citas/<int:pk>/editar/', v.citas_editar, name='citas_editar'),
    path('citas/<int:pk>/cancelar/', v.citas_cancelar, name='citas_cancelar'),
    path('citas/<int:pk>/completar/', v.citas_completar, name='citas_completar'),
    path('citas/<int:pk>/detalle/', v.cita_detalle, name='cita_detalle'),
    
    path('consultas/<int:cita_id>/registrar/', v.consulta_registrar, name='consulta_registrar'),
    path('consultas/<int:pk>/detalle/', v.consulta_detalle, name='consulta_detalle'),
    path('mascotas/<int:mascota_id>/historial/', v.historial_medico, name='historial_medico'),
    path('mis-mascotas/historial/', v.mis_mascotas_historial, name='mis_mascotas_historial'),
    
    path("logout/", v.cerrar_sesion, name="logout"),
    
    path('veterinarios/agenda/', v.agenda_veterinarios, name='agenda_veterinarios'),
    path('veterinarios/<int:vet_id>/agenda/', v.agenda_veterinario_detalle, name='agenda_veterinario_detalle'),
    
    path('usuarios/', v.usuarios_list, name='usuarios_list'),
    path("usuarios/registrar_cliente/", v.registrar_cliente_directo, name="registrar_cliente_directo"),
]