import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# 1. Definições de Caminho (Essencial para o Django se localizar)
BASE_DIR = Path(__file__).resolve().parent.parent

# Procura o .env na raiz do projeto
load_dotenv(find_dotenv())

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-chave-temporaria-para-dev')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*'] 

# Autoriza o Easypanel a enviar formulários via HTTPS
CSRF_TRUSTED_ORIGINS = ['https://*.samuraisdoocidente.com.br', 'https://*.seu-dominio.com.br']

# 3. Definição do App e Middleware
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core', # Seu app
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

ROOT_URLCONF = 'projeto.urls'

# 4. Motor de Templates (Resolve o erro admin.E403)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'projeto.wsgi.application'

# 5. Banco de Dados
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# 6. Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# 7. Arquivos Estáticos e Mídia (Fotos dos Lutadores)
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 8. Tipo de ID padrão (Resolve os avisos amarelos W042)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Proxy Settings (Obrigatório para o Easypanel)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Static Files (Onde o Whitenoise vai juntar o CSS)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Força o Django a usar o motor do Whitenoise para entregar o CSS em produção
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Configurações de Login/Logout
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'perfil'
LOGOUT_REDIRECT_URL = 'home'