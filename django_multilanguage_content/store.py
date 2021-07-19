from dataclasses import dataclass, field
from functools import cached_property
from typing import Dict, List, Set, Tuple, Type

from django.conf import settings
from django.db.models import Model


@dataclass
class TranslationModelsStore:
    __translation_models_list: Set[Type[Model]] = field(default_factory=set)
    __new_created_models_properties: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def translation_models_list(self) -> Tuple[Type[Model]]:
        return tuple(self.__translation_models_list)

    @translation_models_list.setter
    def translation_models_list(self, model):
        if not issubclass(model, Model):
            raise ValueError(f'Class {model} is not subclass of {Model}')
        self.__translation_models_list.add(model)

    @property
    def new_created_models_properties(self):
        return self.__new_created_models_properties

    @new_created_models_properties.setter
    def new_created_models_properties(self, info: Dict[str, List[str]]):
        new_keys = set(info.keys())  # key is name of base (marked as translatable) model
        # registered models names
        allowed_keys = set(map(lambda x: x.get_base_model_name(), self.__translation_models_list))
        intersection = allowed_keys & new_keys
        if not intersection == new_keys:
            raise ValueError(f'{new_keys - allowed_keys} keys are not allowed. '
                             f'Models with such names have not been registered')
        self.__new_created_models_properties.update(info)

    @cached_property
    def global_langs(self):
        return tuple(lang.lower() for lang in settings.TRANSLATING_LANGS)


models_store = TranslationModelsStore()
