django-translating-package
==========================

1) Install from requirements
2) Start install_translator.sh

### Usage

Settings

    TRANSLATING_LANGS = [<langs>]

Models

    from django_translating_package import to_translation

    and decorate your model

App

    Override ready method

        def ready(self):
            ***
            register()
            ***

Makemigrations and migrate

For admin:
    
    from django_translating_package.admin import TranslateAdminInlines, setup_inlines

For adding inlines

    TranslateAdminInlines(Model, admin.TabularInline, exclude_langs=('it', 'en'), can_delete=False, show_change_link=True)

    you can specify inliner for choosed lang. custom class get same kwargs as default

    then better use setup_inlines, like setup_inlines(TranslateAdminInlines, TranslateAdminInlines)

    and set this result into inlines field of your admin.ModelAdmin subclass

For DRF

    from django_translating_package.serializer import TranslationModelSerializer

    inherit it. In Meta class use defaul fields + few special 
        class Meta:
            ***
            translations = ['en', 'fr']
            translations_fields = '__all__' - default __all__ except fk connected model
            translations_connect_exclude = False - default True

