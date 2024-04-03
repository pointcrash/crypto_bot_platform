import os
from pathlib import Path

from config import django_app_key

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = django_app_key

DEBUG = True

ALLOWED_HOSTS = ['bravo.almazor.co', 'localhost', '209.38.180.77', '164.92.182.43', '127.0.0.1']

CORS_ALLOWED_ORIGINS = [
    "https://bravo.almazor.co",
    "https://209.38.180.77",
    # Другие доверенные источники здесь
]

CSRF_TRUSTED_ORIGINS = ['https://*.bravo.almazor.co', 'https://*.209.38.180.77', 'https://*.127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'orders',
    'main',
    'bots',
    'bots_group',
    'single_bot',
    'tg_bot',
    'timezone',
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

ROOT_URLCONF = 'traider_bot.urls'

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

WSGI_APPLICATION = 'traider_bot.wsgi.application'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'BTC_USDT_bot_db',
#         'USER': 'admin',
#         'PASSWORD': '74976',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'MyDB',
        'USER': 'admin',
        'PASSWORD': 'lksd23GBKwed.',
        'HOST': 'db',
        'PORT': '5432',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console_simple': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_verbose': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_simple': {
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'simple',
        },
        'file_verbose': {
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console_simple', 'file_verbose'],
            'level': 'INFO',
            'propagate': True,
        },
        'debug_logger': {
            'handlers': ['console_simple', 'file_verbose'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

LOGIN_URL = "/login/"

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

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
