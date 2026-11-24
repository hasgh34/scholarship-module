"""Исключения модуля."""


class ScholarshipError(Exception):
    """Базовое исключение модуля."""


class ConfigError(ScholarshipError):
    """Ошибка в файле правил."""


class InvalidInputError(ScholarshipError):
    """Некорректные входные данные студента."""
