# chat/admin.py
from django.contrib import admin
from .models import ChatRoom, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['id', 'created_at']
    fields = ['sender', 'content', 'file', 'is_read', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'student', 'teacher', 'message_count', 'last_message', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'student', 'teacher']
    search_fields = ['student__username', 'teacher__username', 'student__email', 'teacher__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [MessageInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'student', 'teacher')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = 'ID'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Mensajes'

    def last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return f"{last_msg.sender.username}: {last_msg.content[:50]}..."
        return "Sin mensajes"
    last_message.short_description = 'Último mensaje'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'room_info', 'sender', 'content_short', 'has_file', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at', 'sender', 'room']
    search_fields = ['content', 'sender__username', 'room__student__username', 'room__teacher__username']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información del Mensaje', {
            'fields': ('id', 'room', 'sender', 'content', 'is_read')
        }),
        ('Archivo Adjunto', {
            'fields': ('file', 'file_name', 'file_size'),
            'classes': ('collapse',)
        }),
        ('Fecha', {
            'fields': ('created_at',)
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = 'ID'

    def room_info(self, obj):
        return f"{obj.room.student.username} - {obj.room.teacher.username}"
    room_info.short_description = 'Chat Room'

    def content_short(self, obj):
        if obj.content:
            return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return "Sin contenido"
    content_short.short_description = 'Contenido'

    def has_file(self, obj):
        return "✅" if obj.file else "❌"
    has_file.short_description = 'Archivo'

    # Acciones personalizadas
    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} mensajes marcados como leídos.")
    mark_as_read.short_description = "Marcar como leído"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} mensajes marcados como no leídos.")
    mark_as_unread.short_description = "Marcar como no leído"