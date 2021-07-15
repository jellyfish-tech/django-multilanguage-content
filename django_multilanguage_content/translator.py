from googletrans import Translator
from deep_translator import GoogleTranslator
from .exceptions import ResponseError


class BigBoyTranslator:
    def __init__(self):
        self.state = 0
        self.tries = 1
        self.max_tries = 5
        self.translators = [self.translate_1, self.translate_2]
        self.now_translator = self.translators[self.state]

    def translate_1(self, data, lang):
        translated = Translator(service_urls=['translate.googleapis.com']).translate(text=list(data), dest=lang)
        response = []
        for d in translated:
            response.append(d.text)
        return response

    def translate_2(self, data, lang):
        response = GoogleTranslator(source='auto', target=lang).translate_batch(batch=data)
        return response

    def __call__(self, list_values, lang, **kwargs):
        self.tries = 1
        while self.tries:
            self.now_translator = self.translators[self.state]
            try:
                self.tries += 1
                response = self.now_translator(list_values, lang)
            except Exception:
                self.state += 1
                if self.state > len(self.translators)-1:
                    self.state = 0
            else:
                self.tries = 0
                return response
            finally:
                if self.tries > self.max_tries:
                    raise ResponseError('Any of translation services does not respond')


main_translator = BigBoyTranslator()
