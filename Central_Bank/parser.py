from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


URL = 'https://ru.investing.com/'


def get_driver():
    """
    Фикстура для создания Selenium-WebDriver.

    :return: driver
    """
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)
    driver.get(URL)

    return driver


def stocks_parser():
    """

    :return: dict gathered_stocks
    """
    gathered_stocks = dict()
    driver = get_driver()

    quotation = driver.find_element_by_xpath('//a[contains(@href,"/markets/")]')
    stock = driver.find_element_by_css_selector('li.row:nth-child(4)')
    stoks_russia = driver.find_element_by_xpath('//a[contains(@href,"/equities/russia")]')

    actions = ActionChains(driver)
    actions.move_to_element(quotation).perform()
    actions.move_to_element(stock).perform()
    actions.click(stoks_russia)
    actions.perform()

    # TODO спарсить данные из таблицы