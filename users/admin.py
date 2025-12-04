# users/admin.py - CORREGIDO
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django import forms
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 
        'email', 
        'role_display',
        'country', 
        'timezone',
        'saldo_clases_25min',
        'saldo_clases_50min',
        'saldo_clases_80min',
        'is_active',
        'date_joined'
    )
    
    list_filter = (
        'role', 
        'country', 
        'is_active', 
        'is_staff', 
        'is_superuser',
        'date_joined'
    )
    
    search_fields = (
        'username', 
        'email', 
        'first_name', 
        'last_name'
    )
    
    readonly_fields = (
        'date_joined', 
        'last_login', 
        'timezone_display',  # Cambiado de 'timezone' a 'timezone_display'
        'saldo_total_display'
    )
    
    ordering = ('-date_joined',)
    list_per_page = 25
    
    fieldsets = (
        ('Información de Cuenta', {
            'fields': (
                'username', 
                'password',
                'email'
            )
        }),
        ('Información Personal', {
            'fields': (
                'first_name', 
                'last_name'
            )
        }),
        ('Información de Perfil', {
            'fields': (
                'role',
                'country', 
                'timezone_display'  # Cambiado aquí también
            )
        }),
        ('Saldo de Clases', {
            'fields': (
                'saldo_clases_25min',
                'saldo_clases_50min',
                'saldo_clases_80min',
                'saldo_total_display'
            ),
            'classes': ('collapse', 'wide')
        }),
        ('Permisos y Estado', {
            'fields': (
                'is_active',
                'is_staff', 
                'is_superuser',
                'groups', 
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': (
                'last_login', 
                'date_joined'
            ),
            'classes': ('collapse',)
        })
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 
                'email', 
                'password1', 
                'password2',
                'role',
                'country',
                'saldo_clases_25min',
                'saldo_clases_50min',
                'saldo_clases_80min',
                'is_active', 
                'is_staff'
            ),
        }),
    )

    # Métodos para display en la lista
    def role_display(self, obj):
        color = 'green' if obj.role == 'student' else 'blue'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_display.short_description = 'Rol'
    role_display.admin_order_field = 'role'

    def timezone_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #666;">{}</span><br>'
            '<small style="color: #999;">Auto-calculado según país</small>',
            obj.timezone
        )
    timezone_display.short_description = 'Zona Horaria'

    def saldo_total_display(self, obj):
        total = obj.saldo_clases_25min + obj.saldo_clases_50min + obj.saldo_clases_80min
        color = 'green' if total > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">'
            'Total: {} clases (25min: {}, 50min: {}, 80min: {})'
            '</span>',
            color,
            total,
            obj.saldo_clases_25min,
            obj.saldo_clases_50min,
            obj.saldo_clases_80min
        )
    saldo_total_display.short_description = 'Resumen de Saldo'

    # Elimina el método get_form problemático o corrígelo así:
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and 'timezone' in form.base_fields:
            # Solo si el campo timezone existe en el formulario
            form.base_fields['timezone'].disabled = True
            form.base_fields['timezone'].help_text = "Calculado automáticamente según el país"
        return form

    # O mejor aún, elimina completamente el método get_form
    # y deja que Django maneje el formulario automáticamente

    actions = [
        'agregar_clase_25min',
        'agregar_clase_50min',
        'agregar_clase_80min', 
        'reiniciar_saldo_cero',
    ]

    def agregar_clase_25min(self, request, queryset):
        for user in queryset:
            user.saldo_clases_25min += 1
            user.save()
        self.message_user(
            request, 
            f'✅ 1 clase de 25min agregada a {queryset.count()} usuario(s).'
        )
    agregar_clase_25min.short_description = "➕ Agregar 1 clase de 25min"

    def agregar_clase_50min(self, request, queryset):
        for user in queryset:
            user.saldo_clases_50min += 1
            user.save()
        self.message_user(
            request, 
            f'✅ 1 clase de 50min agregada a {queryset.count()} usuario(s).'
        )
    agregar_clase_50min.short_description = "➕ Agregar 1 clase de 50min"

    def agregar_clase_80min(self, request, queryset):
        for user in queryset:
            user.saldo_clases_80min += 1
            user.save()
        self.message_user(
            request, 
            f'✅ 1 clase de 80min agregada a {queryset.count()} usuario(s).'
        )
    agregar_clase_80min.short_description = "➕ Agregar 1 clase de 80min"

    def reiniciar_saldo_cero(self, request, queryset):
        updated = queryset.update(
            saldo_clases_25min=0,
            saldo_clases_50min=0,
            saldo_clases_80min=0
        )
        self.message_user(
            request, 
            f'🔄 Saldo reiniciado a 0 para {updated} usuario(s).'
        )
    reiniciar_saldo_cero.short_description = "🔄 Reiniciar saldo a 0"