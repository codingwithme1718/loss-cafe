import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)1_8$l1(6*)!&p9=e2&=7r1c89#idvahly+664j3f**u+%3e40'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["24.199.126.247", "losscafe.com.tr", "www.losscafe.com.tr"]


# Application definition

JAZZMIN_SETTINGS = {
    "site_title": "My Cafe Admin",
    "site_header": "Cafe Management",
    "welcome_sign": "Welcome to the Cafe Admin",
    "search_model": "auth.User",
    # Add more customizations as needed
}

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # other apps
    'cafe',
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

ROOT_URLCONF = 'loss_cafe.urls'

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
        }
    }
]

WSGI_APPLICATION = 'loss_cafe.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
'''
# import dj_database_url

# DATABASES = {
#    'default': dj_database_url.config(conn_max_age=600)
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'losscafe_db'),
        'USER': os.getenv('DATABASE_USER', 'losscafe_user'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'losscafe_pass'),
        'HOST': os.getenv('DATABASE_HOST', 'db'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/root/loss-cafe/media'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # This should point to /root/loss-cafe/media

# STATIC_URL = '/static/'

# STATIC_ROOT = BASE_DIR / 'staticfiles'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')


SESSION_COOKIE_SECURE = True  # Use secure cookies
CSRF_COOKIE_SECURE = True  # Use secure CSRF cookies
SECURE_SSL_REDIRECT = False
CSRF_TRUSTED_ORIGINS = ['https://losscafe.com.tr', 'https://www.losscafe.com.tr']
