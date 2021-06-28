import typing

from googletrans import Translator

translator = Translator(service_urls=['translate.googleapis.com'])


def translate(data: typing.Union[list, tuple], lang: str) -> typing.Iterable:
    return translator.translate(text=list(data), dest=lang)


