import os
from pathlib import Path

from config import django_app_key, SMTP_PASS

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = django_app_key

DEBUG = True

ALLOWED_HOSTS = [
    'bravo.almazor.co',
    'delta.almazor.co',
    'localhost',
    '209.38.180.77',
    '164.92.182.43',
    '127.0.0.1',
    '165.227.142.240',
    '139.59.206.100',
]

CORS_ALLOWED_ORIGINS = [
    "https://bravo.almazor.co",
    "https://209.38.180.77",
    "https://delta.almazor.co",
    "https://139.59.206.100",
    # Другие доверенные источники здесь
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.bravo.almazor.co',
    'https://*.209.38.180.77',
    'https://*.127.0.0.1',
    'https://*.139.59.206.100',
    'https://*.delta.almazor.co',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_q',

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

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
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

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'support@almazor.co'
EMAIL_HOST_PASSWORD = SMTP_PASS
DEFAULT_FROM_EMAIL = 'support@almazor.co'


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


Q_CLUSTER = {
    'name': 'DjangoQ',
    'workers': 1,
    'recycle': 500,
    'timeout': 60,
    'ack_failures': True,
    'max_attempts': 3,
    'retry': 60,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',  # Use Django ORM
    'sync': False,
    'save_limit': 250,
    'poll': 1,
    'log_level': 'DEBUG',  # Set to DEBUG for more detailed logs
    'log_file': 'django_q.log',  # Log file path
}


LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
