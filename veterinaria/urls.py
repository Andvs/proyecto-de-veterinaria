"""
URL configuration for veterinaria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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

    # Mascotas 🐾
    path('mascotas/', v.mascotas_list, name='mascotas_list'),
    path('mascotas/crear/', v.mascotas_crear, name='mascotas_crear'),
    path('mascotas/<int:pk>/editar/', v.mascotas_editar, name='mascotas_editar'),
    path('mascotas/<int:pk>/eliminar/', v.mascotas_eliminar, name='mascotas_eliminar'),
    
    # Cliente
    path('clientes/', v.clientes_list, name='clientes_list'),
    path('clientes/<int:pk>/editar/', v.clientes_editar, name='clientes_editar'),
    path('clientes/<int:pk>/eliminar/', v.clientes_eliminar, name='clientes_eliminar'),

    # VETERINARIOS 
    path('veterinarios/', v.veterinarios_list, name='veterinarios_list'),
    path('veterinarios/<int:pk>/editar/', v.veterinarios_editar, name='veterinarios_editar'),
    path('veterinarios/<int:pk>/eliminar/', v.veterinarios_eliminar, name='veterinarios_eliminar'),

    # RECEPCIONISTA
    path('recepcionistas/', v.recepcionistas_list, name='recepcionistas_list'),
    path('recepcionistas/<int:pk>/editar/', v.recepcionistas_editar, name='recepcionistas_editar'),
    path('recepcionistas/<int:pk>/eliminar/', v.recepcionistas_eliminar, name='recepcionistas_eliminar'),


]