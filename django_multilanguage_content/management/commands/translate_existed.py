from django.apps.registry import apps
from django.core.management.base import BaseCommand

from django_multilanguage_content.logic import (do_translation,
                                                preparing_content,
                                                set_util_instance_methods)
from django_multilanguage_content.store import models_store


@set_util_instance_methods()
def cli_translation(model, instance, lang='', **kwargs):
    field_names, field_values = preparing_content(instance)
    do_translation(instance, lang, field_names, field_values)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', "--app", type=str, default='')

    def handle(self, *args, **options):
        app_name = options.get('app')
        models = models_store.translation_models_list
        if app_name:
            # Filtering by apps
            app_config = apps.get_app_config(app_name)
            app_models = list(app_config.get_models())
            models = tuple(model for model in app_models if model in models_store.translation_models_list)

        # TODO mb threading
        for model in models:
            instances = model.objects.all()
            for instance in instances:
                for lang in models_store.global_langs:
                    if not hasattr(instance, instance.get_translate_model_name(lang)):
                        cli_translation(model, instance, lang=lang)
