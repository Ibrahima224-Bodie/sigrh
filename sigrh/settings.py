"""
Django settings for sigrh project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-p7*ocm@2ovp)@a4o5xev9ur4q6z3*p6zt%d*vr!!5n3sywpbdi'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.comptes',
    'django.contrib.auth',
    'django.contrib.admin',
    'apps.agents',
    'apps.directions',
    'apps.carrieres',
    'apps.absences',
    'apps.formations',
    'apps.organigramme',
    'apps.dashboard',
    'apps.assistant_ia',
    'apps.enseignants',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sigrh',
        'USER': 'postgres',
        'PASSWORD': '6875',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

AUTH_USER_MODEL = "comptes.User"

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

SILENCED_SYSTEM_CHECKS = [
    'admin.E402',
]

# Authentication settings
LOGIN_URL = 'login'  # Redirect to login page when authentication is required
LOGIN_REDIRECT_URL = 'dashboard'  # Redirect after successful login

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Casablanca'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Chatbot IA (optionnel):
# - Definir OPENAI_API_KEY dans les variables d'environnement pour activer l'IA distante.
# - Sans cle API, le chatbot fonctionne en mode local base sur les donnees SIGRH.
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
SIGRH_CHATBOT_MODEL = os.getenv('SIGRH_CHATBOT_MODEL', 'gpt-4o-mini')
SIGRH_CHATBOT_ENABLE_REMOTE = os.getenv('SIGRH_CHATBOT_ENABLE_REMOTE', '1') == '1'