from random import choice, randint
from string import ascii_letters
from urllib.parse import urlparse

import pytest
import requests
from IPy import IP
from requests.exceptions import ReadTimeout

from website_tests.utils import (
    generate_login_password, create_profile, generate_public_ip, make_requests_post, DATA_PATTERN
)


pytestmark = pytest.mark.usefixtures('disable_request_warnings')


def get_APC_version(host, login, password):
    """
    Функция определяет текущую версию мобильного приложения и возвращает ее значение.
    """
    method = 'getAPCVersion'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(host, data, auth=(login, password))

    try:
        result = response.json()['result']
        version = result['current']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    return version


def get_myip(host, login, password):
    """
    Функция определяет текущий IP адрес и возвращает ее значение.
    """
    method = 'myip'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(host, data, auth=(login, password))

    try:
        address = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    return address


def get_default_profile_and_uid(host, login, password):
    """
    Функция определяет айдишник default-профиля.
    Используется метод getProfile.
    """
    hostname = 'SkyDNSAgent'
    os_info = 'DESKTOP-N2NBFCQ'

    version = get_APC_version(host, login, password)
    address = get_myip(host, login, password)

    method = "getProfile"
    params = '"{}", "{}", "{}", "{}", "{}"'.format('', hostname, version, os_info, address,)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(host, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    profile_id = result[2]
    uid = result[0]

    return profile_id, uid


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_plans_amount, expected_plans_length", [
        ('xorp_host', 13, 7),
        ('tredy_host', 30, 7),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_get_plans(xorp_and_tredy_hosts, expected_plans_amount, expected_plans_length):
    """
    Тест апи-метода getPlans. Запрашиваем список тарифных планов.
    Валидируем ответы числа доступных тарифов и числа атрибутов для каждого тарифа.
    """
    method = 'getPlans'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data)

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert len(result) == expected_plans_amount
    for plan_attribute in range(len(result)):
        assert len(result[plan_attribute]) == expected_plans_length


def test_register(xorp_and_tredy_hosts):
    """
    Тест апи-метода register. Создаем пользователя.
    Валидируем по коду ответа.
    """
    login, password = generate_login_password()

    method = 'register'
    params = '"{}", "{}"'.format(login, password)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result == [True]


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_plan_name", [
        ('xorp_host', 'Домашний'),
        ('tredy_host', 'Safe@Home'),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_get_plan(xorp_and_tredy_hosts, expected_plan_name, rpc_user):
    """
    Тест апи-метода getPlan. Создаем пользователя.
    Запрашиваем у пользователя тариф.
    Верифицируем ответы отдельно для ксорпа и треди
    """
    login, password = rpc_user

    method = 'getPlan'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result['isMobile'], 'Ошибка параметра isMobile'
    assert result['expired'] == 15
    assert result['name'] == expected_plan_name


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_time_zone, expected_tz_minutes, expected_plan_name, expected_list_size", [
        ('xorp_host', 3.0, 180.0, 'Домашний', 100),
        ('tredy_host', -5.0, -300, 'Safe@Home', 50),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_user_info(
    xorp_and_tredy_hosts, expected_time_zone, expected_tz_minutes,
    expected_plan_name, expected_list_size, rpc_user
):
    """
    Тест апи-метода userInfo. Создаем пользователя.
    Запрашиваем информацию о пользователе.
    Верифицируем ответы для ксорпа и треди.
    Из-за перехода на зимнее/летнее время на треди параметры tz и tz_minutes нужно обновлять на +/- 1 час
    """
    login, password = rpc_user

    method = 'userInfo'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    assert 'result' in response.json().keys(), response.json()['error']['message']

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result['plan']['code'] == 'PREMIUM'
    assert result['plan']['features']['aliases_list_size'] == 15
    assert not result['plan']['features']['agent_ip_mode'], 'Ошибка параметра agent_ip_mode'
    assert result['plan']['features']['safe_search']
    assert result['plan']['features']['max_profiles'] == 3
    assert result['plan']['features']['white_list_mode']
    assert not result['plan']['features']['show_dns_listen_addr'], 'Ошибка параметра show_dns_listen_addr'
    assert result['tz'] == expected_time_zone
    assert result['tz_minutes'] == expected_tz_minutes
    assert result['plan']['name'] == expected_plan_name
    assert result['plan']['features']['black_list_size'] == expected_list_size
    assert result['plan']['features']['white_list_size'] == expected_list_size


