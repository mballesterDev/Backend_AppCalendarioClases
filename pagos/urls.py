from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarritoViewSet, OrdenCompraViewSet, stripe_webhook

router = DefaultRouter()
router.register(r'carrito', CarritoViewSet, basename='carrito')
router.register(r'ordenes', OrdenCompraViewSet, basename='ordenes')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),
]