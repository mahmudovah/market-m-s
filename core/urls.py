"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import (
    api_root,
    dashboard,
    operator_dashboard,
    operator_ombor,
    web_kassa,
    web_ombor,
    web_profil,
    web_qarzdor,
    web_toifa,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("", dashboard, name="web-dashboard"),
    path("operator/", operator_dashboard, name="operator-dashboard"),
    path("operator/ombor/", operator_ombor, name="operator-ombor"),
    path("savdo/", include("savdo.urls")),
    path("ombor/", web_ombor, name="web-ombor"),
    path("kassa/", web_kassa, name="web-kassa"),
    path("qarzdor/", web_qarzdor, name="web-qarzdor"),
    path("toifa/", web_toifa, name="web-toifa"),
    path("profil/", web_profil, name="web-profil"),
    path("api/", api_root, name="api-root"),
    path("api/toifa/", include("toifa.urls")),
    path("api/ombor/", include("ombor.urls")),
    path("api/kassa/", include("kassa.urls")),
    path("api/qarzdor/", include("qarzdor.urls")),
    path("api/profil/", include("profil.urls")),
]
