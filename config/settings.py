import os
import secrets
from decimal import Decimal
from pathlib import Path

from config.paths import get_data_dir, get_resource_dir

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = get_data_dir()


def _load_or_create_secret_key(path: Path) -> str:
    if path.exists():
        return path.read_text().strip()
    key = secrets.token_urlsafe(64)
    path.write_text(key)
    return key


SECRET_KEY = _load_or_create_secret_key(DATA_DIR / "secret.key")
DEBUG = os.environ.get("COLEGIO_DEBUG") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.simple_history",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "simple_history",
    "colegio",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "colegio.middleware.ConfiguracionInicialMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "colegio.db",
        "OPTIONS": {
            "init_command": (
                "PRAGMA foreign_keys = ON;"
                "PRAGMA synchronous = FULL;"
                "PRAGMA busy_timeout = 5000;"
                "PRAGMA journal_mode = DELETE;"
            ),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Guatemala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = get_resource_dir() / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_AGE = 7200
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "admin:index"

UNIDADES_POR_CICLO = 4
NOTA_MIN = Decimal("0")
NOTA_MAX = Decimal("100")
NOTA_APROBACION = Decimal("60")

UNFOLD = {
    "SITE_TITLE": "Colegio Julio González Celis",
    "SITE_HEADER": "Colegio Julio González Celis",
    "SITE_LOGO": "colegio/escudo_colegio.png",
    "SITE_SYMBOL": "school",
}
