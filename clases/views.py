# views.py - VERSION COMPLETA CORREGIDA (USANDO NOMBRES DEL MODELO)
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Clase, Reserva, HorarioRecurrente
from .serializers import ClaseSerializer, ReservaSerializer, CrearReservaSerializer, HorarioRecurrenteSerializer, CrearHorarioRecurrenteSerializer
from django.utils import timezone
from datetime import datetime, date, timedelta
import pytz

class ClaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Clase.objects.all()
    serializer_class = ClaseSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Clase.objects.all()
        
        profesor_id = self.request.query_params.get('profesor_id')
        if profesor_id:
            queryset = queryset.filter(profesor_id=profesor_id)
            
        return queryset

class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CrearReservaSerializer
        return ReservaSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return self.queryset.filter(alumno=user)
        elif user.role == 'teacher':
            return self.queryset.filter(clase__profesor=user)
        return Reserva.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        try:
            print(f"\n🔵 Nueva reserva desde cliente:")
            print(f"  → Usuario: {request.user.username} ({request.user.role})")
            print(f"  → Datos recibidos: {request.data}")
            
            response = super().create(request, *args, **kwargs)
            print(f"✅ Reserva creada: ID {response.data.get('id')}")
            return response
            
        except Exception as e:
            print(f"❌ Error creando reserva: {str(e)}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        user = request.user
        
        if user.role == 'student' and reserva.alumno != user:
            return Response(
                {"error": "No puedes cancelar esta reserva"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.role == 'teacher' and reserva.clase.profesor != user:
            return Response(
                {"error": "No puedes cancelar esta reserva"},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ CORREGIDO: Usar nombres del modelo
        if user.role == 'student' and reserva.estado not in ['cancelada', 'rechazada']:
            duracion = reserva.clase.duracion_minutos
            if duracion == 25:
                user.saldo_clases_25min += 1
                print(f"  → Saldo 25min devuelto: {user.saldo_clases_25min - 1} → {user.saldo_clases_25min}")
            elif duracion == 50:
                user.saldo_clases_50min += 1
                print(f"  → Saldo 50min devuelto: {user.saldo_clases_50min - 1} → {user.saldo_clases_50min}")
            elif duracion == 80:
                user.saldo_clases_80min += 1
                print(f"  → Saldo 80min devuelto: {user.saldo_clases_80min - 1} → {user.saldo_clases_80min}")
            user.save()
        
        reserva_id = reserva.id
        reserva.delete()

        return Response({
            "message": "Reserva eliminada completamente" + (" y clase devuelta al saldo" if user.role == 'student' else ""),
            "reserva_id": reserva_id
        })

    @action(detail=True, methods=['post'])
    def cambiar_fecha(self, request, pk=None):
        reserva = self.get_object()
        user = request.user
        nueva_fecha = request.data.get('inicio')

        if not nueva_fecha:
            return Response(
                {"error": "Se requiere nueva fecha"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.role == 'student' and reserva.alumno != user:
            return Response(
                {"error": "No puedes cambiar esta reserva"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.role == 'teacher' and reserva.clase.profesor != user:
            return Response(
                {"error": "No puedes cambiar esta reserva"},
                status=status.HTTP_403_FORBIDDEN
            )

        if reserva.estado != 'pendiente':
            return Response(
                {"error": "Solo se pueden cambiar reservas pendientes"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            nueva_fecha_dt = datetime.fromisoformat(nueva_fecha.replace('Z', '+00:00'))
            if timezone.is_naive(nueva_fecha_dt):
                nueva_fecha_dt = timezone.make_aware(nueva_fecha_dt, timezone=pytz.UTC)
            
            if nueva_fecha_dt < timezone.now():
                return Response(
                    {"error": "No se puede reprogramar a una fecha pasada"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, AttributeError):
            return Response(
                {"error": "Formato de fecha inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conflicto = Reserva.objects.filter(
            clase=reserva.clase,
            inicio=nueva_fecha_dt
        ).exclude(id=reserva.id).exists()

        if conflicto:
            return Response(
                {"error": "Ya existe una reserva en ese horario"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reserva.inicio = nueva_fecha_dt
        reserva.fin = nueva_fecha_dt + timedelta(minutes=reserva.clase.duracion_minutos)
        reserva.save()

        return Response({
            "message": "Fecha cambiada exitosamente",
            "reserva": ReservaSerializer(reserva, context={'request': request}).data
        })

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        reserva = self.get_object()
        user = request.user
        nuevo_estado = request.data.get('estado')

        if user.role != 'teacher' or reserva.clase.profesor != user:
            return Response(
                {"error": "Solo el profesor de la clase puede cambiar el estado"},
                status=status.HTTP_403_FORBIDDEN
            )

        if nuevo_estado not in ['aceptada', 'rechazada', 'completada', 'validada']:
            return Response(
                {"error": "Estado no válido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ CORREGIDO: Usar nombres del modelo
        if nuevo_estado == 'rechazada' and reserva.alumno.role == 'student' and reserva.estado not in ['rechazada', 'cancelada']:
            duracion = reserva.clase.duracion_minutos
            if duracion == 25:
                reserva.alumno.saldo_clases_25min += 1
                print(f"  → Saldo 25min devuelto por rechazo: {reserva.alumno.saldo_clases_25min - 1} → {reserva.alumno.saldo_clases_25min}")
            elif duracion == 50:
                reserva.alumno.saldo_clases_50min += 1
                print(f"  → Saldo 50min devuelto por rechazo: {reserva.alumno.saldo_clases_50min - 1} → {reserva.alumno.saldo_clases_50min}")
            elif duracion == 80:
                reserva.alumno.saldo_clases_80min += 1
                print(f"  → Saldo 80min devuelto por rechazo: {reserva.alumno.saldo_clases_80min - 1} → {reserva.alumno.saldo_clases_80min}")
            reserva.alumno.save()

        reserva.estado = nuevo_estado
        reserva.save()

        return Response({
            "message": f"Estado cambiado a {nuevo_estado}",
            "reserva": ReservaSerializer(reserva, context={'request': request}).data
        })

class HorarioRecurrenteViewSet(viewsets.ModelViewSet):
    queryset = HorarioRecurrente.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CrearHorarioRecurrenteSerializer
        return HorarioRecurrenteSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return HorarioRecurrente.objects.filter(profesor=user)
        return HorarioRecurrente.objects.none()

    @action(detail=False, methods=['get'])
    def mis_horarios(self, request):
        if request.user.role != 'teacher':
            return Response(
                {"error": "Solo los profesores pueden acceder a este endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        horarios = HorarioRecurrente.objects.filter(profesor=request.user)
        serializer = self.get_serializer(horarios, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def disponibilidad_profesor(self, request):
        profesor_id = request.GET.get('profesor_id')
        if not profesor_id:
            return Response(
                {"error": "Se requiere profesor_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from users.models import CustomUser
            profesor = CustomUser.objects.get(id=profesor_id, role='teacher')
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Profesor no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_timezone = request.user.timezone or 'UTC'
        
        disponibilidad = []
        fecha_inicio = date.today()
        horarios_recurrentes = HorarioRecurrente.objects.filter(
            profesor=profesor, 
            activo=True
        )
        
        for semana in range(4):
            for horario in horarios_recurrentes:
                fecha_semana = fecha_inicio + timedelta(weeks=semana)
                horario_generado = horario.generar_horarios_semana(fecha_semana)
                
                if horario_generado:
                    inicio_spain = timezone.make_aware(horario_generado['inicio'], timezone=pytz.timezone('Europe/Madrid'))
                    fin_spain = timezone.make_aware(horario_generado['fin'], timezone=pytz.timezone('Europe/Madrid'))
                    
                    inicio_utc = inicio_spain.astimezone(pytz.UTC)
                    fin_utc = fin_spain.astimezone(pytz.UTC)
                    
                    try:
                        user_tz = pytz.timezone(user_timezone)
                        inicio_display = inicio_utc.astimezone(user_tz).isoformat()
                        fin_display = fin_utc.astimezone(user_tz).isoformat()
                    except Exception as e:
                        inicio_display = inicio_utc.isoformat()
                        fin_display = fin_utc.isoformat()
                    
                    reserva_existente = Reserva.objects.filter(
                        clase__profesor=profesor,
                        inicio=inicio_utc,
                        estado__in=['pendiente', 'aceptada']
                    ).exists()
                    
                    if not reserva_existente:
                        slot = {
                            'inicio': inicio_display,
                            'fin': fin_display,
                            'inicio_utc': inicio_utc.isoformat(),
                            'fin_utc': fin_utc.isoformat(),
                            'profesor_nombre': profesor.username,
                            'profesor_id': profesor.id,
                            'es_recurrente': True,
                            'timezone_visualizacion': user_timezone,
                        }
                        disponibilidad.append(slot)
        
        return Response(disponibilidad)

    @action(detail=False, methods=['get'])
    def disponibilidad_semana(self, request):
        if request.user.role != 'teacher':
            return Response(
                {"error": "Solo los profesores pueden ver disponibilidad"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        fecha_inicio = request.GET.get('fecha_inicio')
        if fecha_inicio:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = date.today()
        else:
            fecha_inicio = date.today()
        
        user_timezone = request.user.timezone or 'UTC'
        
        disponibilidad = []
        horarios_recurrentes = HorarioRecurrente.objects.filter(
            profesor=request.user, 
            activo=True
        )
        
        for semana in range(4):
            for horario in horarios_recurrentes:
                fecha_semana = fecha_inicio + timedelta(weeks=semana)
                horario_generado = horario.generar_horarios_semana(fecha_semana)
                
                if horario_generado:
                    inicio_spain = timezone.make_aware(horario_generado['inicio'], timezone=pytz.timezone('Europe/Madrid'))
                    fin_spain = timezone.make_aware(horario_generado['fin'], timezone=pytz.timezone('Europe/Madrid'))
                    
                    inicio_utc = inicio_spain.astimezone(pytz.UTC)
                    fin_utc = fin_spain.astimezone(pytz.UTC)
                    
                    try:
                        user_tz = pytz.timezone(user_timezone)
                        inicio_display = inicio_utc.astimezone(user_tz).isoformat()
                        fin_display = fin_utc.astimezone(user_tz).isoformat()
                    except Exception as e:
                        inicio_display = inicio_utc.isoformat()
                        fin_display = fin_utc.isoformat()
                    
                    slot = {
                        'inicio': inicio_display,
                        'fin': fin_display,
                        'inicio_utc': inicio_utc.isoformat(),
                        'fin_utc': fin_utc.isoformat(),
                        'es_recurrente': True,
                        'horario_recurrente_id': horario.id,
                        'timezone_visualizacion': user_timezone,
                    }
                    disponibilidad.append(slot)
        
        return Response(disponibilidad)

class BuscarProfesoresViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def listar(self, request):
        from users.models import CustomUser
        
        profesores = CustomUser.objects.filter(role='teacher', is_active=True)
        
        profesores_data = []
        for profesor in profesores:
            clases_count = Clase.objects.filter(profesor=profesor).count()
            horarios_count = HorarioRecurrente.objects.filter(profesor=profesor, activo=True).count()
            
            profesores_data.append({
                'id': profesor.id,
                'username': profesor.username,
                'email': profesor.email,
                'country': profesor.get_country_display(),
                'timezone': profesor.timezone,
                'clases_count': clases_count,
                'horarios_activos': horarios_count,
            })
        
        return Response(profesores_data)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        user = request.user
        
        if user.role == 'teacher':
            total_clases = Clase.objects.filter(profesor=user).count()
            total_reservas = Reserva.objects.filter(clase__profesor=user).count()
            reservas_pendientes = Reserva.objects.filter(
                clase__profesor=user, 
                estado='pendiente'
            ).count()
            reservas_aceptadas = Reserva.objects.filter(
                clase__profesor=user, 
                estado='aceptada'
            ).count()
            reservas_completadas = Reserva.objects.filter(
                clase__profesor=user, 
                estado__in=['completada', 'validada']
            ).count()
            
            return Response({
                'total_clases': total_clases,
                'total_reservas': total_reservas,
                'reservas_pendientes': reservas_pendientes,
                'reservas_aceptadas': reservas_aceptadas,
                'reservas_completadas': reservas_completadas,
                'user_timezone': user.timezone,
            })
            
        elif user.role == 'student':
            total_reservas = Reserva.objects.filter(alumno=user).count()
            reservas_activas = Reserva.objects.filter(
                alumno=user,
                estado__in=['pendiente', 'aceptada']
            ).count()
            reservas_completadas = Reserva.objects.filter(
                alumno=user,
                estado__in=['completada', 'validada']
            ).count()
            
            return Response({
                'total_reservas': total_reservas,
                'reservas_activas': reservas_activas,
                'reservas_completadas': reservas_completadas,
                # ✅ CORREGIDO: USAR NOMBRES DEL MODELO
                'saldo_25min': user.saldo_clases_25min,
                'saldo_50min': user.saldo_clases_50min,
                'saldo_80min': user.saldo_clases_80min,
                'user_timezone': user.timezone,
            })
        
        return Response({"error": "Rol no válido"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def proximas_clases(self, request):
        user = request.user
        ahora = timezone.now()
        
        if user.role == 'teacher':
            proximas = Reserva.objects.filter(
                clase__profesor=user,
                inicio__gte=ahora,
                estado__in=['aceptada', 'pendiente']
            ).order_by('inicio')[:10]
            
        elif user.role == 'student':
            proximas = Reserva.objects.filter(
                alumno=user,
                inicio__gte=ahora,
                estado__in=['aceptada', 'pendiente']
            ).order_by('inicio')[:10]
            
        else:
            return Response({"error": "Rol no válido"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ReservaSerializer(proximas, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def panel_estudiante(self, request):
        if request.user.role != 'student':
            return Response(
                {"error": "Solo para estudiantes"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = request.user
        ahora = timezone.now()
        
        reservas_activas = Reserva.objects.filter(
            alumno=user,
            inicio__gte=ahora,
            estado__in=['pendiente', 'aceptada']
        ).order_by('inicio')
        
        reservas_completadas = Reserva.objects.filter(
            alumno=user,
            estado__in=['completada', 'validada']
        ).order_by('-inicio')[:10]
        
        reservas_activas_serializer = ReservaSerializer(reservas_activas, many=True, context={'request': request})
        reservas_completadas_serializer = ReservaSerializer(reservas_completadas, many=True, context={'request': request})
        
        return Response({
            'saldo': {
                # ✅ CORREGIDO: USAR NOMBRES DEL MODELO
                '25min': user.saldo_clases_25min,
                '50min': user.saldo_clases_50min,
                '80min': user.saldo_clases_80min,
                'total': user.saldo_clases_25min + user.saldo_clases_50min + user.saldo_clases_80min,
            },
            'reservas_activas': reservas_activas_serializer.data,
            'reservas_completadas': reservas_completadas_serializer.data,
            'timezone_info': {
                'user_timezone': user.timezone,
                'server_timezone': 'UTC',
                'current_time_user_tz': timezone.now().astimezone(pytz.timezone(user.timezone)).isoformat() if user.timezone else None,
                'current_time_utc': timezone.now().isoformat(),
            },
        })