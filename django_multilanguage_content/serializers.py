from collections import OrderedDict
from rest_framework.serializers import ModelSerializer
from .logic import langs


def translated_model_serializers_fabric(base_model, languages, translations_fields, translations_connect_exclude):
    new_fields = {}
    base_model_name = base_model.get_base_model_name()
    for lang in languages:
        connected_model_class = base_model.get_connected_translated_model_class(lang)
        connected_model_name = base_model.get_translate_model_name(lang)
        # Fabrica-like stuff to dynamically creating serializing
        new_serializer_meta_dict = {
            'model': connected_model_class
        }
        if translations_fields == '__all__' and translations_connect_exclude:
            new_serializer_meta_dict['exclude'] = [f'{base_model_name}_ptr']
        else:
            new_serializer_meta_dict['fields'] = translations_fields

        new_serializer = type(
            f'{connected_model_name}_serializer',
            (ModelSerializer,),
            {'Meta': type('Meta', (object,), new_serializer_meta_dict)}
        )
        new_fields[connected_model_name] = new_serializer(read_only=True)
    return new_fields


class TranslationModelSerializer(ModelSerializer):
    def get_fields(self):
        base_serializer_fields = super().get_fields()
        # get serializing languages
        translations = getattr(self.Meta, 'translations', langs)
        # get serializing fields for translated models
        translations_fields = getattr(self.Meta, 'translations_fields', '__all__')
        translations_connect_exclude = getattr(self.Meta, 'translations_connect_exclude', True)
        base_model = self.Meta.model
        new_fields = translated_model_serializers_fabric(
            # parent_serializer_fields=base_serializer_fields,
            base_model=base_model,
            languages=translations,
            translations_fields=translations_fields,
            translations_connect_exclude=translations_connect_exclude
        )
        base_serializer_fields = dict(base_serializer_fields)
        base_serializer_fields.update(new_fields)
        return OrderedDict(base_serializer_fields)
