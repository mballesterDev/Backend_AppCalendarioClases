# chat/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'teacher-students', views.TeacherStudentsViewSet, basename='teacher-students')

# chat/urls.py
urlpatterns = [
    path('', include(router.urls)),
    path('debug/', views.debug_info, name='debug-info'), 
    path('download/<uuid:message_id>/', views.download_file, name='download-file'),
    path('messages/mark_room_read/', views.MessageViewSet.as_view({'post': 'mark_room_read'}), name='mark-room-read'),
    path('check_unread/<uuid:room_id>/', views.check_unread_count, name='check-unread'),
    path('teachers/all/', views.list_all_teachers, name='list-all-teachers'),
    path('students/all/', views.list_all_students, name='list-all-students'),  # ← NUEVA RUTA
]