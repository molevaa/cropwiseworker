
# cropwiseworker

## Описание
Модуль `Cropwise Worker` предназначен для работы с API цифровой платформы управления агропредприятием Cropwise Operations. Модуль позволяет взаимодействовать с различными данными платформы, облегчая интеграцию и автоматизацию задач.

## Установка
Установите пакет с помощью pip:

```bash
pip install cropwiseworker
```

## Пример использования
Пример использования модуля для получения информации о полях:

```python
from cropwiseworker import data_downloader

token='YOUR_TOKEN'

field_data = data_downloader('fields',token)
print(field_data)
```

## Лицензия
Данный пакет распространяется под лицензией Apache License 2.0.
