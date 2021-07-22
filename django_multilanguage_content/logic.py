from operator import attrgetter
from types import MethodType
from typing import Dict, List, NoReturn, Tuple, Type, Union

from django.db.models import CASCADE, Field, Model, OneToOneField
from django.db.models.signals import post_save
from django.dispatch import receiver

from .store import models_store
from .translator import main_translator


def __cleanify_fields(fields_to_stay: tuple, model: Type[Model]) -> Dict[str, Type[Field]]:
    """Method check fields to be translated, make list of needed fields"""

    base_model_name = model.get_base_model_name()
    cleaned_base_fields = {}

    models_fields = model.get_base_model_fields()
    models_fields_names = set(map(lambda x: x.name, models_fields))
    if not set(fields_to_stay) <= models_fields_names:
        raise ValueError(f'{base_model_name} has incompatible field name to translation')

    for field in models_fields:
        if field.primary_key is not True and field.name in fields_to_stay:
            cleaned_base_fields[field.name] = field
    cleaned_base_fields[f'{base_model_name}_ptr'] = OneToOneField(model, on_delete=CASCADE)
    return cleaned_base_fields


def __follow_langs__create_models(model: Type[Model],
                                  langs_to_translate: Union[list, tuple],
                                  fields_to_stay: tuple) -> NoReturn:
    """Method actually creates new connected models"""

    for lang in langs_to_translate:
        translate_model_name = model.get_translate_model_name(lang)
        cleaned_fields = __cleanify_fields(fields_to_stay, model)
        translate_dict = {'__module__': model.__module__, **cleaned_fields}
        # creating happens here. Magic type() :)
        type(translate_model_name, (Model,), translate_dict)


def to_translation(*field_names: str, only_langs=None):
    """Decorator to mark model as translatable"""
    '''
    *field_names - "positional" field names
    FEAT:
        only_langs - list or tuple langs to be used for translation only
    '''
    def inner(model: Model) -> Type[Model]:

        def get_base_model_name(cls: Type[Model]) -> str:
            """ Class method
             :return str - model name
             """
            return cls._meta.model_name

        def get_base_model_fields(cls: Type[Model]) -> List[Type[Field]]:
            """ Class method
             :return list - list of model fields
             """
            return list(cls._meta.fields)

        def get_translate_model_name(cls: Type[Model], lang: str) -> str:
            """ Class method
             :return str - translated model name
             """
            return f'{cls.get_base_model_name()}_{lang}'

        def get_connected_translated_model_class(cls: Type[Model], lang: str) -> Type[Model]:
            """
            Class method. Returns connected translated model class according to chosen lang
            :return: connected model class
            """
            translated_model_getter = attrgetter(f'{cls.get_translate_model_name(lang)}.related.related_model')
            return translated_model_getter(cls)

        def get_all_connected_models(cls: Type[Model]) -> Dict[str, Type[Model]]:
            """Class method. Return dict of all connected models {name: model_class}"""
            all_connected_models = {}
            for lang in models_store.global_langs:
                try:
                    connected_model = cls.get_connected_translated_model_class(lang)
                    all_connected_models[connected_model.get_base_model_name()] = connected_model
                except AttributeError:
                    continue
            return all_connected_models

        # registration new class methods
        setattr(model, 'get_base_model_name', MethodType(get_base_model_name, model))
        setattr(model, 'get_base_model_fields', MethodType(get_base_model_fields, model))
        setattr(model, 'get_translate_model_name', MethodType(get_translate_model_name, model))
        setattr(model, 'get_connected_translated_model_class', MethodType(get_connected_translated_model_class, model))
        setattr(model, 'get_all_connected_models', MethodType(get_all_connected_models, model))

        models_store.translation_models_list = model

        followed_langs = models_store.global_langs
        if isinstance(only_langs, (list, tuple)):
            for lang in only_langs:
                if lang not in followed_langs:
                    raise ValueError(f'Language {lang}, to be followed by {model.get_base_model_name()} model,'
                                     f' is not in global languages list')
            followed_langs = only_langs
        fields_to_stay = (*field_names,)
        if not len(fields_to_stay):
            fields_to_stay = tuple(map(lambda x: x.name, model.get_base_model_fields()))
        __follow_langs__create_models(model, followed_langs, fields_to_stay)

        models_store.new_created_models_properties = {model.get_base_model_name(): fields_to_stay}

        return model
    return inner


def set_util_instance_methods():
    """Private decorator. Adds additional functionality to model instance """
    def decor(func):
        def wrapper(sender, instance, **kwargs):
            """ Adds instance methods """

            if isinstance(instance, models_store.translation_models_list):
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

                def get_fields_and_pk(self) -> Tuple[List[Type[Field]], Type[Field]]:
                    """Instance level method"""
                    '''
                    :return tuple[instance fields list, instance pk field]
                    '''
                    fields = self.get_base_model_fields()  # base fields
                    # to stay fields
                    fields_to_stay = models_store.new_created_models_properties[sender.get_base_model_name()]

                    pk_field = list(filter(lambda x: x.primary_key is True, fields))[0]
                    fields.remove(pk_field)
                    # if fields to stay list is empty - all by default
                    if len(fields_to_stay):
                        fields = filter(lambda x: x.name in fields_to_stay, fields)
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

            func(sender, instance, **kwargs)
        return wrapper
    return decor


def preparing_content(instance) -> Tuple[List[str], List[str]]:
    """Function to prepare content for translation"""
    # already filtered fields
    fields, pk = instance.get_fields_and_pk()
    # get values from base model for translation
    object_to_translate = {field.name: field.value_from_object(instance) for field in fields}
    obj_keys, obj_vals = list(zip(*object_to_translate.items()))  # unzip dict items | [tuple_keys, tuple_values]
    return obj_keys, obj_vals


def do_translation(instance, lang, field_names, field_values):
    """Function that evaluate translation process"""
    translated = main_translator(field_values, lang)
    data = dict(zip(field_names, translated))
    data[f'{instance.get_base_model_name()}_ptr'] = instance
    instance.translate_connected(lang, data)


def register():
    @receiver(post_save, weak=False)
    @set_util_instance_methods()
    def translate_to_connected_tables(sender, instance, **kwargs):
        if kwargs.get('created', False):
            if sender in models_store.translation_models_list:
                field_names, field_values = preparing_content(instance)
                for lang in models_store.global_langs:
                    # # TODO too slow. threading mb
                    do_translation(instance, lang, field_names, field_values)
