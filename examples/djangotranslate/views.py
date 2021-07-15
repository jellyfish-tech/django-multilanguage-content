from .models import Simple
from django_multilanguage_content.serializers import TranslationModelSerializer
from django_multilanguage_content.views import TranslationViewSet


class SimpleSerializer(TranslationModelSerializer):

    class Meta:
        model = Simple
        fields = '__all__'
        translations = ['en', 'fr']
        # translations_fields = '__all__'
        # translations_connect_exclude = False


class SimpleSet(TranslationViewSet):
    serializer_class = SimpleSerializer
    queryset = Simple.objects.all()
