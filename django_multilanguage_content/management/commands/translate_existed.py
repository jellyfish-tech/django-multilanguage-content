from django.core.management.base import BaseCommand
from django_multilanguage_content.store import models_store


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', "--app", type=str, default='')

    def handle(self, *args, **options):

        self.stdout.write(options.get('app'))
        print(models_store.translation_models_list)
        print(models_store.new_created_models_properties)
