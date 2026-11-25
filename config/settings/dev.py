"""Development settings."""
from .base import *  # noqa
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Easier to debug without eager celery
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)

# Email backend to console for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# django-debug-toolbar
try:
    import debug_toolbar  # noqa
    INSTALLED_APPS = list(INSTALLED_APPS) + ["debug_toolbar"]
    MIDDLEWARE = list(MIDDLEWARE) + ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass

# Disable whitenoise compression in dev for clearer errors
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
