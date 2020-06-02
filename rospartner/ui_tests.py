"""
Module with UI-tests
"""
import pytest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from utils import generate_email_name


URL = 'http://localhost:4000/ui'


@pytest.fixture()
def create_driver():
    """
    fixture to create driver-objeect and get page.
    delets subscriptions from the list.

    :return: Webdriver
    """
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)
    driver.get(URL)

    yield driver

    delete_button = get_delete_button(driver)
    delete_button.click()
    driver.quit()


def get_email_field(driver):
    """
    utility to find web-element 'email field'

    :return: WebElement
    """
    email_field = driver.find_element_by_css_selector('input.form-control:nth-child(1)')

    return email_field


def get_username_field(driver):
    """
    utility to find web-element 'username_field'

    :return: WebElement
    """
    username_field = driver.find_element_by_css_selector('input.form-control:nth-child(2)')

    return username_field


def get_time_field(driver):
    """
    utility to find web-element 'time_field'

    :return: WebElement
    """
    time_field = driver.find_element_by_css_selector('input.form-control:nth-child(3)')

    return time_field


def get_subscribe_button(driver):
    """
    utility to find web-element 'subscribe button'

    :return: WebElement
    """
    subscribe_button = driver.find_element_by_css_selector('.btn-success')

    return subscribe_button


def get_delete_button(driver):
    """
    utility to find web-element 'delete button'

    :return: WebElement
    """
    delete_button = driver.find_element_by_css_selector('button.btn:nth-child(2)')

    return delete_button


def create_subscription(driver, time_value='5d'):
    """
    utility to create new subscription

    :return: tuple(email, name)
    """
    email, name = generate_email_name()

    email_field = get_email_field(driver)
    email_field.send_keys(email)

    username_field = get_username_field(driver)
    username_field.send_keys(name)

    time_field = get_time_field(driver)
    time_field.clear()  # remove default value
    time_field.send_keys(f'{time_value}')

    subscribe_button = get_subscribe_button(driver)
    subscribe_button.click()

    return email, name


@pytest.mark.parametrize("time_value", ("7d", "kek"))
def test_add_subscription(create_driver, time_value):
    """
    add new subscription, make sure that it exetst.
    """
    driver = create_driver
    email, name = create_subscription(driver, time_value)

    try:
        new_subscription = driver.find_element_by_css_selector('.table > tbody:nth-child(2) > tr:nth-child(1)')
    except NoSuchElementException:
        pytest.fail('New subscription was not added')

    try:
        new_subscription.find_element_by_xpath(f"//*[contains(text(), '{email}')]")
    except NoSuchElementException:
        pytest.fail('Email was not added')

    try:
        new_subscription.find_element_by_xpath(f"//*[contains(text(), '{name}')]")
    except NoSuchElementException:
        pytest.fail('Name was not added')

    try:
        image = new_subscription.find_element_by_tag_name('svg')
    except NoSuchElementException:
        pytest.fail('No subscription status')


def test_view_five_items(create_driver):
    """
    check that only 5 subscriptions are displayed in the list at a time.
    """
    driver = create_driver

    for _ in range(6):
        create_subscription(driver)

    try:
        table = driver.find_element_by_tag_name('tbody')
    except NoSuchElementException:
        pytest.fail('No table element')

    try:
        subscription_list = table.find_elements_by_tag_name('tr')
    except NoSuchElementException:
        pytest.fail('No elements in table')

    assert len(subscription_list) - 1 == 5
