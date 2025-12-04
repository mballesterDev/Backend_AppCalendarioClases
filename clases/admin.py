from django.contrib import admin
from .models import Clase, Reserva

# ----- ClaseAdmin -----
@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'profesor', 'duracion_minutos', 'creada_en')
    list_filter = ('profesor', 'duracion_minutos', 'creada_en')
    search_fields = ('titulo', 'profesor__username', 'profesor__email')
    ordering = ('-creada_en',)
    readonly_fields = ('id', 'creada_en')
    fieldsets = (
        (None, {
            'fields': ('profesor', 'titulo', 'descripcion', 'duracion_minutos')
        }),
        ('Información adicional', {
            'fields': ('creada_en',)
        }),
    )

# ----- ReservaAdmin -----
@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'clase', 'alumno', 'inicio', 'fin', 'estado', 'creada_en')
    list_filter = ('estado', 'clase__profesor', 'inicio')
    search_fields = ('alumno__username', 'alumno__email', 'clase__titulo', 'clase__profesor__username')
    ordering = ('-creada_en',)
    readonly_fields = ('id', 'creada_en', 'fin')

    # Acciones rápidas para reservas
    actions = ['aceptar_reservas', 'rechazar_reservas', 'marcar_completadas', 'validar_reservas']

    def aceptar_reservas(self, request, queryset):
        for reserva in queryset:
            try:
                reserva.aceptar(reserva.clase.profesor)
            except Exception as e:
                self.message_user(request, f"No se pudo aceptar la reserva {reserva.id}: {e}", level='error')
        self.message_user(request, "Reservas seleccionadas aceptadas.")
    aceptar_reservas.short_description = "Aceptar reservas seleccionadas"

    def rechazar_reservas(self, request, queryset):
        for reserva in queryset:
            try:
                reserva.rechazar(reserva.clase.profesor, comentario="Rechazada desde admin")
            except Exception as e:
                self.message_user(request, f"No se pudo rechazar la reserva {reserva.id}: {e}", level='error')
        self.message_user(request, "Reservas seleccionadas rechazadas.")
    rechazar_reservas.short_description = "Rechazar reservas seleccionadas"

    def marcar_completadas(self, request, queryset):
        for reserva in queryset:
            try:
                reserva.marcar_completada()
            except Exception as e:
                self.message_user(request, f"No se pudo marcar la reserva {reserva.id} como completada: {e}", level='error')
        self.message_user(request, "Reservas seleccionadas marcadas como completadas.")
    marcar_completadas.short_description = "Marcar reservas como completadas"

    def validar_reservas(self, request, queryset):
        for reserva in queryset:
            try:
                reserva.validar_por_profesor(reserva.clase.profesor)
            except Exception as e:
                self.message_user(request, f"No se pudo validar la reserva {reserva.id}: {e}", level='error')
        self.message_user(request, "Reservas seleccionadas validadas.")
    validar_reservas.short_description = "Validar reservas seleccionadas"
