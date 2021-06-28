import typing
from operator import attrgetter
from types import MethodType
from django.conf import settings
from django.db.models import CASCADE, Field, Model, OneToOneField
from django.db.models.signals import post_save
from django.dispatch import receiver
from .translator import translate

global_langs = tuple(lang.lower() for lang in settings.TRANSLATING_LANGS)
translation_models_list = []

new_created_models = {}


def to_translation(model: Model) -> typing.Type[Model]:
    """
    Decorator, using for mark the model as translatable. Also creating connected to this model, models according to
     languages for translation
    :param model:
    :return: model
    """

    def get_base_model_name(cls: typing.Type[Model]) -> str:
        """ Class method
         :return str - model name
         """
        return cls._meta.model_name

    def get_base_model_fields(cls: typing.Type[Model]) -> typing.List[typing.Type[Field]]:
        """ Class method
         :return list - list of model fields
         """
        return list(cls._meta.fields)

    def get_translate_model_name(cls: typing.Type[Model], lang: str) -> str:
        """ Class method
        :param lang - translated language name
         :return str - translated model name
         """
        return f'{cls.get_base_model_name()}_{lang}'

    def get_connected_translated_model_class(cls: typing.Type[Model], lang: str) -> typing.Type[Model]:
        """
        Class method. return connected translated models according to chosen lang
        :param cls:
        :param lang:
        :return: connected model
        """
        translated_model_getter = attrgetter(f'{cls.get_translate_model_name(lang)}.related.related_model')
        return translated_model_getter(cls)

    def get_all_connected_models(cls):
        all_connected_models = {}
        for lang in global_langs:
            try:
                connected_model = cls.get_connected_translated_model_class(lang)
                all_connected_models[connected_model._meta.model_name] = connected_model
            except AttributeError:
                continue
        return all_connected_models

    # registration new class methods
    setattr(model, 'get_base_model_name', MethodType(get_base_model_name, model))
    setattr(model, 'get_base_model_fields', MethodType(get_base_model_fields, model))
    setattr(model, 'get_translate_model_name', MethodType(get_translate_model_name, model))
    setattr(model, 'get_connected_translated_model_class', MethodType(get_connected_translated_model_class, model))
    setattr(model, 'get_all_connected_models', MethodType(get_all_connected_models, model))

    translation_models_list.append(model)  # adding models to translation to list
    base_model_name = model.get_base_model_name()
    for lang in global_langs:
        translate_model_name = model.get_translate_model_name(lang)
        # recreating translating model with the same fields except primary key
        base_fields = {field.name: field for field in model.get_base_model_fields() if field.primary_key is not True}
        # adding translating model relation to base model
        base_fields[f'{base_model_name}_ptr'] = OneToOneField(model, on_delete=CASCADE)
        # simulating module attribute in translating model, and adding fields
        translate_dict = {'__module__': model.__module__, **base_fields}
        # creating translating model in memory. it saves as relation into base model
        saving_new_model = {translate_model_name: type(translate_model_name, (Model,), translate_dict)}

    return model


def __set_util_funcs():
    """Private decorator. Adds additional functionality to model instance """
    def decor(func):
        def wrapper(sender, instance, update_fields, **kwargs):
            """ Adds instance level functions """

            if isinstance(instance, tuple(translation_models_list)):
                model = instance

                def translate_connected(self, lang: str, data: dict):
                    """ Instance level method."""
                    '''
                    :param lang - precise language
                    :param data - data
                    '''
                    '''Consider, create new or update existence record'''
                    if hasattr(self, self.get_translate_model_name(lang)):
                        self._update_connected(lang, data)
                    else:
                        self._create_connected(lang, data)

                def _create_connected(self, lang: str, data: dict):
                    """Create new record"""
                    this_lang_connected_model = getattr(self, self.get_translate_model_name(lang), None)
                    assert this_lang_connected_model is None
                    model_for_translating = self.get_connected_translated_model_class(lang)
                    model_for_translating.objects.create(**data)

                def _update_connected(self, lang: str, data: dict):
                    """Update existence record"""
                    this_lang_connected_model = getattr(self, self.get_translate_model_name(lang), None)
                    assert this_lang_connected_model is not None
                    for key in data:
                        setattr(this_lang_connected_model, key, data[key])
                    this_lang_connected_model.save()

                def get_fields_and_pk(self) -> typing.Tuple[typing.List[typing.Type[Field]], typing.Type[Field]]:
                    """Instance level method"""
                    '''
                    :return tuple[instance fields list, instance pk field]
                    '''
                    fields = self.get_base_model_fields()
                    pk_field = list(filter(lambda x: x.primary_key is True, fields))[0]
                    fields.remove(pk_field)
                    return fields, pk_field

                def get_connected_translated_model_instance(self, lang: str):
                    """Instance level method"""
                    ''':param lang - language from translated languages list'''
                    '''Method returns instance of connected translated model according to language'''
                    return attrgetter(f'{self.get_translate_model_name(lang)}')(self)

                setattr(model, '_create_connected', MethodType(_create_connected, model))
                setattr(model, '_update_connected', MethodType(_update_connected, model))
                setattr(model, 'translate_connected', MethodType(translate_connected, model))
                setattr(model, 'get_fields_and_pk', MethodType(get_fields_and_pk, model))
                setattr(model, 'get_connected_translated_model_instance',
                        MethodType(get_connected_translated_model_instance, model)
                        )

            func(sender, instance, update_fields, **kwargs)
        return wrapper
    return decor


def register():

    @receiver(post_save)
    @__set_util_funcs()
    def translate_to_connected_tables(sender, instance, update_fields, **kwargs):
        if kwargs.get('created', False):
            if sender in translation_models_list:
                fields, pk = instance.get_fields_and_pk()
                # get values from base model for translation
                object_to_translate = {field.name: field.value_from_object(instance) for field in fields}
                obj_keys, obj_vals = list(zip(*object_to_translate.items()))  # unzip dict items | [tuple_keys, tuple_values]
                base_model_name = instance.get_base_model_name()
                for lang in global_langs:
                    # TODO too slow. threading mb
                    translated = translate(obj_vals, lang)
                    data = {
                        field: value.text for field, value in zip(obj_keys, translated)
                    }
                    data[f'{base_model_name}_ptr'] = instance
                    instance.translate_connected(lang, data)