def test_get_apc_version(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода getAPCVersion. Создаем пользователя.
    Проверяем минимально-поддерживаемую версию и
    текущую версию мобильного приложения.
    """
    login, password = rpc_user
    method = 'getAPCVersion'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result['current'] == 1
    assert result['minimalSupported'] == 0


def test_authenticate_not_registered(xorp_and_tredy_hosts):
    """
    Тест апи-метода testAuth. Вызываем метод для незарегистрированного пользователя.
    """
    login, password = generate_login_password()

    method = 'testAuth'
    params = '"{}", "{}"'.format(login, password)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_authenticate_with_registered(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода testAuth. Регистрируем пользователя.
    Вызываем метод для зарегистрированного пользователя.
    """
    login, password = rpc_user

    method = 'testAuth'
    params = '"{}", "{}"'.format(login, password)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result


def test_system_info(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода systemInfo. Создаем пользователя.
    Запрашиваем для пользователя системные настройки.
    Валидируем результат.
    """
    login, password = rpc_user

    method = 'systemInfo'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert len(result) == 5
    assert IP(result['blockapi']).iptype() == 'PUBLIC'
    assert IP(result['blockapi']).version() == 4
    assert IP(result['blockpage_token']).iptype() == 'PUBLIC'
    assert IP(result['blockpage_token']).version() == 4

    for IP_addr in result['public_dns']:
        assert IP(IP_addr).iptype() == 'PUBLIC'
        assert IP(IP_addr).version() == 4

    assert IP(result['nxdomain']).iptype() == 'PUBLIC'
    assert IP(result['nxdomain']).version() == 4
    assert IP(result['blockpage']).iptype() == 'PUBLIC'
    assert IP(result['blockpage']).version() == 4


EXPECTED_XORP_CATEGORIES = [
    {
        'items': [
            {'id': 3, 'title': 'Virus Propagation'},
            {'id': 4, 'title': 'Phishing'},
            {'id': 12, 'title': 'Botnets'},
        ],
        'title': 'Security'
    },
    {
        'items': [
            {'id': 6, 'title': 'Drugs'},
            {'id': 7, 'title': 'Tasteless'},
            {'id': 8, 'title': 'Academic Fraud'},
            {'id': 9, 'title': 'Parked Domains'},
            {'id': 10, 'title': 'Hate & Discrimination'},
            {'id': 11, 'title': 'Proxies & Anonymizers'},
            {'id': 66, 'title': 'Crypto Mining'},
        ],
        'title': 'Illegal Activity'
     },
    {
        'items': [
            {'id': 13, 'title': 'Adult Sites'},
            {'id': 14, 'title': 'Alcohol & Tobacco'},
            {'id': 15, 'title': 'Dating'},
            {'id': 16, 'title': 'Pornography & Sexuality'},
            {'id': 17, 'title': 'Astrology'},
            {'id': 18, 'title': 'Gambling'},
        ],
        'title': 'Adult Related'
     },
    {
        'items': [
            {'id': 20, 'title': 'Torrents & P2P'},
            {'id': 21, 'title': 'File Storage'},
            {'id': 22, 'title': 'Movies & Video'},
            {'id': 23, 'title': 'Music & Radio'},
            {'id': 24, 'title': 'Photo Sharing'},
        ],
        'title': 'Bandwidth Hogs'
     },
    {
        'items': [
            {'id': 5, 'title': 'Online Ads'},
            {'id': 26, 'title': 'Chats & Messengers'},
            {'id': 27, 'title': 'Forums'},
            {'id': 28, 'title': 'Games'},
            {'id': 29, 'title': 'Social Networks'},
            {'id': 30, 'title': 'Entertainment'},
        ],
        'title': 'Time Wasters'
     },
    {
        'items': [
            {'id': 32, 'title': 'Automotive'},
            {'id': 33, 'title': 'Blogs'},
            {'id': 34, 'title': 'Corporate Sites'},
            {'id': 35, 'title': 'E-commerce'},
            {'id': 36, 'title': 'Education'},
            {'id': 37, 'title': 'Finances'},
            {'id': 38, 'title': 'Government'},
            {'id': 39, 'title': 'Health & Fitness'},
            {'id': 40, 'title': 'Humor'},
            {'id': 41, 'title': 'Jobs & Career'},
            {'id': 42, 'title': 'Weapons'},
            {'id': 43, 'title': 'Politics, Society and Law'},
            {'id': 44, 'title': 'News & Media'},
            {'id': 45, 'title': 'Non-profit'},
            {'id': 46, 'title': 'Portals'},
            {'id': 47, 'title': 'Religious'},
            {'id': 48, 'title': 'Search Engines'},
            {'id': 49, 'title': 'Computers & Internet'},
            {'id': 50, 'title': 'Sports'},
            {'id': 51, 'title': 'Science & Technology'},
            {'id': 52, 'title': 'Travel'},
            {'id': 53, 'title': 'Home & Family'},
            {'id': 54, 'title': 'Shopping'},
            {'id': 55, 'title': 'Arts'},
            {'id': 56, 'title': 'Webmail'},
            {'id': 57, 'title': 'Real Estate'},
            {'id': 58, 'title': 'Classifieds'},
            {'id': 59, 'title': 'Business'},
            {'id': 60, 'title': 'Kids'},
            {'id': 62, 'title': 'Paid sites of mobile operators'},
            {'id': 63, 'title': 'Trackers & Analytics'},
            {'id': 67, 'title': 'Online Libraries'},
        ],
        'title': 'General Sites'
     }
]

EXPECTED_TREDY_CATEGORIES = [
    {
        'items': [
            {'id': 3, 'title': 'Virus Propagation'},
            {'id': 4, 'title': 'Phishing'},
            {'id': 12, 'title': 'Botnets'},
        ],
        'title': 'Security'
     },
    {
        'items': [
            {'id': 6, 'title': 'Drugs'},
            {'id': 7, 'title': 'Tasteless'},
            {'id': 8, 'title': 'Academic Fraud'},
            {'id': 9, 'title': 'Parked Domains'},
            {'id': 10, 'title': 'Hate & Discrimination'},
            {'id': 11, 'title': 'Proxies & Anonymizers'},
            {'id': 19, 'title': 'Child Sexual Abuse (IWF)'},
            {'id': 31, 'title': 'German Youth Protection'},
            {'id': 65, 'title': 'Child Sexual Abuse (Arachnid)'},
            {'id': 66, 'title': 'Crypto Mining'},
        ],
        'title': 'Illegal Activity'
     },
    {
        'items': [
            {'id': 13, 'title': 'Adult Sites'},
            {'id': 14, 'title': 'Alcohol & Tobacco'},
            {'id': 15, 'title': 'Dating'},
            {'id': 16, 'title': 'Pornography & Sexuality'},
            {'id': 17, 'title': 'Astrology'},
            {'id': 18, 'title': 'Gambling'},
        ],
        'title': 'Adult Related'
     },
    {
        'items': [
            {'id': 20, 'title': 'Torrents & P2P'},
            {'id': 21, 'title': 'File Storage'},
            {'id': 22, 'title': 'Movies & Video'},
            {'id': 23, 'title': 'Music & Radio'},
            {'id': 24, 'title': 'Photo Sharing'},
        ],
        'title': 'Bandwidth Hogs'
     },
    {
        'items': [
            {'id': 5, 'title': 'Online Ads'},
            {'id': 26, 'title': 'Chats & Messengers'},
            {'id': 27, 'title': 'Forums'},
            {'id': 28, 'title': 'Games'},
            {'id': 29, 'title': 'Social Networks'},
            {'id': 30, 'title': 'Entertainment'},
        ],
        'title': 'Time Wasters'
     },
    {
        'items': [
            {'id': 32, 'title': 'Automotive'},
            {'id': 33, 'title': 'Blogs'},
            {'id': 34, 'title': 'Corporate Sites'},
            {'id': 35, 'title': 'E-commerce'},
            {'id': 36, 'title': 'Education'},
            {'id': 37, 'title': 'Finances'},
            {'id': 38, 'title': 'Government'},
            {'id': 39, 'title': 'Health & Fitness'},
            {'id': 40, 'title': 'Humor'},
            {'id': 41, 'title': 'Jobs & Career'},
            {'id': 42, 'title': 'Weapons'},
            {'id': 43, 'title': 'Politics, Society and Law'},
            {'id': 44, 'title': 'News & Media'},
            {'id': 45, 'title': 'Non-profit'},
            {'id': 46, 'title': 'Portals'},
            {'id': 47, 'title': 'Religious'},
            {'id': 48, 'title': 'Search Engines'},
            {'id': 49, 'title': 'Computers & Internet'},
            {'id': 50, 'title': 'Sports'},
            {'id': 51, 'title': 'Science & Technology'},
            {'id': 52, 'title': 'Travel'},
            {'id': 53, 'title': 'Home & Family'},
            {'id': 54, 'title': 'Shopping'},
            {'id': 55, 'title': 'Arts'},
            {'id': 56, 'title': 'Webmail'},
            {'id': 57, 'title': 'Real Estate'},
            {'id': 58, 'title': 'Classifieds'},
            {'id': 59, 'title': 'Business'},
            {'id': 60, 'title': 'Kids'},
            {'id': 63, 'title': 'Trackers & Analytics'},
            {'id': 67, 'title': 'Online Libraries'},
        ],
        'title': 'General Sites'
     }
]


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_categories", [
        ('xorp_host', EXPECTED_XORP_CATEGORIES),
        ('tredy_host', EXPECTED_TREDY_CATEGORIES),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_categories(xorp_and_tredy_hosts, expected_categories, rpc_user):
    """
    Тест апи-метода categories. Создаем пользователя.
    Запрашиваем списк категорий фильтрации.
    Валидируем результат.
    """
    login, password = rpc_user

    method = 'categories'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result == expected_categories


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_categories", [
        ('xorp_host', [3, 4, 6, 9, 11, 12, 13, 16, 18]),
        ('tredy_host', [3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 65]),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_user_filter(xorp_and_tredy_hosts, expected_categories, rpc_user):
    """
    Тест апи-метода userFilter. Создаем пользователя.
    Создаем пользователю профиль.
    Запрашиваем списк установленных категорий фильтрации.
    Валидируем результат.
    """
    login, password = rpc_user
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)

    method = 'userFilter'
    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result == expected_categories


def test_profiles_rpc(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода profiles. Создаем пользователя.
    Запрашиваем список профилей. Валидируем дефолтные настройки.
    """
    login, password = rpc_user

    method = 'profiles'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result'][0]
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert len(result) == 9
    assert result['name'] == 'Основной' or 'Default'
    assert result['default']
    assert not result['white_list_only'], 'Ошибка параметра white_list_only'
    assert isinstance(result['token'], int)
    assert not result['safe_search_enabled'], 'Ошибка параметра safe_search_enabled'
    assert not result['is_schedule_enabled'], 'Ошибка параметра is_schedule_enabled'
    assert not result['safe_youtube_enabled'], 'Ошибка параметра safe_youtube_enabled'
    assert isinstance(result['id'], int)
    assert not result['block_unknown_enabled'], 'Ошибка параметра block_unknown_enabled'


def test_add_profile(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода addProfile.
    Создаем пользователя. Создаем пользователю профиль.
    Проверяем, что профиль добавился и отображается в списке активных профилей.
    """
    login, password = rpc_user
    profile_name = 'my_profile_test'

    method = 'addProfile'
    params = '"{}"'.format(profile_name)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result['name'] == profile_name
    assert not result['default'], 'Ошибка параметра default'
    assert isinstance(result['token'], int)
    assert not result['white_list_only'], 'Ошибка параметра white_list_only'
    assert not result['safe_search_enabled'], 'Ошибка параметра safe_search_enabled'
    assert not result['is_schedule_enabled'], 'Ошибка параметра is_schedule_enabled'
    assert not result['safe_youtube_enabled'], 'Ошибка параметра safe_youtube_enabled'
    assert not result['block_unknown_enabled'], 'Ошибка параметра block_unknown_enabled'

    try:
        profile_id = result['id']
    except KeyError:
        pytest.fail('Ошибка параметра "id":', result)

    method = 'profiles'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result'][1]
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert profile_id == result['id']


def test_remove_profile(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода removeProfile. Создаем пользователя.
    Создаем пользователю профиль. Проверяем, что профиль добавился.
    Удаляем созданный профиль. Проверяем, что профиль удалился.
    """
    login, password = rpc_user
    profile_name = 'Default'
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)

    method = 'profiles'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        profile = response.json()['result'][1]
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert profile_id == profile['id']

    method = 'removeProfile'
    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    method = 'profiles'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert len(result) == 1
    assert result[0]['name'] == profile_name


def test_rename_profile(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода renameProfile. Создаем пользователя.
    Создаем пользователю профиль. Изменем имя профиля.
    Проверяем, что имя изменилось.
    """
    login, password = rpc_user
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    new_name = ''.join(choice(ascii_letters) for i in range(10))

    method = 'renameProfile'
    params = '{}, "{}"'.format(profile_id, new_name)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    assert response.json()['result'] == new_name, 'Ошибка параметра result'

    method = 'profiles'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert len(result) == 2
    assert result[1]['name'] == new_name
    assert result[1]['id'] == profile_id


def test_get_myip(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода myip. Создаем пользователя.
    Запрашиваем и валидируем IP-адрес пользователя.
    """
    login, password = rpc_user
    ip_address = get_myip(xorp_and_tredy_hosts, login, password)

    try:
        assert IP(ip_address)
    except ValueError as ex:
        pytest.fail(ex)

    assert IP(ip_address).version() in [4, 6]


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_prod_servers, expected_test_servers", [
        ('xorp_host', 'www.skydns.ru', 'www.xorp.ru'),
        ('tredy_host', 'www.safedns.com', 'www.tredy.ru'),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_get_advertising(xorp_and_tredy_hosts, expected_prod_servers, expected_test_servers, rpc_user):
    """
    Тест апи-метода getAdvertising. Создаем пользователя.
    Запрашиваем и валидируем информацию об акции
    """
    login, password = rpc_user

    method = 'getAdvertising'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert len(result) == 2
    url = urlparse(result[0])
    assert url.scheme == 'http'
    assert url.netloc == expected_prod_servers
    url = urlparse(result[1])
    assert url.scheme == 'https'
    assert url.netloc == expected_test_servers


def test_get_profile_without_uid(xorp_and_tredy_hosts, rpc_user):
    """
    Тест json-rpc-api метода getProfile. Создаем пользователя.
    Передается запрос без параметра UID.
    """
    login, password = rpc_user

    version = get_APC_version(xorp_and_tredy_hosts, login, password)
    address = get_myip(xorp_and_tredy_hosts, login, password)

    hostname = 'SkyDNSAgent'
    os_info = 'DESKTOP-N2NBFCQ'

    method = 'getProfile'
    params = '"{}", "{}", "{}", "{}", "{}"'.format('', hostname, version, os_info, address)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    uid = result[0]

    assert len(result) == 3
    assert isinstance(result[1], int)
    assert isinstance(result[2], int)


def test_get_profile_all_params(xorp_and_tredy_hosts, rpc_user):
    """
    Тест json-rpc-api метода getProfile. Создаем пользователя.
    Вызываем метод со всеми доступными параметрами.
    """
    login, password = rpc_user

    version = get_APC_version(xorp_and_tredy_hosts, login, password)
    address = get_myip(xorp_and_tredy_hosts, login, password)

    hostname = 'SkyDNSAgent'
    os_info = 'DESKTOP-N2NBFCQ'
    _, uid = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'getProfile'
    params = '"{}", "{}", "{}", "{}", "{}"'.format(uid, hostname, version, os_info, address)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert len(result) == 3
    assert isinstance(result[1], int)
    assert isinstance(result[2], int)


def test_get_profile_uid_param(xorp_and_tredy_hosts, rpc_user):
    """
    Тест json-rpc-api метода getProfile. Создаем пользователя.
    Вызываем метод с одним параметром uid.
    """
    login, password = rpc_user
    _, uid = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'getProfile'
    params = '"{}", "{}", "{}", "{}", "{}"'.format(uid, '', '', '', '')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert len(result) == 3
    assert isinstance(result[1], int)
    assert isinstance(result[2], int)


def test_update_nic(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода updateNic. Создаем пользователя.
    Запрашиваем ip пользователя.
    Запрашиваем id дефолтного профиля пользователя.
    Апдейтим айпишник и валидируем ответ.
    При локальном запуске тестов может возникнуть конфликт привязки ip-адреса
    ввиду того, что у кого-либо из сотрудников может быть привязка офисного айпишника
    к профилю. На платформе CI/CD подобной ошибки быть не должно.
    """
    login, password = rpc_user
    hostname = 'SkyDNSAgent'

    ip_address = get_myip(xorp_and_tredy_hosts, login, password)
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'updateNic'
    params = '{}, "{}"'.format(profile_id, hostname)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result == ip_address


@pytest.mark.parametrize('xorp_and_tredy_hosts',
    [pytest.param('xorp_host', marks=pytest.mark.xfail), 'tredy_host'],
    # Xfail - из-за ожидаемой ошибки 500 на xorp. #1919
    indirect=["xorp_and_tredy_hosts"],
)
def test_preset_list(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода presetList. Создаем пользователя. Запрашиваем id
    дефолтного профиля пользователя.
    Запрашиваем стандартные настройки пользователя и валидируем их.
    """
    login, password = rpc_user
    expected_preset_kids = {
        'is_custom': False, 'is_combine': True, 'name': 'Kids', 'icon': 'kids',
        'all_cats': [3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 26],
        'white_list_only': False, 'safe_search_enabled': True, 'block_ads': False,
        'safe_youtube_enabled': True, 'id': 23, 'block_unknown_sites': False,
        'description': 'Block Illegal Activity, Adult Related, Ads, Torrent & P2P, Chats & Messenger, '
        'Weapons websites. Force Safe Search and Youtube Restricted Mode.'
    }
    expected_preset_block_all = {
        'is_custom': False, 'is_combine': False, 'name': 'Block All', 'icon': 'block_all', 'all_cats': [],
        'white_list_only': False, 'safe_search_enabled': False, 'block_ads': False, 'safe_youtube_enabled': False,
        'id': 21, 'block_unknown_sites': False, 'description': 'Block all, no internet.'
    }
    expected_preset_allow_all = {
        'is_custom': False, 'is_combine': False, 'name': 'Allow All', 'icon': 'allow_all', 'all_cats': [],
        'white_list_only': False, 'safe_search_enabled': False, 'block_ads': False, 'safe_youtube_enabled': False,
        'id': 22, 'block_unknown_sites': False, 'description': 'Nothing blocked.'
    }
    expected_preset_custom = {
        'is_custom': True, 'is_combine': False, 'name': 'Custom', 'icon': 'custom',
        'all_cats': [65, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], 'white_list_only': False,
        'safe_search_enabled': False, 'block_ads': False, 'safe_youtube_enabled': False, 'id': None,
        'block_unknown_sites': False, 'description': None
    }

    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'presetList'
    params = '{}, "{}"'.format(profile_id, 'en')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    result = json.loads(result)
    result[3]['id'] = None
    # Так как id в preset_custom меняется у каждого пользователя, выставляем его значение в None

    assert len(result) == 4
    assert expected_preset_kids == result[0]
    assert expected_preset_block_all == result[1]
    assert expected_preset_allow_all == result[2]
    assert expected_preset_custom == result[3]


def test_set_profile(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода setProfile.
    Создаем пользователя. Создаем пользователю профиль.
    Генерируем UID. Меняем текущий профиль фильтрации.
    """
    login, password = rpc_user
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    _, uid = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'setProfile'
    params = '"{}", {}'.format(uid, profile_id)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_domains(xorp_and_tredy_hosts, rpc_user):
    """
    Тест проверяет апи-метод domains.
    Создаем пользователя, получаем profile_id.
    Делаем запросы с тремя разными параметрами.
    param : white, black, alias
    """
    login, password = rpc_user
    params = ['white', 'black', 'alias']
    method = 'domains'
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    for param in params:
        params = '{}, "{}"'.format(profile_id, param)
        data = DATA_PATTERN.format(method=method, params=params)
        response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

        try:
            result = response.json()['result']
        except KeyError:
            pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

        assert not result, 'Ошибка параметра result'


def test_feedback(xorp_and_tredy_hosts, rpc_user):
    """
    Тест проверяет апи-метод feedback.
    Создаем пользователя. Отправляем сообщение-фидбэк от его имени.
    Валидируем ответ.
    """
    login, password = rpc_user
    title = 'my_title'
    message = 'my_message'

    method = 'feedback'
    params = '"{}", "{}"'.format(title, message)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_set_preset_safe_search_enabled(xorp_and_tredy_hosts, rpc_user):
    """
    Тест проверяет апи-метод setPresetSafeSearchEnabled.
    Создаем пользователя, получаем profile_id.
    Проверяем метод с двумя флагами: true и false.
    Валидируем ответы.

    Для свежесозданного пользователя пресеты не установлены.
    Пока нет инструментов их настройки, проверять можем только по факту отсутствия пресета.
    Нужно либо заводить в базе статичного юзера с константными настройками пресетов
    (настройки юзера plantest могут быть изменены в другом тесте),
    либо делать инструмент заведения пресетов для пользователя.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    flags = ['true', 'false']
    method = 'setPresetSafeSearchEnabled'

    for flag in flags:
        params = '{}, "{}"'.format(profile_id, flag)
        data = DATA_PATTERN.format(method=method, params=params)
        response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

        try:
            error = response.json()['error']
        except KeyError:
            pytest.fail('Ошибка поиска значения по ключу "error" в ответе: {}'.format(response.json()))

        assert error['message'] == 'JsonRpcInvalidParamsError: Preset does not Exist'


def test_set_preset_safe_youtube_enabled(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода setPresetSafeYoutubeEnabled.
    Создаем пользователя, получаем profile_id.
    Проверяем метод с двумя флагами: true и false.
    Валидируем ответы.

    Для свежесозданного пользователя пресеты не установлены.
    Пока нет инструментов их настройки, проверять можем только по факту отсутствия пресета.
    Нужно либо заводить в базе статичного юзера с константными настройками пресетов
    (настройки юзера plantest могут быть изменены в другом тесте),
    либо делать инструмент заведения пресетов для пользователя
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    flags = ['true', 'false']
    method = 'setPresetSafeYoutubeEnabled'

    for flag in flags:
        params = '{}, "{}", "{}"'.format(profile_id, 'preset', flag)
        data = DATA_PATTERN.format(method=method, params=params)
        response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

        try:
            error = response.json()['error']
        except KeyError:
            pytest.fail('Ошибка поиска значения по ключу "error" в ответе: {}'.format(response.json()))

        assert error['message'] == 'JsonRpcInvalidParamsError: Preset does not Exist'


def test_set_filter_category_exist(xorp_and_tredy_hosts, rpc_user):
    """
    Тест проверяет апи-метод setFilterCat.
    Рассматриваем добавление существующей  категории.
    Создаем пользователя, получаем profile_id дефолтного профиля.
    Делаем запрос, валидируем ответ.
    [2, 59+1] - диапазон валидных категорий.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    cat_num = randint(2, 59+1)

    method = 'setFilterCat'
    params = '{}, {}, {}'.format(profile_id, cat_num, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_set_filter_category_not_exist(xorp_and_tredy_hosts, rpc_user):
    """
    Тест проверяет апи-метод setFilterCat.
    Рассматриваем  добавление несуществующей категории.
    Создаем пользователя, получаем profile_id дефолтного профиля.
    Делаем запрос, валидируем ответ.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'setFilterCat'
    params = '{}, {}, {}'.format(profile_id, 1, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        error = response.json()['error']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "error" в ответе: {}'.format(response.json()))

    assert error['message'] == 'JsonRpcInvalidParamsError: Category does not exist'


def test_set_filter_cats(xorp_and_tredy_hosts, rpc_user):
    """
    Тест проверяет апи-метод setFilterCats.
    Рассматриваем 2 кейса: добавление существующей и несуществующей категорий
    Создаем пользователя, получаем profile_id дефолтного профиля.
    Делаем запрос, валидируем ответ.
    """
    login, password = rpc_user
    categories_list_ok = [randint(2, 60), randint(2, 60), ]
    categories_list_error = [randint(2, 60), 999, ]

    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    method = 'setFilterCats'

    # Кейс1. Добавление существующей категории
    params = '{}, {}'.format(profile_id, categories_list_ok)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    for category in result:
        assert category in categories_list_ok

    # Кейс2. Добавление несуществующей категории
    params = '{}, {}'.format(profile_id, categories_list_error)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        error = response.json()['error']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "error" в ответе: {}'.format(response.json()))

    assert error['message'] == 'JsonRpcInvalidParamsError: Category does not exist'


def test_add_domain(xorp_and_tredy_hosts, rpc_user):
    """
    Тест проверяет апи-метод addDomain.
    На каждый параметр рассматривается отдельный кейс.
    Создаем пользователя, получаем profile_id дефолтного профиля.
    Делаем запросы, валидируем ответы.
    params : black, white, alias
    """
    login, password = rpc_user
    # Добавлять мы можем только разные домены
    values = {
        'black': 'black.domain.ru',
        'white': 'white.domain.ru',
        'alias': 'www.alias.ru',
        'ip': generate_public_ip()
    }
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    method = 'addDomain'

    # Case1. Black
    params = '{}, "{}", "{}"'.format(profile_id, 'black', values['black'])
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)

    # Case2. White
    params = '{}, "{}", "{}"'.format(profile_id, 'white', values['white'])
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)

    # Case3. Alias
    params = '{}, "{}", "{}", "{}"'.format(profile_id, 'alias', values['alias'], values['ip'])
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)


def test_remove_domain(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода removeDomain. Создаем пользователя. Последовательно
    рассматриваем 3 кейса по добавлению/последующему удалению на/с дефолтный профиль
    разных доменов в разные списки (params : black, white, alias)
    id домена получаем из метода addDomain
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    # Добавлять мы можем только разные домены
    values = {
        'black': generate_login_password()[0].replace('@', ''),
        'white': generate_login_password()[0].replace('@', ''),
        'alias': generate_login_password()[0].replace('@', ''),
        'ip': generate_public_ip()
    }
    method_add = 'addDomain'
    method_remove = 'removeDomain'

    # Case1. Black
    params = '{}, "{}", "{}"'.format(profile_id, 'black', values['black'])
    data = DATA_PATTERN.format(method=method_add, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)

    domain_id = result
    params = '{}, "{}", {}'.format(profile_id, 'black', domain_id)
    data = DATA_PATTERN.format(method=method_remove, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    # Case2. White
    params = '{}, "{}", "{}"'.format(profile_id, 'white', values['white'])
    data = DATA_PATTERN.format(method=method_add, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)

    domain_id = result
    params = '{}, "{}", {}'.format(profile_id, 'white', domain_id)
    data = DATA_PATTERN.format(method=method_remove, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    # Case3. Alias
    params = '{}, "{}", "{}", "{}"'.format(profile_id, 'alias', values['alias'], values['ip'])
    data = DATA_PATTERN.format(method=method_add, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)

    domain_id = result
    params = '{}, "{}", {}'.format(profile_id, 'alias', domain_id)
    data = DATA_PATTERN.format(method=method_remove, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_clear_domains(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода clearDomains. Создаем пользователя.
    Получаем айдишник дефолтного профиля.
    Добавляем домены в списки. Очищаем списки.
    Рассматриваются 3 кейса: black/white и alias.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    values = {
        'black': generate_login_password()[0].replace('@', ''),
        'white': generate_login_password()[0].replace('@', ''),
        'alias': generate_login_password()[0].replace('@', ''),
        'ip': generate_public_ip()
    }
    method_add = 'addDomain'
    method_clear = 'clearDomains'

    # Case1. Добавляем данные в black-list и очищаем список
    params = '{}, "{}", "{}"'.format(profile_id, 'black', values['black'])
    data = DATA_PATTERN.format(method=method_add, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)

    params = '{}, "{}"'.format(profile_id, 'black')
    data = DATA_PATTERN.format(method=method_clear, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    # Case2. Добавляем данные в white-list и очищаем список
    params = '{}, "{}", "{}"'.format(profile_id, 'white', values['white'])
    data = DATA_PATTERN.format(method=method_add, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)

    params = '{}, "{}"'.format(profile_id, 'white')
    data = DATA_PATTERN.format(method=method_clear, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    # Case3. Добавляем данные в alias-list и очищаем список
    params = '{}, "{}", "{}", "{}"'.format(profile_id, 'alias', values['alias'], values['ip'])
    data = DATA_PATTERN.format(method=method_add, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert isinstance(result, int)

    params = '{}, "{}"'.format(profile_id, 'alias')
    data = DATA_PATTERN.format(method=method_clear, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_set_white_list_only(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода setWhiteListOnly.
    Создаем пользователя. Получаем айдишник дефолтного профиля.
    Устанавливаем фильтрацию "Только по белому списку".
    Валидируем результат.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'setWhiteListOnly'
    params = '{}, "{}"'.format(profile_id, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    params = '{}, "{}"'.format(profile_id, '')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_set_safe_search_enabled(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода setSafeSearchEnabled.
    Создаем пользователя. Получаем айдишник дефолтного профиля.
    Устанавливаем SafeSearch в активный режим.
    Валидируем результат.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'setSafeSearchEnabled'
    params = '{}, "{}"'.format(profile_id, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    params = '{}, "{}"'.format(profile_id, '')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_set_safe_youtube_enabled(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода setSafeYoutubeEnabled.
    Создаем пользователя. Получаем айдишник дефолтного профиля.
    Устанавливаем SafeYoutube в активный режим.
    Валидируем результат.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    method = 'setSafeYoutubeEnabled'

    params = '{}, "{}"'.format(profile_id, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    params = '{}, "{}"'.format(profile_id, '')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_set_block_unknown_enabled(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода setBlockUnknownEnabled.
    Создаем пользователя. Получаем айдишник дефолтного профиля.
    Устанавливаем BlockUnknown в активный режим.
    Валидируем результат.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    method = 'setBlockUnknownEnabled'

    params = '{}, "{}"'.format(profile_id, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    params = '{}, "{}"'.format(profile_id, '')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_set_schedule_enabled(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода setScheduleEnabled.
    Создаем пользователя и активируем расписание.
    Рассматриваются 2 кейса: для дефолтного и тестового профилей.
    """
    login, password = rpc_user
    method = 'setScheduleEnabled'

    # Кейс 1. Проверка метода для дефолтного метода
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    message = 'JsonRpcInvalidParamsError: Default profile is not allowed'
    params = '{}, {}'.format(profile_id, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        error = response.json()['error']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "error" в ответе: {}'.format(response.json()))

    assert error['message'] == message

    # Кейс 2. Создаем тестовый профиль и активируем на нем расписание
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    params = '{}, {}'.format(profile_id, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result


def test_set_schedule(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода setSchedule.
    Создаем пользователя и получаем айдишник дефолтного профиля.
    Устанавливаем для дефолтного профиля расписани для фильтрации.
    Валидируем ответ.
    """
    login, password = rpc_user
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    # Временные интервалы выбраны рандомно и не влияют на результат тестирования
    schedule = '[[0, true], [1980, false], [3000, true], [3780, false]]'

    method = 'setSchedule'
    params = '{}, {}'.format(profile_id, schedule)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result


def test_multi_schedule(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода multiSchedule.
    Создаем пользователя.
    Рассматривается 2 кейса:
    Кейс1. Запрашиваем айдишник дефолтного профиля.
    Запрашиваем расписание для дефолтного профиля. Валидируем ответ.
    Кейс 2. Создаем прользователю профиль.
    Устанавливаем расписание для профиля. Проверяем результат
    """
    login, password = rpc_user

    # Кейс1. Запрашиваем расписание для дефолтного профиля
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method_multi = 'multiSchedule'
    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method_multi, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'

    # Кейс2. Создаем профиль. Устанавливаем расписание для профиля. Проверяем результат
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    schedule = '[[0, true], [1980, false], [3000, true], [3780, false]]'

    method = 'setSchedule'
    params = '{}, {}'.format(profile_id, schedule)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result

    method = 'setScheduleEnabled'
    params = '{}, {}'.format(profile_id, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result

    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method_multi, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result == [[0, True], [1980, False], [3000, True], [3780, False]]


def test_profile_schedule_activity(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода profileScheduleActivity.
    запрашиваем ИД профиля
    Создаем пользователя.
    Рассматривается 2 кейса:
    Кейс1. Запрашиваем айдишник дефолтного профиля.
    Запрашиваем активность по расписанию для дефолтного профиля. Валидируем ответ.
    Кейс 2. Создаем прользователю профиль.
    Запрашиваем активность по расписанию для тестового профиля. Проверяем результат.
    """
    login, password = rpc_user
    method_activity = 'profileScheduleActivity'

    # Кейс1. Определяем айдишник дефолтного профиля и делаем запрос
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method_activity, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result == [True, -1]

    # Кейс 2. Делаем профиль, накатываем на него расписание и делаем запрос.
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    schedule = '[[0, true], [1980, false], [3000, true], [3780, false]]'

    method = 'setSchedule'
    params = '{}, {}'.format(profile_id, schedule)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    method = 'setScheduleEnabled'
    params = '{}, {}'.format(profile_id, 'true')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert result

    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method_activity, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    # Параметры True, False для профиля зависит от времени запуска теста
    # (включена фильтрация по расписанию для данного профиля или нет)
    assert result[0] in [True, False]
    assert isinstance(result[1], int)


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_amount", [
        ('xorp_host', 48),
        ('tredy_host', 3),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_set_active_presets(xorp_and_tredy_hosts, expected_amount, rpc_user):
    """
    Тест апи-метода setActivePresets.
    Создаем пользователя. Запрашиваем айдишник дефолтного профиля.
    Рассматриваем 2 Кейса:
    Кейс1. Проверка несуществующего пресета.
    Кейс2. Поочерёдно проверяем все доступные пресеты.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    method = 'setActivePresets'

    # Кейс 1. Проверка несуществующего пресета
    params = '{}, {}'.format(profile_id, [0])
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        error = response.json()['error']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "error" в ответе: {}'.format(response.json()))

    assert error['message'] == 'JsonRpcInvalidParamsError: Preset does not Exist'

    # Кейс 2. Поочерёдно проверяем доступные пресеты
    for preset_id in range(1, expected_amount):
        params = '{}, {}'.format(profile_id, [preset_id])
        data = DATA_PATTERN.format(method=method, params=params)
        response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

        try:
            result = response.json()['result']
        except KeyError:
            pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

        assert not result, 'Ошибка параметра result'


def test_get_active_preset_list(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода getActivePresetList.
    Создаем пользователя. Запрашиваем айдишник дефолтного профиля.
    Получаем список активных пресетов. Валидируем ответ.
    """
    login, password = rpc_user
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)

    method = 'getActivePresetList'
    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    preset_id = json.loads(result)[0]

    assert isinstance(preset_id, int)


def test_get_categories_daily_stats(xorp_and_tredy_hosts, rpc_user):
    """
    Тест апи-метода getCategoriesDailyStats.
    Создаем пользователя. Запрашиваем айдишник дефолтного профиля.
    Рассматривается 3 Кейса:
    Кейс 1. Делаем запрос для дефолтного профиля
    Кейс 2. Создаем профиль и делаем запрос для него
    Кейс 3. Делаем запрос для созданного профиля со всеми доступными параметрами
    """
    login, password = rpc_user
    method = 'getCategoriesDailyStats'

    # Кейс 1. Делаем запрос для дефолтного профиля
    profile_id, _ = get_default_profile_and_uid(xorp_and_tredy_hosts, login, password)
    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result в ответе: {}'.format(response.json())

    # Кейс 2. Создаем профиль и делаем запрос для него
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    params = '{}'.format(profile_id)
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе')

    assert not result, 'Ошибка параметра result в ответе: {}'.format(response.json())

    # Кейс 3. Делаем запрос для созданного профиля со всеми доступными параметрами
    params = '{}, "{}", {}'.format(profile_id, 'en', '[3, 4, 23]')
    data = DATA_PATTERN.format(method=method, params=params)
    response = make_requests_post(xorp_and_tredy_hosts, data, auth=(login, password))

    try:
        result = response.json()['result']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "result" в ответе: {}'.format(response.json()))

    assert not result, 'Ошибка параметра result'


def test_no_traceback_rpc(xorp_and_tredy_hosts):
    """
    Негативный тест-кейс на проверку отсутствия трейсбэка
    с указанием доступных тарифов. Запрос без авторизации.
    Выставлен таймаут запроса 10 секунд.
    """
    method = 'non_existing_method'
    params = ''
    data = DATA_PATTERN.format(method=method, params=params)

    url = '{host}/api/json/v2'.format(host=xorp_and_tredy_hosts)

    try:
        response = requests.post(url, data=data, timeout=10)
    except ReadTimeout:
        pytest.fail('Время установки соединения превышает предельно допустимое значение')

    assert response.status_code == 404, error_message

    try:
        error = response.json()['error']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "error" в ответе: {}'.format(response.json()))

    error_message = (
            'Expected Status Code is 404, \n'
            'but we`ve got {code} on {url} \n'
            'with data_params: {data}'
        ).format(code=response.status_code, url=url, data=data)

    assert error['name'] == 'JsonRpcMethodNotFoundError'
    assert 'Available methods' not in response.text
