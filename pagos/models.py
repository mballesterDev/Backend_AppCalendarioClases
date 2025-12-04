from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class CarritoCompra(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_quantity(self):
        return sum(item.cantidad for item in self.items.all())

    class Meta:
        verbose_name = "Carrito de Compra"
        verbose_name_plural = "Carritos de Compra"


class ItemCarrito(models.Model):
    DURACION_CHOICES = [
        (25, '25 minutos'),
        (50, '50 minutos'),
        (80, '80 minutos'),
    ]

    PRECIOS = {
        25: 6,
        50: 12,
        80: 16,
    }

    carrito = models.ForeignKey(
        CarritoCompra,
        on_delete=models.CASCADE,
        related_name='items'
    )
    duracion_minutos = models.IntegerField(choices=DURACION_CHOICES)
    cantidad = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ['carrito', 'duracion_minutos']
        verbose_name = "Item de Carrito"
        verbose_name_plural = "Items de Carrito"

    def __str__(self):
        return f"{self.cantidad} x {self.get_duracion_minutos_display()}"

    @property
    def precio_unitario(self):
        return self.PRECIOS.get(self.duracion_minutos, 0)

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad


class OrdenCompra(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de pago'),
        ('completada', 'Completada'),
        ('fallida', 'Fallida'),
        ('cancelada', 'Cancelada'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ordenes'
    )
    items = models.JSONField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    stripe_payment_intent_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    stripe_session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    completada_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-creada_en']
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"

    def __str__(self):
        return f"Orden #{self.id} - {self.usuario.username} - {self.total}€"

    def marcar_como_completada(self):
        """Marca la orden como completada y añade las clases al usuario"""
        if self.estado != 'completada':
            self.estado = 'completada'
            self.completada_en = timezone.now()
            self.save()

            # Añadir las clases al saldo del usuario
            usuario = self.usuario
            for item in self.items:
                duracion = item['duracion_minutos']
                cantidad = item['cantidad']
                
                if duracion == 25:
                    usuario.saldo_clases_25min += cantidad
                elif duracion == 50:
                    usuario.saldo_clases_50min += cantidad
                elif duracion == 80:
                    usuario.saldo_clases_80min += cantidad
            
            usuario.save()

    def marcar_como_fallida(self):
        self.estado = 'fallida'
        self.save()

    def marcar_como_cancelada(self):
        self.estado = 'cancelada'
        self.save()