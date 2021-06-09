from googletrans import Translator
import typing

translator = Translator(service_urls=['translate.googleapis.com'])


def translate(data: typing.Union[list, tuple], lang: str) -> typing.Iterable:
    return translator.translate(text=list(data), dest=lang)


