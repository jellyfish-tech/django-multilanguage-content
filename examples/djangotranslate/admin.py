from django.contrib import admin

from django_multilanguage_content.admin import (TranslateAdminInlines,
                                                setup_inlines)

from .models import Simple

inlines = setup_inlines(
    TranslateAdminInlines(Simple,
                          admin.TabularInline,
                          exclude_langs=('it', 'en'),
                          can_delete=False,
                          show_change_link=True),
    TranslateAdminInlines(Simple,
                          admin.StackedInline,
                          exclude_langs=('fr',))
)


class SimpleAdmin(admin.ModelAdmin):
    inlines = inlines


admin.site.register(Simple, SimpleAdmin)
