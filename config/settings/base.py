"""
Base settings shared across environments.
"""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, ""),
    DJANGO_ALLOWED_HOSTS=(str, "*"),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-key-change-in-production-please-make-it-long")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # 3rd party
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_htmx",
    "django_celery_beat",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "django_extensions",
    "django_tables2",
    "formtools",

    # Local apps
    "apps.common",
    "apps.tenants",
    "apps.accounts",
    "apps.organizations",
    "apps.audit",
    "apps.integrations",
    "apps.tally_connector",
    "apps.zoho_connector",
    "apps.accounting_connectors",
    "apps.customers",
    "apps.receivables",
    "apps.payments",
    "apps.collections",
    "apps.reconciliation",
    "apps.communications",
    "apps.workflows",
    "apps.credit_management",
    "apps.analytics",
    "apps.customer_portal",
    "apps.field_sales",
    "apps.disputes",
    "apps.targets",
    "apps.documents",
    "apps.subscriptions",
    "apps.ai_assistant",
    "apps.notifications",
    "apps.administration",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.tenants.middleware.TenantMiddleware",
    "apps.audit.middleware.AuditMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.common.context_processors.global_settings",
                "apps.tenants.context_processors.tenant_context",
            ],
        },
    },
]

DATABASES = {
    "default": env.db_url("DATABASE_URL", default="sqlite:///payreceivio.db"),
}
# Force SQLite for dev if env value is the sandbox placeholder
if DATABASES["default"]["ENGINE"] == "file":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "payreceivio.db"),
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
elif DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3" and "/" not in DATABASES["default"]["NAME"]:
    DATABASES["default"]["NAME"] = str(BASE_DIR / DATABASES["default"]["NAME"])

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = env("DJANGO_LANGUAGE_CODE", default="en-in")
TIME_ZONE = env("DJANGO_TIME_ZONE", default="Asia/Kolkata")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# Crispy
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Email
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="PayReceivio <no-reply@payreceivio.com>")

# Security
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# OTP
OTP_TOTP_ISSUER = "PayReceivio"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "payreceivio.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "payreceivio": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
    },
}

# Application-specific
PAYRECEIVIO = {
    "COMPANY_NAME": "PayReceivio",
    "TAGLINE": "Universal Receivables & Payment Collection Platform",
    "CURRENCY": "INR",
    "CURRENCY_SYMBOL": "₹",
    "AGEING_BUCKETS": [
        ("current", "Current"),
        ("1-30", "1-30 days"),
        ("31-60", "31-60 days"),
        ("61-90", "61-90 days"),
        ("91-180", "91-180 days"),
        ("180+", "Above 180 days"),
    ],
    "REMINDER_SCHEDULE": [
        (-7, "Friendly payment reminder"),
        (-3, "Upcoming due notification"),
        (0, "Payment due message"),
        (3, "First overdue reminder"),
        (7, "Second reminder"),
        (15, "Escalation to salesperson"),
        (30, "Manager notification"),
        (60, "Credit review recommendation"),
    ],
}

# Tenant cookie
TENANT_SESSION_KEY = "payreceivio_tenant"
