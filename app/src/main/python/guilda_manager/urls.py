from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GuildViewSet, QuestViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'guilds', GuildViewSet, basename='guild')
router.register(r'quests', QuestViewSet, basename='quest')

urlpatterns = [
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
