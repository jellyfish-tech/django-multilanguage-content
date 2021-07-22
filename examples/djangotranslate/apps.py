from django.apps import AppConfig

from django_multilanguage_content import register


class DjangotranslateConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djangotranslate'

    def ready(self):
        register()
