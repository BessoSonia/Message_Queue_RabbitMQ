# Message Queue Parser

## Описание проекта
**Message Queue Parser** — это асинхронное приложение для обработки ссылок с веб-страниц с использованием очередей сообщений RabbitMQ. 

Приложение состоит:
1. **Producer** — добавляет ссылки в очередь `links`.
2. **Consumer** — обрабатывает ссылки из очереди, извлекая данные и публикуя новые ссылки обратно в очередь.

## Используемые технологии
- **Python 3.11**.
- **RabbitMQ** — для обработки сообщений.
- **aio-pika** — библиотека для работы с RabbitMQ.
- **BeautifulSoup4** — библиотека для парсинга HTML.

## Установка и настройка
1. Убедитесь, что у вас установлен **Python 3.10** и **RabbitMQ**.

2. Склонируйте репозиторий и перейдите в директорию проекта:

    ```
    git clone https://github.com/BessoSonia/Message_Queue_RabbitMQ
    cd Message_Queue_RabbitMQ
    ```

3. Установите зависимости (beautifulsoup4, requests, aio-pika)

    ```
    pip install -r requirements.txt
    ```

4. Настройте RabbitMQ

    - Убедитесь, что RabbitMQ запущен на localhost
    - Настройте переменные окружения для подключения:
        - RABBITMQ_HOST
        - RABBITMQ_PORT
        - RABBITMQ_USER
        - RABBITMQ_PASSWORD

5. Запуск

    Запустите Producer:

    ```
    python producer.py
    ``` 

    Запустите Consumer:
    
    ```
    python consumer.py
    ```
