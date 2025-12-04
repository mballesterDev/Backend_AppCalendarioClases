from django.contrib import admin
from .models import CarritoCompra, ItemCarrito, OrdenCompra

@admin.register(CarritoCompra)
class CarritoCompraAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'get_total_quantity', 'get_total', 'creado_en']
    list_filter = ['creado_en']
    search_fields = ['usuario__username', 'usuario__email']
    readonly_fields = ['get_total', 'get_total_quantity', 'creado_en', 'actualizado_en']
    date_hierarchy = 'creado_en'
    
    def get_total_quantity(self, obj):
        """Muestra la cantidad total de items en el carrito"""
        return obj.total_quantity
    get_total_quantity.short_description = 'Cantidad Total'
    get_total_quantity.admin_order_field = 'total_quantity'
    
    def get_total(self, obj):
        """Muestra el total del carrito"""
        return f"€{obj.total}"
    get_total.short_description = 'Total'
    get_total.admin_order_field = 'total'

@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ['carrito', 'duracion_display', 'cantidad', 'precio_unitario_display', 'subtotal_display']
    list_filter = ['duracion_minutos']
    search_fields = ['carrito__usuario__username']
    
    def duracion_display(self, obj):
        return obj.get_duracion_minutos_display()
    duracion_display.short_description = 'Duración'
    
    def precio_unitario_display(self, obj):
        return f"€{obj.precio_unitario}"
    precio_unitario_display.short_description = 'Precio Unitario'
    
    def subtotal_display(self, obj):
        return f"€{obj.subtotal}"
    subtotal_display.short_description = 'Subtotal'

@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'estado', 'total_display', 'creada_en', 'completada_en']
    list_filter = ['estado', 'creada_en', 'completada_en']
    search_fields = ['usuario__username', 'usuario__email', 'stripe_payment_intent_id', 'stripe_session_id']
    readonly_fields = ['items_display', 'total_display', 'creada_en', 'completada_en', 'stripe_payment_intent_id', 'stripe_session_id']
    actions = ['marcar_como_completada', 'marcar_como_fallida', 'marcar_como_cancelada']
    date_hierarchy = 'creada_en'
    
    def total_display(self, obj):
        """Muestra el total formateado con moneda"""
        return f"€{obj.total}"
    total_display.short_description = 'Total'
    total_display.admin_order_field = 'total'
    
    def items_display(self, obj):
        """Muestra los items de la orden en formato HTML"""
        items_html = "<ul>"
        for item in obj.items:
            duracion = item['duracion_minutos']
            cantidad = item['cantidad']
            precio_unitario = item.get('precio_unitario', 0)
            subtotal = cantidad * precio_unitario
            
            items_html += f"<li>{cantidad} x {duracion} min - €{precio_unitario} cada uno = €{subtotal}</li>"
        items_html += "</ul>"
        return items_html
    items_display.short_description = 'Items'
    items_display.allow_tags = True
    
    def marcar_como_completada(self, request, queryset):
        """Marca las órdenes seleccionadas como completadas"""
        for orden in queryset:
            if orden.estado != 'completada':
                orden.marcar_como_completada()
        self.message_user(request, f"{queryset.count()} órdenes marcadas como completadas.")
    marcar_como_completada.short_description = "Marcar como completada"
    
    def marcar_como_fallida(self, request, queryset):
        """Marca las órdenes seleccionadas como fallidas"""
        for orden in queryset:
            if orden.estado != 'fallida':
                orden.marcar_como_fallida()
        self.message_user(request, f"{queryset.count()} órdenes marcadas como fallidas.")
    marcar_como_fallida.short_description = "Marcar como fallida"
    
    def marcar_como_cancelada(self, request, queryset):
        """Marca las órdenes seleccionadas como canceladas"""
        for orden in queryset:
            if orden.estado != 'cancelada':
                orden.marcar_como_cancelada()
        self.message_user(request, f"{queryset.count()} órdenes marcadas como canceladas.")
    marcar_como_cancelada.short_description = "Marcar como cancelada"