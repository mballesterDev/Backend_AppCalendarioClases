# users/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate  # ← AÑADE 'authenticate' aquí
from rest_framework.authtoken.models import Token
from .models import CustomUser
from .serializers import CustomUserSerializer, CustomRegisterSerializer, UserSimpleSerializer, UserProfileSerializer, UpdateProfileSerializer
import pytz
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny 
User = get_user_model()

# -----------------------------------
# ViewSet de usuarios (para GET/PUT/DELETE)
# -----------------------------------
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para usuarios.
    - GET /users/ -> lista todos
    - GET /users/<id>/ -> detalle
    - POST /users/ -> crear (con rol)
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Permite filtrar por rol usando ?role=teacher o ?role=student
        """
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        if role in ['teacher', 'student']:
            queryset = queryset.filter(role=role)
        return queryset

# -----------------------------------
# Registro de usuarios
# -----------------------------------
class RegisterUserAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CustomRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # No necesitas pasar 'request'
            # Devolver los datos del usuario creado
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'country': user.country,
                'timezone': user.timezone,
                'message': 'Usuario registrado exitosamente'
            }
            return Response(user_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------------
# Lista de países
# -----------------------------------
@api_view(['GET'])
def get_countries(request):
    """
    🌍 Devuelve la lista de países del modelo CustomUser
    """
    countries = [{"code": code, "name": name} for code, name in CustomUser.COUNTRY_CHOICES]
    return Response(countries)

# -----------------------------------
# Lista de timezones
# -----------------------------------
@api_view(['GET'])
def get_timezones(request):
    """
    🕓 Devuelve todas las zonas horarias disponibles (pytz)
    """
    timezones = [{"name": tz, "value": tz} for tz in pytz.all_timezones]
    return Response(timezones)

# ✅ CORREGIR: Vista comprar_clase_virtual para incluir 30 minutos
@api_view(['POST'])
@permission_classes([AllowAny])  # ← Permitir acceso sin autenticación
def comprar_clase_virtual(request):
    """
    Endpoint SIN autenticación para testing
    """
    try:
        duracion = request.data.get('duracion_minutos')
        
        # ✅ CORREGIR: Incluir 30 minutos
        if duracion not in [30, 50, 90]:
            return Response(
                {"error": "La duración debe ser 30, 50 o 90 minutos"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # SIMULAR compra sin base de datos
        return Response({
            "message": f"✅ ¡Clase de {duracion} minutos comprada exitosamente!",
            "duracion": duracion,
            "status": "success"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ✅ CORREGIR: Vista user_profile para usar el serializer completo
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Endpoint para obtener perfil completo del usuario"""
    user = request.user
    serializer = UserProfileSerializer(user)
    return Response(serializer.data)

# ✅ CORREGIR: Vista comprar_saldo_clases para incluir 30 minutos
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comprar_saldo_clases(request):
    """
    Endpoint para comprar saldo de clases
    """
    try:
        duracion = request.data.get('duracion_minutos')
        cantidad = request.data.get('cantidad', 1)
        
        # ✅ CORREGIR: Incluir 30 minutos
        if duracion not in [30, 50, 90]:
            return Response(
                {"error": "La duración debe ser 30, 50 o 90 minutos"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cantidad <= 0:
            return Response(
                {"error": "La cantidad debe ser mayor a 0"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Añadir saldo al usuario
        request.user.comprar_clase(duracion, cantidad)
        
        # ✅ CORREGIR: Incluir saldo de 30 minutos en la respuesta
        return Response({
            "message": f"✅ ¡{cantidad} clase(s) de {duracion} minutos comprada(s) exitosamente!",
            "nuevo_saldo_30min": request.user.saldo_clases_30min,
            "nuevo_saldo_50min": request.user.saldo_clases_50min,
            "nuevo_saldo_90min": request.user.saldo_clases_90min,
            "status": "success"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ✅ NUEVO: Vista para actualizar perfil
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Actualizar perfil del usuario"""
    serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ NUEVO: Vista para obtener saldo completo
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_balance(request):
    """Obtener saldo completo del usuario"""
    user = request.user
    return Response({
        'saldo': {
            '30min': user.saldo_clases_30min,
            '50min': user.saldo_clases_50min,
            '90min': user.saldo_clases_90min,
            'total': user.saldo_clases_30min + user.saldo_clases_50min + user.saldo_clases_90min
        },
        'user_timezone': user.timezone,
        'role': user.role
    })

# ✅ NUEVO: Vista para administradores recargar saldo
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_recargar_saldo(request):
    """
    Endpoint para que administradores recarguen saldo a usuarios
    """
    from .serializers import RecargarSaldoSerializer
    
    # Verificar que sea admin
    if not request.user.is_staff:
        return Response(
            {"error": "Solo los administradores pueden usar este endpoint"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = RecargarSaldoSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        duracion = serializer.validated_data['duracion_minutos']
        cantidad = serializer.validated_data['cantidad']
        
        # Recargar saldo
        user.comprar_clase(duracion, cantidad)
        
        return Response({
            "message": f"✅ Se han añadido {cantidad} clase(s) de {duracion} minutos al usuario {user.username}",
            "nuevo_saldo_usuario": {
                '30min': user.saldo_clases_30min,
                '50min': user.saldo_clases_50min,
                '90min': user.saldo_clases_90min
            },
            "status": "success"
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ NUEVO: Vista para listar profesores
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_profesores(request):
    """Listar todos los profesores disponibles"""
    profesores = CustomUser.objects.filter(role='teacher', is_active=True)
    serializer = UserSimpleSerializer(profesores, many=True)
    return Response(serializer.data)

# ✅ NUEVO: Vista para detalle de profesor
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_profesor(request, profesor_id):
    """Obtener detalle de un profesor específico"""
    try:
        profesor = CustomUser.objects.get(id=profesor_id, role='teacher', is_active=True)
        serializer = UserProfileSerializer(profesor)
        return Response(serializer.data)
    except CustomUser.DoesNotExist:
        return Response(
            {"error": "Profesor no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

# users/views.py - AÑADE ESTO AL FINAL DEL ARCHIVO


@api_view(['POST'])
@permission_classes([AllowAny])
def custom_login(request):
    """
    Login personalizado que funciona con username o email
    """
    username_or_email = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    
    if not username_or_email or not password:
        return Response(
            {'error': 'Username/email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Intentar primero con username
    user = authenticate(username=username_or_email, password=password)
    
    # Si no funciona con username, intentar con email
    if not user and '@' in username_or_email:
        try:
            # Buscar usuario por email
            user_obj = User.objects.get(email=username_or_email)
            # Intentar autenticar con su username real
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
    
    if user and user.is_active:
        # Obtener o crear token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'country': user.country,
                'timezone': user.timezone,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'Invalid credentials or account is inactive'},
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def custom_logout(request):
    """
    Logout personalizado
    """
    if request.user.is_authenticated:
        # Eliminar token si existe
        Token.objects.filter(user=request.user).delete()
    
    return Response({'message': 'Logged out successfully'})        