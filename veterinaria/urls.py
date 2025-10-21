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
    path('admin/', admin.site.urls),
    path('', v.iniciarSesion, name="iniciarSesion"),
    path('inicio/', v.dashboard, name="dashboard"),
    path("registro/", v.registrar_paso1, name="registrar_paso1"),
    path("registro/vet/", v.registrar_paso2_vet, name="registrar_paso2_vet"),
    path("registro/cli/", v.registrar_paso2_cli, name="registrar_paso2_cli"),
    path("registro/final/", v.registrar_finalizar_sin_detalle, name="registrar_finalizar_sin_detalle")
]
