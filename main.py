import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
import os
import re
from urllib.parse import urljoin


# Функция для скрапинга данных с AutoRia
def scrape_auto_ria(url, connection):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        car_list = soup.find_all('div', class_='proposition')
        for car in car_list:
            link = urljoin(url, car.find('a', class_='proposition_link')['href'])
            data = scrape_car_data(link)
            if data:
                insert_into_database(data, connection)


# Функция для скрапинга данных с карточки авто
def scrape_car_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1', class_='proposition_name').text
        price_text = soup.find('span', class_='size22').text
        price_usd = float(re.sub(r'[^\d.]', '', price_text))
        odometer_text = soup.find('li', class_='race').text
        odometer = int(re.sub(r'[^\d]', '', odometer_text))
        username = soup.find('div', class_='user-name').text
        phone = soup.find('div', class_='phone').text
        image_url = soup.find('img', class_='open-photo')['src']
        images_count = len(soup.find_all('div', class_='photo-item'))
        car_number = soup.find('li', class_='autoID')
        car_vin = soup.find('li', class_='vin')

        data = {
            'url': url,
            'title': title,
            'price_usd': price_usd,
            'odometer': odometer,
            'username': username,
            'phone_number': phone,
            'image_url': image_url,
            'images_count': images_count,
            'car_number': car_number.text if car_number else None,
            'car_vin': car_vin.text if car_vin else None,
            'datetime_found': datetime.now()
        }
        return data
    return None



def insert_into_database(data, connection):
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO auto_data (url, title, price_usd, odometer, username, phone_number, image_url, images_count, car_number, car_vin, datetime_found)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        data['url'], data['title'], data['price_usd'], data['odometer'],
        data['username'], data['phone_number'], data['image_url'],
        data['images_count'], data['car_number'], data['car_vin'], data['datetime_found']
    ))
    connection.commit()



def create_daily_dump(connection):
    dump_file = os.path.join('dumps', datetime.now().strftime('%Y-%m-%d.dump'))
    subprocess.run(['pg_dump', '-U', 'your_db_user', '-d', 'your_db_name', '-f', dump_file])


# URL AutoRia
auto_ria_url = 'https://auto.ria.com/car/mercedes-benz/'


db_connection = psycopg2.connect(
    dbname='your_db_name',
    user='your_db_user',
    password='your_db_password',
    host='Autoria'  # Имя контейнера Docker для PostgreSQL
)


scrape_auto_ria(auto_ria_url, db_connection)

db_connection.close()