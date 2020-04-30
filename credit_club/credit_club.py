import os
import pytest

from selenium import webdriver


LOGIN = '9196884718'
PASSWORD = 'pas1234567'
AUTH_URL = 'https://test.partner.credit.club/login'


@pytest.fixture()
def authenticate():
    """
    Фикстура для авторизации в кабинете пользователя.

    :return: driver
    """
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)
    driver.get(AUTH_URL)

    insert_login(driver)
    insert_password_and_enter(driver)

    return driver


def insert_login(driver):
    """
    Утилита по вводу логина на страницке авторизации.

    :return: None
    """
    input_field = driver.find_element_by_tag_name('input')
    submit_button = driver.find_element_by_tag_name('button')

    input_field.send_keys(LOGIN)
    submit_button.submit()


def insert_password_and_enter(driver):
    """
    Утилита по вводу пароля на странице авторизации.
    Выполняется переход на страницу оформления заявки.

    :return: None
    """
    input_field = driver.find_element_by_xpath('//form/div[3]/div/input')
    submit_button = driver.find_element_by_tag_name('button')

    input_field.send_keys(PASSWORD)
    submit_button.submit()


def test_application_form(authenticate):
    """
    Тест на проверку работоспособности формы по оформлению заявки.
    """
    driver = authenticate

    create_button = driver.find_element_by_xpath('//div[1]/button')
    create_button.click()

    name, phone, email, lend, term, file = driver.find_elements_by_tag_name('input')
    comment = driver.find_element_by_tag_name('textarea')

    name.send_keys('Иванов Иван Иванович')
    # дополнительный клик по имени в подсказке
    prompt = driver.find_element_by_xpath('//div[@class="Autocomplete-module_option__2ZVpV"]/div')
    prompt.click()

    phone.send_keys('999 999-99-99')
    email.send_keys('kek@foo.bar')
    lend.send_keys('200000')
    term.send_keys('6')
    comment.send_keys('test_comment')
    file.send_keys(os.getcwd()+"/test.txt")

    submit_button = driver.find_element_by_tag_name('button')
    submit_button.click()

    try:
        info_card = driver.find_element_by_xpath('//div[contains(@class, "Message_wrapper")]')
    except NoSuchElementException:
        pytest.fail('Element does not present on this site')

    assert 'Уведомление' in info_card.text
    assert 'Ваша заявка обрабатывается, скоро она появится в списке заявок' in info_card.text
