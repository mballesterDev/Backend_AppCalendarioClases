# chat/views.py
import pusher
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
import logging
from uuid import UUID
import json
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from users.models import CustomUser

logger = logging.getLogger(__name__)

# Configurar Pusher con manejo de errores
try:
    pusher_client = pusher.Pusher(
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
        cluster=settings.PUSHER_CLUSTER,
        ssl=True
    )
    PUSHER_AVAILABLE = True
    logger.info("Pusher configurado correctamente")
except Exception as e:
    logger.error(f"Error configurando Pusher: {e}")
    PUSHER_AVAILABLE = False
    pusher_client = None

# Encoder personalizado para UUID
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

class ChatRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        user = self.request.user
        logger.info(f"Usuario accediendo a chats: {user.username} (rol: {user.role})")
        
        if user.role == 'teacher':
            return ChatRoom.objects.filter(teacher=user)
        else:
            return ChatRoom.objects.filter(student=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'])
    def my_chats(self, request):
        """Obtener todas las conversaciones del usuario"""
        try:
            chats = self.get_queryset()
            serializer = self.get_serializer(chats, many=True)
            logger.info(f"Encontradas {len(serializer.data)} conversaciones para {request.user.username}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error en my_chats: {e}")
            return Response(
                {"error": "Error obteniendo conversaciones"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def start_chat(self, request):
        """Iniciar una conversación (para alumnos) o obtener chat existente"""
        try:
            student = request.user
            teacher_id = request.data.get('teacher_id')
            
            if student.role != 'student':
                return Response(
                    {"error": "Solo los alumnos pueden iniciar chats"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            teacher = get_object_or_404(CustomUser, id=teacher_id, role='teacher')
            
            # Buscar chat existente o crear uno nuevo
            chat_room, created = ChatRoom.objects.get_or_create(
                student=student,
                teacher=teacher
            )
            
            serializer = self.get_serializer(chat_room)
            logger.info(f"Chat {'creado' if created else 'encontrado'} entre {student.username} y {teacher.username}")
            
            return Response(serializer.data, 
                           status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                           
        except Exception as e:
            logger.error(f"Error en start_chat: {e}")
            return Response(
                {"error": "Error iniciando chat"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        student_rooms = user.chat_rooms_as_student.all()
        teacher_rooms = user.chat_rooms_as_teacher.all()
        all_rooms = student_rooms | teacher_rooms
        return Message.objects.filter(room__in=all_rooms)

    def perform_create(self, serializer):
        try:
            message = serializer.save(sender=self.request.user)
            logger.info(f"Mensaje creado por {self.request.user.username} en room {message.room.id}")
            
            # Notificar via Pusher si está disponible
            if PUSHER_AVAILABLE and pusher_client:
                self._notify_pusher(message)
            else:
                logger.warning("Pusher no disponible para notificación")
                
        except Exception as e:
            logger.error(f"Error en perform_create: {e}")
            raise

    def _notify_pusher(self, message):
        """Notificar a Pusher sobre nuevo mensaje"""
        try:
            # Serializar el mensaje manualmente para evitar problemas de UUID
            message_data = {
                'id': str(message.id),
                'room': str(message.room.id),
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'email': message.sender.email,
                    'role': message.sender.role,
                    'country': message.sender.country
                },
                'content': message.content,
                'file': message.file.url if message.file else None,
                'file_name': message.file_name,
                'file_size': message.file_size,
                'is_read': message.is_read,
                'created_at': message.created_at.isoformat()
            }
            
            # Notificar via Pusher
            pusher_client.trigger(
                f'chat-room-{str(message.room.id)}',
                'new-message',
                {
                    'message': message_data,
                    'room_id': str(message.room.id)
                }
            )
            logger.info(f"Mensaje {message.id} notificado via Pusher")
            
        except Exception as e:
            logger.error(f"Error notificando Pusher: {e}")

    def create(self, request, *args, **kwargs):
        """Sobrescribir create para mejor manejo de errores"""
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Mensaje creado exitosamente por {request.user.username}")
            return response
        except Exception as e:
            logger.error(f"Error en create message: {e}")
            return Response(
                {"error": "Error creando mensaje: " + str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Eliminar un mensaje"""
        try:
            message = self.get_object()
            
            # Verificar que el usuario es el propietario del mensaje
            if message.sender != request.user:
                return Response(
                    {"error": "Solo puedes eliminar tus propios mensajes"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Notificar via Pusher antes de eliminar
            if PUSHER_AVAILABLE and pusher_client:
                pusher_client.trigger(
                    f'chat-room-{str(message.room.id)}',
                    'message-deleted',
                    {
                        'message_id': str(message.id),
                        'room_id': str(message.room.id)
                    }
                )
            
            message.delete()
            logger.info(f"Mensaje {message.id} eliminado por {request.user.username}")
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Error eliminando mensaje: {e}")
            return Response(
                {"error": "Error eliminando mensaje"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def room_messages(self, request):
        """Obtener mensajes de una sala específica"""
        try:
            room_id = request.query_params.get('room_id')
            if not room_id:
                return Response({"error": "room_id es requerido"}, status=400)
            
            room = get_object_or_404(ChatRoom, id=room_id)
            
            # Verificar que el usuario pertenece a esta sala
            if request.user not in [room.student, room.teacher]:
                return Response({"error": "No tienes acceso a esta sala"}, status=403)
            
            messages = Message.objects.filter(room=room).order_by('created_at')
            serializer = self.get_serializer(messages, many=True)
            logger.info(f"Enviados {len(messages)} mensajes del room {room_id}")
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error en room_messages: {e}")
            return Response(
                {"error": "Error obteniendo mensajes: " + str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marcar mensajes como leídos"""
        try:
            message = self.get_object()
            if message.room.student == request.user or message.room.teacher == request.user:
                message.is_read = True
                message.save()
                logger.info(f"Mensaje {message.id} marcado como leído")
                return Response({"status": "marked as read"})
            return Response({"error": "No autorizado"}, status=403)
        except Exception as e:
            logger.error(f"Error en mark_read: {e}")
            return Response(
                {"error": "Error marcando mensaje como leído"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def mark_room_read(self, request):
        """Marcar TODOS los mensajes de una sala como leídos"""
        try:
            room_id = request.data.get('room_id')
            if not room_id:
                return Response({"error": "room_id es requerido"}, status=400)
            
            room = get_object_or_404(ChatRoom, id=room_id)
            
            # Verificar que el usuario pertenece a esta sala
            if request.user not in [room.student, room.teacher]:
                return Response({"error": "No tienes acceso a esta sala"}, status=403)
            
            # Marcar todos los mensajes no leídos (excepto los del usuario actual) como leídos
            messages_updated = Message.objects.filter(
                room=room,
                is_read=False
            ).exclude(sender=request.user).update(is_read=True)
            
            logger.info(f"Marcados {messages_updated} mensajes como leídos en room {room_id} por {request.user.username}")
            
            # Notificar via Pusher que los mensajes fueron leídos
            if PUSHER_AVAILABLE and pusher_client:
                pusher_client.trigger(
                    f'chat-room-{str(room.id)}',
                    'messages-read',
                    {
                        'room_id': str(room.id),
                        'user_id': request.user.id,
                        'messages_updated': messages_updated
                    }
                )
            
            return Response({
                "status": "messages marked as read",
                "messages_updated": messages_updated
            })
            
        except Exception as e:
            logger.error(f"Error en mark_room_read: {e}")
            return Response(
                {"error": "Error marcando mensajes como leídos"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Vista para que el profesor vea todos los alumnos
class TeacherStudentsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            if request.user.role != 'teacher':
                return Response({"error": "Solo para profesores"}, status=403)
            
            # Obtener todos los alumnos que han tenido alguna interacción
            students = CustomUser.objects.filter(
                role='student',
                chat_rooms_as_student__teacher=request.user
            ).distinct()
            
            student_data = []
            for student in students:
                chat_room = ChatRoom.objects.filter(student=student, teacher=request.user).first()
                
                # Calcular mensajes no leídos correctamente
                unread_count = 0
                if chat_room:
                    unread_count = Message.objects.filter(
                        room=chat_room, 
                        is_read=False
                    ).exclude(sender=request.user).count()
                
                # Obtener último mensaje
                last_message = None
                if chat_room:
                    last_message_obj = chat_room.messages.last()
                    if last_message_obj:
                        last_message = {
                            'content': last_message_obj.content,
                            'created_at': last_message_obj.created_at.isoformat(),
                            'sender': last_message_obj.sender.id
                        }
                
                student_data.append({
                    'id': student.id,
                    'username': student.username,
                    'email': student.email,
                    'country': student.country,
                    'chat_room_id': str(chat_room.id) if chat_room else None,
                    'unread_messages': unread_count,
                    'last_message': last_message,  # Añadir último mensaje
                    'last_interaction': chat_room.updated_at.isoformat() if chat_room else None
                })
            
            logger.info(f"Profesor {request.user.username} ve {len(student_data)} alumnos")
            return Response(student_data)
            
        except Exception as e:
            logger.error(f"Error en TeacherStudentsViewSet: {e}")
            return Response(
                {"error": "Error obteniendo lista de alumnos"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Vista de diagnóstico
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_info(request):
    """Endpoint de diagnóstico"""
    try:
        info = {
            'user_authenticated': request.user.is_authenticated,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'username': request.user.username if request.user.is_authenticated else None,
            'user_role': request.user.role if request.user.is_authenticated else None,
            'pusher_available': PUSHER_AVAILABLE,
            'total_chat_rooms': ChatRoom.objects.count(),
            'total_messages': Message.objects.count(),
        }
        
        if request.user.is_authenticated:
            if request.user.role == 'teacher':
                info['user_chat_rooms'] = ChatRoom.objects.filter(teacher=request.user).count()
                info['user_students'] = CustomUser.objects.filter(
                    role='student',
                    chat_rooms_as_student__teacher=request.user
                ).distinct().count()
            else:
                info['user_chat_rooms'] = ChatRoom.objects.filter(student=request.user).count()
        
        return Response(info)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# Vista para descargar archivos
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_file(request, message_id):
    """Descargar archivo de un mensaje"""
    try:
        message = get_object_or_404(Message, id=message_id)
        
        # Verificar que el usuario tiene acceso al chat
        if request.user not in [message.room.student, message.room.teacher]:
            return Response({"error": "No autorizado"}, status=403)
        
        if not message.file:
            return Response({"error": "Este mensaje no tiene archivo adjunto"}, status=404)
        
        # Verificar que el archivo existe físicamente
        if not message.file.storage.exists(message.file.name):
            logger.error(f"Archivo físico no encontrado: {message.file.name}")
            return Response({"error": "El archivo no está disponible"}, status=404)
        
        # Servir el archivo para descarga
        try:
            file = message.file.open('rb')
            filename = message.file_name or message.file.name.split('/')[-1]
            
            response = FileResponse(
                file,
                as_attachment=True,
                filename=filename
            )
            
            # Agregar headers adicionales para mejor compatibilidad
            response['Content-Length'] = message.file.size
            response['Content-Type'] = 'application/octet-stream'
            
            logger.info(f"Archivo {filename} descargado por {request.user.username}")
            return response
            
        except IOError as e:
            logger.error(f"Error abriendo archivo: {e}")
            return Response({"error": "Error al acceder al archivo"}, status=500)
            
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error descargando archivo: {e}")
        return Response({"error": "Error interno del servidor"}, status=500)

# Endpoint temporal para diagnóstico de contadores
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_unread_count(request, room_id):
    """Endpoint temporal para verificar contadores"""
    try:
        room = get_object_or_404(ChatRoom, id=room_id)
        unread_count = Message.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=request.user).count()
        
        return Response({
            'room_id': room_id,
            'unread_count': unread_count,
            'total_messages': room.messages.count(),
            'user': request.user.username
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
        

# chat/views.py - AÑADE ESTA VISTA NUEVA
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_teachers(request):
    """Listar TODOS los profesores disponibles (no solo los que tienen chat)"""
    try:
        # Si el usuario es estudiante, mostrar todos los profesores
        if request.user.role == 'student':
            teachers = CustomUser.objects.filter(
                role='teacher', 
                is_active=True
            ).select_related()
            
            teacher_data = []
            for teacher in teachers:
                # Verificar si ya existe un chat con este profesor
                existing_chat = ChatRoom.objects.filter(
                    student=request.user,
                    teacher=teacher
                ).first()
                
                teacher_data.append({
                    'id': teacher.id,
                    'username': teacher.username,
                    'email': teacher.email,
                    'country': teacher.country,
                    'timezone': teacher.timezone,
                    'has_chat': existing_chat is not None,
                    'chat_room_id': str(existing_chat.id) if existing_chat else None,
                })
            
            return Response(teacher_data)
        
        # Si el usuario es profesor, mostrar todos los otros profesores
        elif request.user.role == 'teacher':
            teachers = CustomUser.objects.filter(
                role='teacher', 
                is_active=True
            ).exclude(id=request.user.id)
            
            teacher_data = []
            for teacher in teachers:
                # Verificar si ya existe un chat entre profesores
                existing_chat = ChatRoom.objects.filter(
                    teacher=request.user,
                    student=teacher
                ).first()
                
                teacher_data.append({
                    'id': teacher.id,
                    'username': teacher.username,
                    'email': teacher.email,
                    'country': teacher.country,
                    'has_chat': existing_chat is not None,
                    'chat_room_id': str(existing_chat.id) if existing_chat else None,
                })
            
            return Response(teacher_data)
        
        else:
            return Response({"error": "Usuario no válido"}, status=403)
            
    except Exception as e:
        logger.error(f"Error en list_all_teachers: {e}")
        return Response(
            {"error": "Error obteniendo lista de profesores"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
# chat/views.py - AÑADE ESTA VISTA NUEVA
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_students(request):
    """Listar TODOS los estudiantes registrados"""
    try:
        if request.user.role != 'teacher':
            return Response({"error": "Solo para profesores"}, status=403)
        
        # Obtener todos los estudiantes registrados
        students = CustomUser.objects.filter(
            role='student', 
            is_active=True
        ).order_by('username')
        
        student_data = []
        for student in students:
            # Verificar si ya existe un chat con este estudiante
            existing_chat = ChatRoom.objects.filter(
                student=student,
                teacher=request.user
            ).first()
            
            # Calcular mensajes no leídos si hay chat existente
            unread_count = 0
            last_message = None
            last_interaction = None
            
            if existing_chat:
                unread_count = Message.objects.filter(
                    room=existing_chat,
                    is_read=False
                ).exclude(sender=request.user).count()
                
                # Obtener último mensaje
                last_message_obj = existing_chat.messages.last()
                if last_message_obj:
                    last_message = {
                        'content': last_message_obj.content,
                        'created_at': last_message_obj.created_at.isoformat(),
                        'sender': last_message_obj.sender.id
                    }
                
                last_interaction = existing_chat.updated_at.isoformat()
            
            student_data.append({
                'id': student.id,
                'username': student.username,
                'email': student.email,
                'country': student.country,
                'timezone': student.timezone,
                'is_active': student.is_active,
                'date_joined': student.date_joined.isoformat() if student.date_joined else None,
                'chat_room_id': str(existing_chat.id) if existing_chat else None,
                'has_chat': existing_chat is not None,
                'unread_messages': unread_count,
                'last_message': last_message,
                'last_interaction': last_interaction
            })
        
        logger.info(f"Profesor {request.user.username} ve {len(student_data)} estudiantes totales")
        return Response(student_data)
        
    except Exception as e:
        logger.error(f"Error en list_all_students: {e}")
        return Response(
            {"error": "Error obteniendo lista de estudiantes"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )        