from random import choice
import string
import time

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


AUTH_URL = 'https://dev.adapty.io/registration'
COMPANY_NAME = 'kek'
PASSWORD = 'qwe123'
APP_NAME = 'test'


@pytest.fixture()
def get_auth_page():
    """
    Фикстура для перехода к странице с формой авторизации.

    :return: driver
    """
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)
    driver.get(AUTH_URL)

    return driver


def generate_email():
    """
    Утилита генерации email для регистрируемого пользователя.
    email является уникальным, поэтому на каждый тест нужно генерировать новый.

    :return: email
    """
    email_head = [choice(string.ascii_letters) for _ in range(5)]
    email_tail = '@domain.foo'
    # Собираем строки
    email_head = ''.join(email_head)
    email = email_head + email_tail

    return email


def add_first_app(driver):
    """
    Утилита для создания first_app.

    :return:
    """
    add_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, '//div[3]/button'))
    )
    add_btn.click()

    app_name_field = driver.find_element_by_tag_name('input')
    app_name_field.send_keys(APP_NAME)

    continue_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '//span/button'))
    )
    time.sleep(3)  # костыль, но без него драйвер отказывается жать на кнопку
    driver.execute_script("arguments[0].click();", continue_btn)


def test_registration_form(get_auth_page):
    """
    Тест на проверку работоспособности формы регистрации пользователей.
    """
    driver = get_auth_page
    email = generate_email()

    try:
        (company_name_field,
         email_field,
         password_field,
         confirm_password_field) = driver.find_elements_by_tag_name('input')
    except NoSuchElementException:
        pytest.fail('Element does not present on this site')

    company_name_field.send_keys(COMPANY_NAME)
    email_field.send_keys(email)
    password_field.send_keys(PASSWORD)
    confirm_password_field.send_keys(PASSWORD)

    sing_up_button = driver.find_elements_by_tag_name('button')[1]
    sing_up_button.click()

    add_first_app(driver)

    skip = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '//span[text()= "Skip"]'))
    )

    driver.execute_script("arguments[0].click();", skip)

    url = driver.current_url
    url = url.split('dashboard')[0] + 'account'
    driver.get(url)

    try:
        added_company = driver.find_element_by_xpath('//div[1]//span/input')
        added_email = driver.find_element_by_xpath('//div[4]//span/input')
    except NoSuchElementException:
        pytest.fail('Element does not present on this site')

    assert added_company.get_attribute('value') == COMPANY_NAME
    assert added_email.get_attribute('value') == email
