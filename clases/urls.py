# clases/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clases', views.ClaseViewSet)
router.register(r'reservas', views.ReservaViewSet)
router.register(r'horarios-recurrentes', views.HorarioRecurrenteViewSet)
router.register(r'dashboard', views.DashboardViewSet, basename='dashboard')
router.register(r'buscar-profesores', views.BuscarProfesoresViewSet, basename='buscar-profesores')

urlpatterns = [
    path('', include(router.urls)),  # ← Cambiado a path vacío
]