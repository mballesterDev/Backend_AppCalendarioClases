from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Alumno'),
        ('teacher', 'Profesor'),
    ]

    COUNTRY_CHOICES = [
        # América del Norte
        ('US', 'United States'),
        ('CA', 'Canada'),
        ('MX', 'Mexico'),
        
        # América Central
        ('CR', 'Costa Rica'),
        ('PA', 'Panama'),
        ('GT', 'Guatemala'),
        ('HN', 'Honduras'),
        ('SV', 'El Salvador'),
        ('NI', 'Nicaragua'),
        
        # Caribe
        ('DO', 'Dominican Republic'),
        ('PR', 'Puerto Rico'),
        
        # América del Sur
        ('BR', 'Brazil'),
        ('AR', 'Argentina'),
        ('CL', 'Chile'),
        ('CO', 'Colombia'),
        ('PE', 'Peru'),
        ('VE', 'Venezuela'),
        ('UY', 'Uruguay'),
        ('PY', 'Paraguay'),
        ('BO', 'Bolivia'),
        ('EC', 'Ecuador'),
        
        # Europa Occidental
        ('ES', 'Spain'),
        ('UK', 'United Kingdom'),
        ('IE', 'Ireland'),
        ('FR', 'France'),
        ('DE', 'Germany'),
        ('IT', 'Italy'),
        ('NL', 'Netherlands'),
        ('BE', 'Belgium'),
        ('LU', 'Luxembourg'),
        ('CH', 'Switzerland'),
        ('AT', 'Austria'),
        ('PT', 'Portugal'),
        
        # Europa del Norte
        ('SE', 'Sweden'),
        ('NO', 'Norway'),
        ('DK', 'Denmark'),
        ('FI', 'Finland'),
        ('IS', 'Iceland'),
        
        # Europa del Este
        ('PL', 'Poland'),
        ('CZ', 'Czech Republic'),
        ('HU', 'Hungary'),
        ('RO', 'Romania'),
        ('BG', 'Bulgaria'),
        ('RU', 'Russia'),
        ('UA', 'Ukraine'),
        ('EE', 'Estonia'),
        ('LV', 'Latvia'),
        ('LT', 'Lithuania'),
        ('SK', 'Slovakia'),
        ('SI', 'Slovenia'),
        ('HR', 'Croatia'),
        
        # Europa del Sur
        ('GR', 'Greece'),
        ('TR', 'Turkey'),
        
        # Asia Oriental
        ('CN', 'China'),
        ('JP', 'Japan'),
        ('KR', 'South Korea'),
        ('HK', 'Hong Kong'),
        ('TW', 'Taiwan'),
        
        # Sudeste Asiático
        ('SG', 'Singapore'),
        ('MY', 'Malaysia'),
        ('TH', 'Thailand'),
        ('VN', 'Vietnam'),
        ('PH', 'Philippines'),
        ('ID', 'Indonesia'),
        
        # Sur de Asia
        ('IN', 'India'),
        
        # Medio Oriente
        ('AE', 'United Arab Emirates'),
        ('SA', 'Saudi Arabia'),
        ('IL', 'Israel'),
        ('QA', 'Qatar'),
        ('KW', 'Kuwait'),
        
        # Asia Central
        ('KZ', 'Kazakhstan'),
        
        # África del Norte
        ('MA', 'Morocco'),
        ('EG', 'Egypt'),
        ('DZ', 'Algeria'),
        ('TN', 'Tunisia'),
        
        # África Occidental
        ('NG', 'Nigeria'),
        ('GH', 'Ghana'),
        
        # África Oriental
        ('KE', 'Kenya'),
        ('ET', 'Ethiopia'),
        
        # África del Sur
        ('ZA', 'South Africa'),
        
        # Oceanía
        ('AU', 'Australia'),
        ('NZ', 'New Zealand'),
    ]

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
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='ES')
    timezone = models.CharField(max_length=50, default='UTC')

    # ✅ CAMPOS DE SALDO ACTUALIZADOS A 25/50/80
    saldo_clases_25min = models.IntegerField(default=0)
    saldo_clases_50min = models.IntegerField(default=0)
    saldo_clases_80min = models.IntegerField(default=0)
  
    def saldo_total(self, duracion=None):
        """
        Devuelve el saldo de clases disponibles.
        """
        if duracion == 25:
            return self.saldo_clases_25min
        elif duracion == 50:
            return self.saldo_clases_50min
        elif duracion == 80:
            return self.saldo_clases_80min
        else:
            return {
                '25min': self.saldo_clases_25min,
                '50min': self.saldo_clases_50min,
                '80min': self.saldo_clases_80min,
                'total': self.saldo_clases_25min + self.saldo_clases_50min + self.saldo_clases_80min
            }
    
    def comprar_clase(self, duracion, cantidad=1):
        """
        Añadir clases al saldo del usuario.
        """
        if duracion == 25:
            self.saldo_clases_25min += cantidad
        elif duracion == 50:
            self.saldo_clases_50min += cantidad
        elif duracion == 80:
            self.saldo_clases_80min += cantidad
        else:
            raise ValueError("Duración debe ser 25, 50 u 80 minutos")
        self.save()
    
    def usar_clase(self, duracion):
        """
        Descontar una clase del saldo.
        Devuelve True si pudo usar la clase, False si no tenía saldo.
        """
        if duracion == 25 and self.saldo_clases_25min > 0:
            self.saldo_clases_25min -= 1
            self.save()
            return True
        elif duracion == 50 and self.saldo_clases_50min > 0:
            self.saldo_clases_50min -= 1
            self.save()
            return True
        elif duracion == 80 and self.saldo_clases_80min > 0:
            self.saldo_clases_80min -= 1
            self.save()
            return True
        return False

    def devolver_clase(self, duracion):
        """
        Devolver una clase al saldo (para cancelaciones).
        """
        if duracion == 25:
            self.saldo_clases_25min += 1
        elif duracion == 50:
            self.saldo_clases_50min += 1
        elif duracion == 80:
            self.saldo_clases_80min += 1
        self.save()

    def save(self, *args, **kwargs):
        self.timezone = self.COUNTRY_TIMEZONES.get(self.country, 'UTC')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()} - {self.get_country_display()})"