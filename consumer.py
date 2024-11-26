import aio_pika
import asyncio
import os
import requests
from bs4 import BeautifulSoup

# Таймаут ожидания сообщений (в секундах)
queue_timeout = 30


# Извлечение ссылок
def extract_links(url, base_domain):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Текущая страницу
        title = soup.title.string.strip() if soup.title else "No Title"
        print(f"Обработка страницы: '{title}' ({url})")

        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True) or "No Text"
            if href.startswith('/'):
                href = base_domain + href
            elif not href.startswith('http'):  # Обработка ссылок вида some/path
                href = base_domain + '/' + href
            if base_domain in href:
                links.add(href)
                print(f"Найдена ссылка: '{text}' ({href})")  # Логируем каждую ссылку
        return links
    except requests.RequestException as e:
        print(f"Не удалось получить данные {url}: {e}")
        return set()


# Асинхронный обработчик сообщений
async def on_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        url = message.body.decode()
        print(f"\nПолучен URL: {url}")

        base_domain = f"{url.split('//')[0]}//{url.split('/')[2]}"
        processed_links = set()

        # Обрабатываем текущий URL
        if url not in processed_links:
            processed_links.add(url)
            new_links = extract_links(url, base_domain)

            # Публикуем найденные ссылки обратно в очередь
            try:
                connection = await aio_pika.connect_robust(
                    os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
                )
                async with connection:
                    channel = await connection.channel()
                    for link in new_links:
                        await channel.default_exchange.publish(
                            aio_pika.Message(body=link.encode()),
                            routing_key="links",
                        )
                        print(f"Публикация ссылки: {link}")
            except Exception as e:
                print(f"Ошибка при публикации: {e}")
        else:
            print(f"URL уже обработан: {url}")


# Основной код
async def main():
    connection = await aio_pika.connect_robust(
        host=os.getenv('RABBITMQ_HOST', 'localhost'),
        port=int(os.getenv('RABBITMQ_PORT', 5672)),
        login=os.getenv('RABBITMQ_USER', 'guest'),
        password=os.getenv('RABBITMQ_PASSWORD', 'guest')
    )

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue("links", durable=False)

        print("Ожидание. Нажмите CTRL+C для выхода.")

        try:
            timer = True
            start_time = asyncio.get_event_loop().time()  # Запоминаем время начала
            while True:
                # Ожидание сообщения из очереди
                try:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > queue_timeout:
                        print(f"Таймаут {queue_timeout} секунд истек. Завершение.")
                        break  # Выход из цикла
                    message = await asyncio.wait_for(queue.get(no_ack=False), timeout=queue_timeout)
                    await on_message(message)
                    start_time = asyncio.get_event_loop().time()  # Сбрасываем таймер
                except aio_pika.exceptions.QueueEmpty:
                    if timer:
                        print("Очередь пуста. Ожидание...")
                        timer = False

        except asyncio.CancelledError:
            print("Consumer прерван.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Consumer остановлен.")
