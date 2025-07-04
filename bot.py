import os
import re
import shutil
import subprocess
import sys
import time
import requests
from packaging import version
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'
CHROME_JSON_URL = 'https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json'

STORE_URL = 'https://theventashop.com/'

SHIPPING_INFO = {
    'email': 'test@example.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'address1': '123 Elm Street',
    'city': 'Los Angeles',
    'country': 'United States',
    'province': 'California',
    'zip': '90001',
    'phone': '1234567890'
}

PAYMENT_INFO = {
    'card_number': '5424587008239322',
    'name_on_card': 'John Doe',
    'expiry': '12/34',
    'cvv': '123'
}

def get_chrome_version():
    output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
    match = re.search(r'(\d+\.\d+\.\d+)', output)
    return match.group(1)

def download_and_install_chromedriver(driver_url):
    zip_path = '/tmp/chromedriver_linux64.zip'
    extracted_path = '/tmp/chromedriver-linux64/chromedriver'

    r = requests.get(driver_url, stream=True)
    with open(zip_path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)

    subprocess.run(['unzip', '-o', zip_path, '-d', '/tmp/'], check=True)

    shutil.move(extracted_path, CHROME_DRIVER_PATH)
    os.chmod(CHROME_DRIVER_PATH, 0o755)

def install_best_chromedriver():
    chrome_ver = get_chrome_version()
    major_ver = int(chrome_ver.split('.')[0])

    data = requests.get(CHROME_JSON_URL).json()
    milestones = data['milestones']

    suitable = []
    for milestone, details in milestones.items():
        if int(milestone) <= major_ver and details.get('downloads', {}).get('chromedriver'):
            suitable.append((int(milestone), details))

    best_milestone, best_data = max(suitable, key=lambda x: x[0])
    linux64 = next(d for d in best_data['downloads']['chromedriver'] if d['platform'] == 'linux64')
    download_and_install_chromedriver(linux64['url'])

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(CHROME_DRIVER_PATH, options=options)

def get_cheapest_product(driver):
    driver.get(STORE_URL)
    time.sleep(3)
    products = driver.find_elements(By.CSS_SELECTOR, 'a.full-unstyled-link')
    product_data = []

    for product in products:
        title = product.text.strip()
        if not title:
            continue
        try:
            price_element = product.find_element(By.XPATH, './/following-sibling::*[contains(text(), "$")])')
            price = float(price_element.text.strip().replace('$', '').replace(',', ''))
            link = product.get_attribute('href')
            product_data.append({'title': title, 'price': price, 'link': link})
        except:
            continue

    return min(product_data, key=lambda x: x['price'])

def add_to_cart(driver, product_link):
    driver.get(product_link)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="add"]'))).click()
    time.sleep(2)
    driver.get(STORE_URL + '/cart')
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="checkout"], a[href*="/checkouts/"]'))).click()

def fill_shipping_info(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'checkout_email'))).send_keys(SHIPPING_INFO['email'])
    driver.find_element(By.ID, 'checkout_shipping_address_first_name').send_keys(SHIPPING_INFO['first_name'])
    driver.find_element(By.ID, 'checkout_shipping_address_last_name').send_keys(SHIPPING_INFO['last_name'])
    driver.find_element(By.ID, 'checkout_shipping_address_address1').send_keys(SHIPPING_INFO['address1'])
    driver.find_element(By.ID, 'checkout_shipping_address_city').send_keys(SHIPPING_INFO['city'])
    driver.find_element(By.ID, 'checkout_shipping_address_zip').send_keys(SHIPPING_INFO['zip'])
    driver.find_element(By.ID, 'checkout_shipping_address_phone').send_keys(SHIPPING_INFO['phone'])
    driver.find_element(By.ID, 'checkout_shipping_address_country').send_keys(SHIPPING_INFO['country'])
    driver.find_element(By.ID, 'checkout_shipping_address_province').send_keys(SHIPPING_INFO['province'])
    driver.find_element(By.CSS_SELECTOR, 'button[name="button"]').click()
    time.sleep(5)

def main():
    install_best_chromedriver()
    driver = init_driver()
    cheapest = get_cheapest_product(driver)
    add_to_cart(driver, cheapest['link'])
    fill_shipping_info(driver)
    driver.quit()

if __name__ == '__main__':
    main()
