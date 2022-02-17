class MyDescriptionOfError(Exception):
    """Собственное описание ошибки."""

    def __init__(self, text):
        """Переопределяем текст ошибки."""
        self.txt = text
