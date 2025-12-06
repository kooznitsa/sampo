from dotenv import load_dotenv
import environ

from .base import *  # noqa

load_dotenv(BASE_DIR / 'env' / '.env.prod')  # noqa
env = environ.Env()

ENV = env.str('ENV')
VERSION = env.str('VERSION')
APP_NAME = env.str('APP_NAME')
SECRET_KEY = env.str('SECRET_KEY')
DEBUG = env.bool('DEBUG')
ALLOWED_HOSTS = env.list('URLS')
TIME_ZONE = env.str('TZ')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env.str('POSTGRES_DB'),
        'USER': env.str('POSTGRES_USER'),
        'PASSWORD': env.str('POSTGRES_PASSWORD'),
        'HOST': env.str('POSTGRES_HOST'),
        'PORT': env.str('POSTGRES_PORT'),
        'OPTIONS': {
            'sslmode': env.str('DATABASE_SSLMODE', default='disable'),
        },
    }
}


# SECURITY

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

CSRF_TRUSTED_ORIGINS = [
    f'http://{env.str("IP_ADDRESS")}',
    f'http://{env.str("IP_ADDRESS")}:1337',
]


# EMAILS

ADMIN_EMAILS = [('', email) for email in env.str('ADMINS').split(',')]
ADMINS = ADMIN_EMAILS
MANAGERS = ADMIN_EMAILS
