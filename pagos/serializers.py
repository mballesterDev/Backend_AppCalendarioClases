from rest_framework import serializers
from .models import CarritoCompra, ItemCarrito, OrdenCompra


class ItemCarritoSerializer(serializers.ModelSerializer):
    duracion_display = serializers.CharField(
        source='get_duracion_minutos_display',
        read_only=True
    )
    precio_unitario = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )
    subtotal = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = ItemCarrito
        fields = [
            'id',
            'duracion_minutos',
            'duracion_display',
            'cantidad',
            'precio_unitario',
            'subtotal'
        ]


class CarritoCompraSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    total = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = CarritoCompra
        fields = [
            'id',
            'items',
            'total',
            'total_quantity',
            'creado_en',
            'actualizado_en'
        ]


class AgregarAlCarritoSerializer(serializers.Serializer):
    duracion_minutos = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1, max_value=100)

    def validate_duracion_minutos(self, value):
        if value not in [25, 50, 80]:
            raise serializers.ValidationError(
                "Duración debe ser 25, 50 u 80 minutos"
            )
        return value


class ActualizarCantidadSerializer(serializers.Serializer):
    duracion_minutos = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1, max_value=100)

    def validate_duracion_minutos(self, value):
        if value not in [25, 50, 80]:
            raise serializers.ValidationError(
                "Duración debe ser 25, 50 u 80 minutos"
            )
        return value


class OrdenCompraSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    items_detalle = serializers.SerializerMethodField()

    class Meta:
        model = OrdenCompra
        fields = [
            'id',
            'usuario',
            'items',
            'items_detalle',
            'total',
            'estado',
            'estado_display',
            'stripe_payment_intent_id',
            'stripe_session_id',
            'creada_en',
            'completada_en'
        ]
        read_only_fields = ['usuario', 'total', 'estado', 'items']

    def get_items_detalle(self, obj):
        """Procesar los items para mostrar información más detallada"""
        items_detalle = []
        precios = {25: 6, 50: 12, 80: 16}
        
        for item in obj.items:
            precio_unitario = precios.get(item['duracion_minutos'], 0)
            duracion_display = f"{item['duracion_minutos']} minutos"
            
            items_detalle.append({
                'duracion_minutos': item['duracion_minutos'],
                'duracion_display': duracion_display,
                'cantidad': item['cantidad'],
                'precio_unitario': precio_unitario,
                'subtotal': precio_unitario * item['cantidad']
            })
        
        return items_detalle


class PreciosSerializer(serializers.Serializer):
    """Serializer para obtener precios"""
    duracion_25min = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )
    duracion_50min = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )
    duracion_80min = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )