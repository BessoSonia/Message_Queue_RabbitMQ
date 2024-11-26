import sys
import requests
from bs4 import BeautifulSoup
import pika
import os


# Подключение к RabbitMQ
def connect_to_rabbitmq():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST', 'localhost'),
            port=int(os.getenv('RABBITMQ_PORT', 5672)),
            credentials=pika.PlainCredentials(
                username=os.getenv('RABBITMQ_USER', 'guest'),
                password=os.getenv('RABBITMQ_PASSWORD', 'guest')
            )
        )
    )
    return connection.channel()


# Извлечение ссылок
def extract_links(url, base_domain):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/'):  # Обработка ссылок вида /some/path
                href = base_domain + href
            elif not href.startswith('http'):  # Обработка ссылок вида some/path
                href = base_domain + '/' + href
            if base_domain in href:
                links.add(href)
        return links

    except requests.RequestException as e:
        print(f"Не удалось получить данные {url}: {e}")
        return set()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python link_parser.py <URL>")
        sys.exit(1)

    start_url = sys.argv[1]
    base_domain = start_url.split('/')[0] + '//' + start_url.split('/')[2]

    print(f"Извлечение ссылок из {start_url}")
    links = extract_links(start_url, base_domain)

    channel = connect_to_rabbitmq()
    channel.queue_declare(queue='links')

    for link in links:
        channel.basic_publish(exchange='', routing_key='links', body=link)
        print(f"Добавлено в очередь: {link}")

    print("Все ссылки добавлены в очередь.")
