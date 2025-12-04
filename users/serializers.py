from django.db import IntegrityError
from rest_framework import serializers
from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model
from .models import CustomUser
from clases.models import Clase


User = get_user_model()

# Mapeo completo de países a timezones
COUNTRY_TIMEZONES = {
    'US': 'America/New_York',
    'ES': 'Europe/Madrid',
    'CA': 'America/Toronto',
    'BR': 'America/Sao_Paulo',
    'MX': 'America/Mexico_City',
    'AR': 'America/Argentina/Buenos_Aires',
    'CL': 'America/Santiago',
    'CO': 'America/Bogota',
    'PE': 'America/Lima',
    'VE': 'America/Caracas',
    'UY': 'America/Montevideo',
    'PY': 'America/Asuncion',
    'BO': 'America/La_Paz',
    'EC': 'America/Guayaquil',
    'CR': 'America/Costa_Rica',
    'PA': 'America/Panama',
    'DO': 'America/Santo_Domingo',
    'PR': 'America/Puerto_Rico',
    'GT': 'America/Guatemala',
    'HN': 'America/Tegucigalpa',
    'SV': 'America/El_Salvador',
    'NI': 'America/Managua',
    'UK': 'Europe/London',
    'IE': 'Europe/Dublin',
    'FR': 'Europe/Paris',
    'DE': 'Europe/Berlin',
    'IT': 'Europe/Rome',
    'NL': 'Europe/Amsterdam',
    'BE': 'Europe/Brussels',
    'LU': 'Europe/Luxembourg',
    'CH': 'Europe/Zurich',
    'AT': 'Europe/Vienna',
    'PL': 'Europe/Warsaw',
    'CZ': 'Europe/Prague',
    'HU': 'Europe/Budapest',
    'RO': 'Europe/Bucharest',
    'BG': 'Europe/Sofia',
    'SE': 'Europe/Stockholm',
    'NO': 'Europe/Oslo',
    'DK': 'Europe/Copenhagen',
    'FI': 'Europe/Helsinki',
    'IS': 'Atlantic/Reykjavik',
    'PT': 'Europe/Lisbon',
    'GR': 'Europe/Athens',
    'TR': 'Europe/Istanbul',
    'RU': 'Europe/Moscow',
    'UA': 'Europe/Kiev',
    'EE': 'Europe/Tallinn',
    'LV': 'Europe/Riga',
    'LT': 'Europe/Vilnius',
    'SK': 'Europe/Bratislava',
    'SI': 'Europe/Ljubljana',
    'HR': 'Europe/Zagreb',
    'CN': 'Asia/Shanghai',
    'JP': 'Asia/Tokyo',
    'KR': 'Asia/Seoul',
    'IN': 'Asia/Kolkata',
    'SG': 'Asia/Singapore',
    'MY': 'Asia/Kuala_Lumpur',
    'TH': 'Asia/Bangkok',
    'VN': 'Asia/Ho_Chi_Minh',
    'PH': 'Asia/Manila',
    'HK': 'Asia/Hong_Kong',
    'ID': 'Asia/Jakarta',
    'AE': 'Asia/Dubai',
    'SA': 'Asia/Riyadh',
    'IL': 'Asia/Jerusalem',
    'QA': 'Asia/Qatar',
    'KW': 'Asia/Kuwait',
    'KZ': 'Asia/Almaty',
    'ZA': 'Africa/Johannesburg',
    'MA': 'Africa/Casablanca',
    'EG': 'Africa/Cairo',
    'NG': 'Africa/Lagos',
    'KE': 'Africa/Nairobi',
    'GH': 'Africa/Accra',
    'DZ': 'Africa/Algiers',
    'TN': 'Africa/Tunis',
    'ET': 'Africa/Addis_Ababa',
    'AU': 'Australia/Sydney',
    'NZ': 'Pacific/Auckland',
}

