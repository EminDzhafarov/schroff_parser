# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from lxml import etree


download_dir = ''  # Директория для документов
# Инициализация драйвера
chrome_options = Options()
# chrome_options.add_argument("--headless")
profile = {
    'download.prompt_for_download': False,
    'download.default_directory': download_dir,
    'download.directory_upgrade': False,
    'plugins.always_open_pdf_externally': True,
}
chrome_options.add_experimental_option('prefs', profile)
driver = webdriver.Chrome(options=chrome_options)


items = []

for page in range(0, 10, 10):
    url = f"https://schroff.nvent.com/ru-ru/search#first={page}&t=Tab_All&f:@nventtype=[Product%20Item]"
    driver.get(url)
    time.sleep(3)
    elements = driver.find_elements(By.CLASS_NAME, 'nventCatalogId')
    for element in elements:
        item = []
        item_id = element.find_elements(By.TAG_NAME, 'span')[1].text
        item.append(item_id)
        item.append(f'https://schroff.nvent.com/ru-ru/products/enc{item_id}')
        item.append(f'https://schroff.nvent.com/ru-ru/products/enc{item_id}/pdf')
        items.append(item)

# Создаем описание магазина
root = etree.Element('catalog', date=str(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S%z")) + "+03:00")
shop = etree.SubElement(root, 'shop')
etree.SubElement(shop, 'name').text = "Schroff"
etree.SubElement(shop, 'company').text = 'nVent'

for item in items:
    driver.get(item[1])
    time.sleep(3)
    item_id = driver.find_element(By.XPATH, '//*[@id="block-mainpagecontent"]/div/div/div/div'
                                            '[3]/div/price-block/div/div[1]/span').text
    name = driver.find_element(By.CLASS_NAME, 'product-hero__title').text
    description = driver.find_element(By.CLASS_NAME, 'product-hero__description').text
    attributes = driver.find_element(By.CLASS_NAME, 'products-attribute__list').text

    # Артикул
    print(item_id)
    # Название позиции
    print(name)
    # Описание позиции
    print(description)
    # Атрибуты позиции
    print(attributes)

    # Создаем карточку товара
    offer = etree.SubElement(shop, 'offer', id=str(item_id))
    etree.SubElement(offer, 'name').text = name
    etree.SubElement(offer, 'description').text = description
    etree.SubElement(offer, 'attributes').text = attributes

    # Скачиваем картинки
    driver.find_element(By.XPATH, '//*[@id="block-mainpagecontent"]/div/div/div/div[2]/div[1]'
                                  '/div/div[2]/div/div[2]/ul').click()
    slick_track = driver.find_element(By.CLASS_NAME, "slick-track")
    images = slick_track.find_elements(By.TAG_NAME, "img")

    for image in images:
        image_url = image.get_attribute("src")  # Получение ссылки на картинку
        response = requests.get(image_url)
        response.raise_for_status()

        with open(f'images/{item_id}_{images.index(image)}.png.webp', 'wb') as file:
            file.write(response.content)
        etree.SubElement(offer, f'picture').text = f"{item_id}_{images.index(image)}.png.webp"

    # Скачиваем документы
    driver.get(item[2])
    driver.execute_script("document.title = \'{}\'".format("filename"))
    time.sleep(3)

    file_name = ""

    while file_name.lower().endswith('.pdf') is False:
        time.sleep(.25)
        try:
            file_name = max([download_dir + '/' + f for f in os.listdir(download_dir)], key=os.path.getctime)
            file_name = file_name.split("/")[-1]
            # Директория PDF
            print(file_name)
            etree.SubElement(offer, 'document').text = file_name
        except ValueError:
            pass


tree = etree.ElementTree(root)
tree.write("file.xml", encoding="utf-8", xml_declaration=True)

# Закрытие браузера
driver.quit()
