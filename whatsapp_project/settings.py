"""
Django settings for whatsapp_project project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv()

# --- Security and Debugging ---

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production-xyz123')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# Dominio ngrok dinámico
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN")

# ALLOWED_HOSTS
ALLOWED_HOSTS = [
    'chatboot-1-s96f.onrender.com',
    'chatboot-mfv8.onrender.com',
    "127.0.0.1",
    "localhost",
]

if NGROK_DOMAIN:
    ALLOWED_HOSTS.append(NGROK_DOMAIN)

ALLOWED_HOSTS.append(".ngrok-free.app")

ENV_ALLOWED = os.getenv("ALLOWED_HOSTS")
if ENV_ALLOWED:
    ALLOWED_HOSTS.extend([h.strip() for h in ENV_ALLOWED.split(",") if h.strip()])


# --- Application definition ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chatbot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'whatsapp_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'whatsapp_project.wsgi.application'


# --- Database Configuration ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'u659323332_ebano_company'),
        'USER': os.getenv('DB_USER', 'u659323332_ebano_company'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Ebano123*'),
        'HOST': os.getenv('DB_HOST', '82.197.82.29'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Base de datos externa para consultas de elecciones estudiantiles
ELECTION_DB_ALIAS = 'elecciones'
DATABASES[ELECTION_DB_ALIAS] = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'u659323332_puestos',
    'USER': 'u659323332_puestos',
    'PASSWORD': 'Puestos123@',
    'HOST': '82.197.82.29',
    'PORT': '3306',
    'OPTIONS': {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4',
    },
}

# Mapeo de tabla/columnas de censo electoral
ELECTIONS_TABLE = os.getenv('ELECTIONS_TABLE', 'censo_electoral')
ELECTIONS_DOCUMENT_COLUMN = os.getenv('ELECTIONS_DOCUMENT_COLUMN', 'documento')
ELECTIONS_NAME_COLUMN = os.getenv('ELECTIONS_NAME_COLUMN', 'nombre')
ELECTIONS_POLLING_PLACE_COLUMN = os.getenv('ELECTIONS_POLLING_PLACE_COLUMN', 'puesto_votacion')
ELECTIONS_TABLE_NUMBER_COLUMN = os.getenv('ELECTIONS_TABLE_NUMBER_COLUMN', 'mesa')
ELECTIONS_ADDRESS_COLUMN = os.getenv('ELECTIONS_ADDRESS_COLUMN', 'direccion')
ELECTIONS_ZONE_COLUMN = os.getenv('ELECTIONS_ZONE_COLUMN', 'zona')


# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --- Internationalization ---
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# --- Static files ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login para inbox
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/chatbot/inbox/'


# --- WhatsApp Configuration ---
META_PHONE_NUMBER_ID = os.getenv('META_PHONE_NUMBER_ID', '')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN', '')
META_VERIFY_TOKEN = os.getenv('META_VERIFY_TOKEN', 'my_secure_verify_token')
META_WEBHOOK_SECRET = os.getenv('META_WEBHOOK_SECRET', '')

# --- Gemini Configuration ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCUni3L_9YtuWJkYe77Otcs-E4yTfUhrDs')

# --- Escalamiento a Humano ---
# Número de WhatsApp o CRM para escalar casos no resueltos
ESCALAMIENTO_WHATSAPP = os.getenv('ESCALAMIENTO_WHATSAPP', '')

# --- Logging Configuration ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'chatbot': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# --- CSRF Configuration ---
CSRF_TRUSTED_ORIGINS = []

if NGROK_DOMAIN and DEBUG:
    CSRF_TRUSTED_ORIGINS.append(f"https://{NGROK_DOMAIN}")
elif not DEBUG:
    CSRF_TRUSTED_ORIGINS = ['https://tu-dominio.com']
