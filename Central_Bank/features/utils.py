from string import ascii_letters
from random import choice


class TextNotFound(Exception):
    """
    Исключение, вызываемое при отсутствии в документе вводимого текста.
    """
    def __init__(self, value):
        Exception.__init__(self, f'TextNotFound has occered with param {value}')
        self.value = value


def generate_text():
    """
    Функция-генератор случайного текста
    """
    text = [choice(ascii_letters) for _ in range(5)]
    # Собираем строку
    text = ''.join(text)

    return text
