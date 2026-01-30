from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-#your-secret-key-here#'

DEBUG = False
# 生产域名与IP
ALLOWED_HOSTS = [
    'www.aiphysophil.tech',
    'aiphysophil.tech',
    '119.45.252.190'
]
CSRF_TRUSTED_ORIGINS = [
    'http://www.aiphysophil.tech',
    'https://www.aiphysophil.tech',
    'http://aiphysophil.tech',
    'https://aiphysophil.tech'
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 第三方库
    'rest_framework',
    'corsheaders',
    'django_filters',
    
    # 你的应用
    'core', 
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'zmg_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'zmg_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# 告诉 Django 除了各 App 内部的 static，还要去根目录的 static 文件夹找文件
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# 生产环境使用的静态文件根目录（执行 collectstatic 时使用）
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 允许跨域
CORS_ALLOW_ALL_ORIGINS = True

AUTH_USER_MODEL = 'core.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# =================================================
# 👇 核心修复：局域网 HTTP 开发安全策略松绑 👇
# =================================================

# 1. 允许 iframe 嵌入 (解决 "192.168.x.x 拒绝了我们的连接请求")
X_FRAME_OPTIONS = 'ALLOWALL'

# 2. 禁用 COOP 策略头 (解决 "Cross-Origin-Opener-Policy header has been ignored")
# 浏览器在非 HTTPS 下会强制忽略此头并报错，所以我们直接禁用它
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# 3. 禁用 SSL 重定向 (防止在局域网 IP 访问时跳到 HTTPS 导致无法连接)
SECURE_SSL_REDIRECT = False

# 4. 允许的 HTTP 方法
XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']