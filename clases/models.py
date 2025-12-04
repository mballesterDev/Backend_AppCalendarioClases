# models.py
from django.db import models
from datetime import timedelta, date, datetime
from django.conf import settings

class Clase(models.Model):
    DURACION_CHOICES = [
        (25, "25 minutos"),  # ✅ CAMBIADO: 25 en lugar de 30
        (50, "50 minutos"),
        (80, "80 minutos"),  # ✅ CAMBIADO: 80 en lugar de 90
    ]

    profesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clases"
    )
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    duracion_minutos = models.IntegerField(choices=DURACION_CHOICES, default=50)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.profesor.username}"
    
    @property
    def precio(self):
        if self.duracion_minutos == 25:
            return 8
        elif self.duracion_minutos == 50:
            return 12
        elif self.duracion_minutos == 80:
            return 20
        return 0

class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente (compra iniciada)'),
        ('aceptada', 'Aceptada por el profesor'),
        ('rechazada', 'Rechazada por el profesor'),
        ('completada', 'Clase completada'),
        ('validada', 'Validada por el profesor'),
    ]

    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name="reservas")
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservas"
    )
    inicio = models.DateTimeField()
    fin = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    creada_en = models.DateTimeField(auto_now_add=True)
    comentario_profesor = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('clase', 'inicio', 'alumno')
        ordering = ['-creada_en']

    def save(self, *args, **kwargs):
        if not self.fin and self.inicio and self.clase:
            self.fin = self.inicio + timedelta(minutes=self.clase.duracion_minutos)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.clase.titulo} - {self.alumno.username} ({self.estado})"

    @property
    def puede_ser_cancelada(self):
        return self.estado not in ['completada', 'validada']

    @property
    def puede_ser_reprogramada(self):
        return self.estado == 'pendiente'


class HorarioRecurrente(models.Model):
    DIA_SEMANA_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    profesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="horarios_recurrentes"
    )
    dia_semana = models.IntegerField(choices=DIA_SEMANA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Horarios recurrentes"
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['profesor', 'dia_semana', 'hora_inicio', 'hora_fin']

    def __str__(self):
        return f"{self.profesor.username} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"

    def generar_horarios_semana(self, fecha_inicio=None):
        """Genera horarios disponibles para una semana específica"""
        if not self.activo:
            return []
        
        if not fecha_inicio:
            fecha_inicio = date.today()
        
        # Encontrar el próximo día de la semana que coincida
        dias_para_sumar = (self.dia_semana - fecha_inicio.weekday()) % 7
        fecha_dia = fecha_inicio + timedelta(days=dias_para_sumar)
        
        # Combinar fecha con hora
        inicio_datetime = datetime.combine(fecha_dia, self.hora_inicio)
        fin_datetime = datetime.combine(fecha_dia, self.hora_fin)
        
        return {
            'inicio': inicio_datetime,
            'fin': fin_datetime,
            'es_recurrente': True,
            'horario_recurrente_id': self.id
        }