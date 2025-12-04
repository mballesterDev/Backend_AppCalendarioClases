# chatRoom/serializers.py
from rest_framework import serializers
from .models import ChatRoom, Message
from users.models import CustomUser

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'country']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSimpleSerializer(read_only=True)
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=ChatRoom.objects.all(), 
        source='room', 
        write_only=True,
        required=True
    )
    
    # Convertir UUID a string para JSON
    id = serializers.UUIDField(read_only=True)
    room = serializers.UUIDField(source='room.id', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'room_id', 'sender', 'content', 'file', 
                 'file_name', 'file_size', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at', 'file_name', 'file_size', 'sender']

    def create(self, validated_data):
        # Asignar automáticamente el sender desde el request
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['sender'] = request.user
        else:
            raise serializers.ValidationError("Usuario no autenticado")
        
        return super().create(validated_data)

class ChatRoomSerializer(serializers.ModelSerializer):
    student = UserSimpleSerializer(read_only=True)
    teacher = UserSimpleSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    # Convertir UUID a string
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['id', 'student', 'teacher', 'created_at', 'updated_at', 
                 'last_message', 'unread_count']

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Solo contar mensajes de otros usuarios que no estén leídos
            return obj.messages.filter(
                is_read=False
            ).exclude(sender=request.user).count()
        return 0