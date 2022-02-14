class MyError(Exception):
    """Ошибка недоступности эндпоинта."""

    def __init__(self, text):
        """Переопределяем текст ошибки."""
        self.txt = text
