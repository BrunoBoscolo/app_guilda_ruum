"""
URL configuration for config project.

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
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from guilda_manager.views import (
    sede_view, missoes_view, construcoes_view, construcoes_projetos_view,
    construcoes_infra_view, bestiario_list_view, bestiario_hub_view,
    bestiario_rememoracao_view, bestiario_edit_view, bestiario_create_view,
    landing_view, mestre_view, root_routing_view, entry_portal_view,
    create_guild_view, sync_guild_view, share_guild_view, mapa_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('guilda_manager.urls')),
    path('', root_routing_view, name='root'),
    path('landing/', landing_view, name='landing'),
    path('entry/', entry_portal_view, name='entry_portal'),
    path('create-guild/', create_guild_view, name='create_guild'),
    path('sync-guild/', sync_guild_view, name='sync_guild'),
    path('share-guild/', share_guild_view, name='share_guild'),
    path('sede/', sede_view, name='sede'),
    path('missoes/', missoes_view, name='missoes'),
    path('construcoes/', construcoes_view, name='construcoes'),
    path('construcoes/projetos/', construcoes_projetos_view, name='construcoes_projetos'),
    path('construcoes/infra/', construcoes_infra_view, name='construcoes_infra'),
    path('mestre/', mestre_view, name='mestre'),
    path('mapa/', mapa_view, name='mapa'),
    path('bestiario/', bestiario_hub_view, name='bestiario'),
    path('bestiario/lista/', bestiario_list_view, name='bestiario_list'),
    path('bestiario/rememoracao/', bestiario_rememoracao_view, name='bestiario_rememoracao'),
    path('bestiario/novo/', bestiario_create_view, name='bestiario_create'),
    path('bestiario/editar/<slug:slug>/', bestiario_edit_view, name='bestiario_edit'),
    re_path(r'^sede/(?P<path>.*)$', serve, {
        'document_root': str(settings.BASE_DIR / 'frontend_standalone'),
    }),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