# -----------------------------------
# Registro de usuarios
# -----------------------------------
class CustomRegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role', 'country']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'role': {'required': True},
            'country': {'required': True}
        }

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return email

    def validate_username(self, username):
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Este username ya está registrado.")
        return username

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):
        # Extraer contraseñas
        password = validated_data.pop('password1')
        validated_data.pop('password2')  # No lo necesitamos
        
        # Crear usuario
        user = CustomUser(**validated_data)
        
        # Asignar timezone automáticamente según el país
        user.timezone = COUNTRY_TIMEZONES.get(user.country, 'UTC')
        
        # Establecer contraseña
        user.set_password(password)
        
        try:
            user.save()
            return user
        except IntegrityError as e:
            if 'email' in str(e).lower():
                raise serializers.ValidationError({"email": ["Este email ya está registrado."]})
            if 'username' in str(e).lower():
                raise serializers.ValidationError({"username": ["Este username ya está registrado."]})
            raise serializers.ValidationError({"non_field_errors": ["Error al guardar el usuario."]})

# -----------------------------------
# Serializer para ver usuarios
# -----------------------------------
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"


# -----------------------------------
# Serializer de suscripción
# -----------------------------------
class SubscriptionSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
    premium_until = serializers.DateTimeField(allow_null=True)

# Serializer para comprar clases
class ComprarClaseSerializer(serializers.Serializer):
    duracion_minutos = serializers.IntegerField()
    
    def validate_duracion_minutos(self, value):
        if value not in [25, 50, 80]:
            raise serializers.ValidationError("La duración debe ser 25, 50 u 80 minutos")
        return value

# UserSimpleSerializer
class UserSimpleSerializer(serializers.ModelSerializer):
    saldo_clases = serializers.SerializerMethodField()
    country_name = serializers.CharField(source='get_country_display', read_only=True)
    role_name = serializers.CharField(source='get_role_display', read_only=True)
    
    saldo_25_min = serializers.IntegerField(source='saldo_clases_25min', read_only=True)
    saldo_50_min = serializers.IntegerField(source='saldo_clases_50min', read_only=True)
    saldo_80_min = serializers.IntegerField(source='saldo_clases_80min', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 
            'role', 'role_name', 'country', 'country_name', 'timezone',
            'saldo_clases', 'saldo_25_min', 'saldo_50_min', 'saldo_80_min'
        ]

    def get_saldo_clases(self, obj):
        return obj.saldo_total()

# Serializer para perfil de usuario completo
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil completo del usuario incluyendo todos los saldos"""
    country_name = serializers.CharField(source='get_country_display', read_only=True)
    role_name = serializers.CharField(source='get_role_display', read_only=True)
    
    saldo_25_min = serializers.IntegerField(source='saldo_clases_25min', read_only=True)
    saldo_50_min = serializers.IntegerField(source='saldo_clases_50min', read_only=True)
    saldo_80_min = serializers.IntegerField(source='saldo_clases_80min', read_only=True)
    
    # Información de saldo total
    saldo_total = serializers.SerializerMethodField()
    clases_compradas = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_name', 'country', 'country_name', 'timezone',
            'date_joined', 'last_login', 'is_active',
            'saldo_25_min', 'saldo_50_min', 'saldo_80_min',
            'saldo_total', 'clases_compradas'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def get_saldo_total(self, obj):
        """Total de todas las clases disponibles"""
        return {
            '25min': obj.saldo_clases_25min,
            '50min': obj.saldo_clases_50min,
            '80min': obj.saldo_clases_80min,
            'total_clases': obj.saldo_clases_25min + obj.saldo_clases_50min + obj.saldo_clases_80min
        }

    def get_clases_compradas(self, obj):
        """Información de clases compradas"""
        return {
            'total_compradas': obj.saldo_clases_25min + obj.saldo_clases_50min + obj.saldo_clases_80min,
            'detalle': {
                '25min': obj.saldo_clases_25min,
                '50min': obj.saldo_clases_50min,
                '80min': obj.saldo_clases_80min
            }
        }

# Serializer para actualizar perfil
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'country', 'timezone']
    
    def update(self, instance, validated_data):
        # Si cambia el país, actualizar automáticamente la timezone
        if 'country' in validated_data:
            country = validated_data['country']
            validated_data['timezone'] = COUNTRY_TIMEZONES.get(country, 'UTC')
        
        return super().update(instance, validated_data)

# Serializer para recargar saldo
class RecargarSaldoSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    duracion_minutos = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1, max_value=100)
    
    def validate_duracion_minutos(self, value):
        if value not in [25, 50, 80]:
            raise serializers.ValidationError("La duración debe ser 25, 50 u 80 minutos")
        return value
    
    def validate(self, data):
        try:
            user = CustomUser.objects.get(id=data['user_id'])
            data['user'] = user
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"user_id": "Usuario no encontrado"})
        return data