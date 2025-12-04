# serializers.py - VERSION CORREGIDA
from rest_framework import serializers
from .models import Clase, Reserva, HorarioRecurrente
from datetime import timedelta
from django.utils import timezone
import pytz

class ClaseSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.CharField(source="profesor.username", read_only=True)
    precio = serializers.SerializerMethodField()

    class Meta:
        model = Clase
        fields = ['id', 'titulo', 'descripcion', 'duracion_minutos', 'precio', 'profesor', 'profesor_nombre']

    def get_precio(self, obj):
        if obj.duracion_minutos == 25:
            return 8
        elif obj.duracion_minutos == 50:
            return 12
        elif obj.duracion_minutos == 80:
            return 20
        return 0

class ReservaSerializer(serializers.ModelSerializer):
    clase_info = ClaseSerializer(source="clase", read_only=True)
    alumno_nombre = serializers.CharField(source="alumno.username", read_only=True)
    puede_cancelar = serializers.SerializerMethodField()
    puede_cambiar = serializers.SerializerMethodField()
    
    inicio = serializers.SerializerMethodField()
    fin = serializers.SerializerMethodField()
    
    inicio_utc = serializers.DateTimeField(source='inicio', format='iso-8601', read_only=True)
    fin_utc = serializers.DateTimeField(source='fin', format='iso-8601', read_only=True)

    class Meta:
        model = Reserva
        fields = [
            'id', 'clase', 'clase_info', 'alumno', 'alumno_nombre',
            'inicio', 'fin', 'inicio_utc', 'fin_utc', 'estado', 
            'creada_en', 'comentario_profesor', 'puede_cancelar', 'puede_cambiar'
        ]
        read_only_fields = ['alumno', 'fin', 'estado', 'creada_en']

    def get_inicio(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_timezone = request.user.timezone
                if user_timezone:
                    tz = pytz.timezone(user_timezone)
                    if timezone.is_aware(obj.inicio):
                        return obj.inicio.astimezone(tz).isoformat()
                    else:
                        return timezone.make_aware(obj.inicio, pytz.UTC).astimezone(tz).isoformat()
            except Exception as e:
                print(f"⚠️ Error convirtiendo timezone: {e}")
        
        return obj.inicio.isoformat() if timezone.is_aware(obj.inicio) else timezone.make_aware(obj.inicio, pytz.UTC).isoformat()

    def get_fin(self, obj):
        if not obj.fin:
            return None
            
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_timezone = request.user.timezone
                if user_timezone:
                    tz = pytz.timezone(user_timezone)
                    if timezone.is_aware(obj.fin):
                        return obj.fin.astimezone(tz).isoformat()
                    else:
                        return timezone.make_aware(obj.fin, pytz.UTC).astimezone(tz).isoformat()
            except Exception as e:
                print(f"⚠️ Error convirtiendo timezone fin: {e}")
        
        return obj.fin.isoformat() if timezone.is_aware(obj.fin) else timezone.make_aware(obj.fin, pytz.UTC).isoformat()

    def get_puede_cancelar(self, obj):
        return obj.estado not in ['completada', 'validada', 'cancelada']

    def get_puede_cambiar(self, obj):
        return obj.estado == 'pendiente'

class CrearReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = ['clase', 'inicio']

    def validate_inicio(self, value):
        if isinstance(value, str):
            try:
                value = serializers.DateTimeField().to_internal_value(value)
            except Exception as e:
                raise serializers.ValidationError(f"Formato de fecha inválido: {str(e)}")
        
        request = self.context.get('request')
        user_timezone = 'Europe/Madrid'
        
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_timezone = request.user.timezone or 'Europe/Madrid'
        
        try:
            if timezone.is_naive(value):
                user_tz = pytz.timezone(user_timezone)
                value = user_tz.localize(value)
            
            spain_tz = pytz.timezone('Europe/Madrid')
            value_spain = value.astimezone(spain_tz)
            value_utc = value_spain.astimezone(pytz.UTC)
            
        except Exception as e:
            print(f"❌ Error en conversión de timezone: {e}")
            if timezone.is_naive(value):
                value = timezone.make_aware(value, timezone=pytz.UTC)
        
        if value < timezone.now():
            raise serializers.ValidationError("No se puede reservar en fechas pasadas")
        
        return value

    def validate(self, data):
        user = self.context['request'].user
        clase = data['clase']
        inicio = data['inicio']

        if user.role not in ['student', 'teacher']:
            raise serializers.ValidationError("Solo estudiantes y profesores pueden reservar clases")

        # ✅ CORREGIDO: Usar nombres del modelo
        if user.role == 'student':
            if clase.duracion_minutos == 25 and user.saldo_clases_25min <= 0:
                raise serializers.ValidationError("No tienes saldo suficiente para clases de 25 minutos")
            elif clase.duracion_minutos == 50 and user.saldo_clases_50min <= 0:
                raise serializers.ValidationError("No tienes saldo suficiente para clases de 50 minutos")
            elif clase.duracion_minutos == 80 and user.saldo_clases_80min <= 0:
                raise serializers.ValidationError("No tienes saldo suficiente para clases de 80 minutos")

        reserva_existente = Reserva.objects.filter(
            clase=clase,
            inicio=inicio
        ).exists()
        
        if reserva_existente:
            raise serializers.ValidationError("Ya existe una reserva en este horario")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        clase = validated_data['clase']
        inicio = validated_data['inicio']
        
        fin = inicio + timedelta(minutes=clase.duracion_minutos)
        
        # ✅ CORREGIDO: Descontar saldo usando nombres del modelo
        if user.role == 'student':
            if clase.duracion_minutos == 25:
                if user.saldo_clases_25min <= 0:
                    raise serializers.ValidationError("No tienes saldo suficiente para clases de 25 minutos")
                user.saldo_clases_25min -= 1
                print(f"  → Saldo 25min descontado: {user.saldo_clases_25min + 1} → {user.saldo_clases_25min}")
            elif clase.duracion_minutos == 50:
                if user.saldo_clases_50min <= 0:
                    raise serializers.ValidationError("No tienes saldo suficiente para clases de 50 minutos")
                user.saldo_clases_50min -= 1
                print(f"  → Saldo 50min descontado: {user.saldo_clases_50min + 1} → {user.saldo_clases_50min}")
            elif clase.duracion_minutos == 80:
                if user.saldo_clases_80min <= 0:
                    raise serializers.ValidationError("No tienes saldo suficiente para clases de 80 minutos")
                user.saldo_clases_80min -= 1
                print(f"  → Saldo 80min descontado: {user.saldo_clases_80min + 1} → {user.saldo_clases_80min}")
            user.save()

        estado_inicial = 'pendiente' if user.role == 'student' else 'aceptada'

        reserva = Reserva.objects.create(
            clase=clase,
            alumno=user,
            inicio=inicio,
            fin=fin,
            estado=estado_inicial
        )

        return reserva

class HorarioRecurrenteSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.CharField(source="profesor.username", read_only=True)
    dia_semana_nombre = serializers.CharField(source="get_dia_semana_display", read_only=True)
    
    hora_inicio = serializers.SerializerMethodField()
    hora_fin = serializers.SerializerMethodField()
    
    class Meta:
        model = HorarioRecurrente
        fields = ['id', 'profesor', 'profesor_nombre', 'dia_semana', 'dia_semana_nombre', 
                 'hora_inicio', 'hora_fin', 'activo', 'creado_en']
        read_only_fields = ['profesor', 'creado_en']

    def get_hora_inicio(self, obj):
        return obj.hora_inicio.strftime('%H:%M') if obj.hora_inicio else None

    def get_hora_fin(self, obj):
        return obj.hora_fin.strftime('%H:%M') if obj.hora_fin else None

class CrearHorarioRecurrenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioRecurrente
        fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'activo']

    def validate(self, data):
        hora_inicio = data['hora_inicio']
        hora_fin = data['hora_fin']
        
        if hora_fin <= hora_inicio:
            raise serializers.ValidationError("La hora de fin debe ser después de la hora de inicio")
        
        duracion_minutos = (hora_fin.hour * 60 + hora_fin.minute) - (hora_inicio.hour * 60 + hora_inicio.minute)
        if duracion_minutos < 25:
            raise serializers.ValidationError("La duración mínima debe ser de 25 minutos")
        
        user = self.context['request'].user
        
        if user.role != 'teacher':
            raise serializers.ValidationError("Solo los profesores pueden configurar horarios recurrentes")
        
        horarios_solapados = HorarioRecurrente.objects.filter(
            profesor=user,
            dia_semana=data['dia_semana'],
            activo=True,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio
        ).exclude(id=self.instance.id if self.instance else None).exists()
        
        if horarios_solapados:
            raise serializers.ValidationError("Este horario se solapa con otro horario recurrente existente")
        
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        return HorarioRecurrente.objects.create(profesor=user, **validated_data)