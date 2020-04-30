import json
import pytest
import urllib3

from settings import API_PUBLIC_KEY
from website_tests.utils import (
    generate_login_password, get_plan, make_request, make_verification,
    generate_public_ip, create_profile, create_user,
)


pytestmark = pytest.mark.usefixtures('disable_request_warnings')


XORP_PLANS = {
    'SCHOOL': 'Школа',
    'PREMIUM': 'Домашний',
    'BUSINESS': 'Бизнес',
}

TREDY_PLANS = {
    'PREMIUM': 'Safe@Home',
    'ENTERPRISE': 'Enterprise',
    'EDU': 'Education',
    'BUSINESS-5': 'Safe@Office 5',
    'BUSINESS-10': 'Safe@Office 10',
    'BUSINESS-25': 'Safe@Office 25',
    'BUSINESS-50': 'Safe@Office 50',
    'BUSINESS-75': 'Safe@Office 75',
    'BUSINESS-100': 'Safe@Office 100',
    'WIFI': 'HotSpot Advanced Edition',
    'WIFI-1': 'HotSpot Edition 1',
    'WIFI-2': 'HotSpot Edition 2',
    'WIFI-3': 'HotSpot Edition 3',
    'WIFI-4': 'HotSpot Edition 4',
    'WIFI-5': 'HotSpot Edition 5',
    'WIFI-10': 'HotSpot Edition 10',
    'NONPROFIT': 'Nonprofit'
}


def test_subscribe_user(xorp_and_tredy_hosts):
    """
    Тест проверяет метод регистрации пользователя.
    Создаем пользователя с двумя обязательными и двумя необязательными
    параметрами.
    """
    login, password = generate_login_password()
    full_subscribe_params = {
        'key': API_PUBLIC_KEY,
        'login': login,
        'password': password,
        'email': login,
        # Привязка к конкретной таймзоне не сказывается на результатах теста
        'timezone': 'Asia/Yekaterinburg',
        }
    response = make_request(xorp_and_tredy_hosts, 'subscribe', full_subscribe_params)
    make_verification(response)


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_plans", [
        ('xorp_host', XORP_PLANS),
        ('tredy_host', TREDY_PLANS),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_subscribe_plans(xorp_and_tredy_hosts, expected_plans):
    """
    Тест проверяет метод по получению списка доступных тарифов
    для создания/изменения пользователя реселлером.
    """
    params = {'key': API_PUBLIC_KEY}
    response = make_request(xorp_and_tredy_hosts, 'subscribe_plans', params)
    make_verification(response)

    try:
        subscribe_plans = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert subscribe_plans == expected_plans


def test_deactivate(xorp_and_tredy_hosts):
    """
    Тест проверяет метод деактивации пользователя.
    Создается активный пользователь, который деактивируется.
    """
    login, password = generate_login_password()
    deactivation_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    create_user(xorp_and_tredy_hosts, login, password)
    response = make_request(xorp_and_tredy_hosts, 'deactivate', deactivation_params)
    make_verification(response)


def test_activate(xorp_and_tredy_hosts):
    """
    Тест проверяет метод активации пользователя.
    Сперва создается активный пользователь, который деактивируется.
    Затем вызывается api-метод активации для неактивного пользователя.
    """
    login, password = generate_login_password()
    params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    create_user(xorp_and_tredy_hosts, login, password)
    response = make_request(xorp_and_tredy_hosts, 'deactivate', params)
    make_verification(response)
    response = make_request(xorp_and_tredy_hosts, 'activate', params)
    make_verification(response)


def test_update_email(xorp_and_tredy_hosts):
    """
    Тест проверяет метод обновления email пользователя.
    Создается пользователь с почтой. Почта пользователя обновляется.
    """
    login, password = generate_login_password()
    # К новой почте добавляем префикс для исключения совпадений при параллельном запуске тестов
    new_email = 'new_' + login
    registration_params = {
        'key': API_PUBLIC_KEY,
        'login': login,
        'password': password,
        'email': login,
    }
    updating_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'email': new_email,
    }
    response = make_request(xorp_and_tredy_hosts, 'subscribe', registration_params)
    make_verification(response)
    response = make_request(xorp_and_tredy_hosts, 'update_email', updating_params)
    make_verification(response)


def test_update_password(xorp_and_tredy_hosts):
    """
    Тест проверяет метод обновления пароля пользователя.
    Создается пользователь. Пароль пользователя обновляется.
    """
    login, password = generate_login_password()
    _, new_password = generate_login_password()
    updating_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'password': new_password,
    }
    create_user(xorp_and_tredy_hosts, login, password)
    response = make_request(xorp_and_tredy_hosts, 'update_password', updating_params)
    make_verification(response)


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_plans", [
        ('xorp_host', XORP_PLANS),
        ('tredy_host', TREDY_PLANS),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_prolongate_mandatory(xorp_and_tredy_hosts, expected_plans):
    """
    Тест проверяет метод включения или изменения платного тарифа для пользователя
    Создается пользователь. Вызываем для пользователя метод prolongate c одним обязательным параметром.
    Валидируем полученный результат.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    mandatory_prolongate_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    # Включаем для пользователя платный тариф. Если по умолчанию у провайдера создается пользователь
    # с платным тарифом, то метод все равно отработает корректно.
    response = make_request(xorp_and_tredy_hosts, 'prolongate', mandatory_prolongate_params)
    make_verification(response)
    result = get_plan(xorp_and_tredy_hosts, login, password)

    assert result.get('name') == expected_plans['PREMIUM']


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_plans", [
        ('xorp_host', XORP_PLANS),
        ('tredy_host', TREDY_PLANS),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_prolongate_full(xorp_and_tredy_hosts, expected_plans):
    """
    Тест проверяет метод включения или изменения платного тарифа для пользователя
    Создается пользователь. Вызываем для пользователя метод prolongate c двумя параметрами.
    Подключается тариф, передаваемый необязательным параметром.
    Валидируем полученный результат.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    for plan in expected_plans.keys():
        full_prolongate_params = {
            'key': API_PUBLIC_KEY,
            'ident': login,
            'plan': plan,
        }
        response = make_request(xorp_and_tredy_hosts, 'prolongate', full_prolongate_params)
        make_verification(response)
        result = get_plan(xorp_and_tredy_hosts, login, password)

        assert result.get('name') == expected_plans[plan]


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_plans", [
        ('xorp_host', XORP_PLANS),
        ('tredy_host', TREDY_PLANS),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_unsubscribe(xorp_and_tredy_hosts, expected_plans):
    """
    Тест проверяет метод отключения у пользователя платного тарифа.
    Создается пользователь, подключаем ему платный тариф.
    Проверяем, что тариф подключился. Отключаем пользователю тариф.
    Проверям, что тариф отключился.
    """
    login, password = generate_login_password()
    mandatory_prolongate_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    create_user(xorp_and_tredy_hosts, login, password)
    result = get_plan(xorp_and_tredy_hosts, login, password)

    assert result.get('name') == expected_plans['PREMIUM']

    response = make_request(xorp_and_tredy_hosts, 'unsubscribe', mandatory_prolongate_params)
    make_verification(response)
    result = get_plan(xorp_and_tredy_hosts, login, password)

    assert result.get('name') == 'FREE'


def test_subscription_info(xorp_and_tredy_hosts):
    """
    Тест проверяет метод получения информации о подписке.
    Api-методы не поддерживают опционал изменения даты окончания подписки.
    Пользователи создаются с неограниченно действующей подпиской для всех тарифов.
    Создается пользователь с платным тарифом.
    Проверяется неограниченность срока действия тарифа.
    """
    login, password = generate_login_password()
    info_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    create_user(xorp_and_tredy_hosts, login, password)
    response = make_request(xorp_and_tredy_hosts, 'subscription_info', info_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    date_end = data.get('date_end')

    assert not date_end


def test_profiles(xorp_and_tredy_hosts):
    """
    Тест проверяет метод получения информации о профилях пользователя.
    Cоздается пользователь. Запрашиваем и валидируем его профиль.
    """
    login, password = generate_login_password()
    profiles_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    create_user(xorp_and_tredy_hosts, login, password)
    response = make_request(xorp_and_tredy_hosts, 'profiles', profiles_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    profile_id = eval([key for key in data.keys()][0])
    profile_name = data.values()

    assert isinstance(profile_id, int)
    assert 'Default' in profile_name


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, expected_plan", [
        ('xorp_host', 'BUSINESS'),
        ('tredy_host', 'ENTERPRISE'),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_update_profile(xorp_and_tredy_hosts, expected_plan):
    """
    Тест проверяет метод update_profile.
    Создаем пользователя, делаем для него новый профиль.
    Методом update_profile меняем параметры профиля.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    update_params = {
        'key': API_PUBLIC_KEY,
        'profile_id': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'update_profile', update_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert not data['tls']
    assert data['name'] == 'my_profile_test'

    full_update_params = {
        'key': API_PUBLIC_KEY,
        'profile_id': profile_id,
        'name': 'modified_profile',
        'tls': 'True',
    }
    prolongate_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'plan': expected_plan,
    }
    response = make_request(xorp_and_tredy_hosts, 'prolongate', prolongate_params)
    make_verification(response)
    response = make_request(xorp_and_tredy_hosts, 'update_profile', full_update_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['tls']
    assert data['name'] == 'modified_profile'
    assert data['id'] == int(profile_id)


def test_add_ip_free(xorp_and_tredy_hosts):
    """
    Тест проверяет метод add_ip. Кейс1.
    Создаем пользователя с тарифом FREE и пытаемся добавить ему непубличный ip-адрес.
    Пытаемся добавить пользователю два ip-адреса.
    Первый адрес добавляется, второй не может быть добавлен.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    unsubscribe_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'unsubscribe', unsubscribe_params)
    make_verification(response)

    # Case1
    mandatory_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': '255.255.255.255',
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', mandatory_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['added_addresses'] == [], 'Case1. Добавлен непубличный адрес'

    invalid_adress = data['invalid_adresses'][0]

    assert invalid_adress['255.255.255.255'] == 'This address is not public', \
    'Case1. Адрес отсутствует в invalid_adresses'

    # Case2
    address = generate_public_ip()
    mandatory_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': address,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', mandatory_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['added_addresses'][0] == address, 'Case2. Адрес не добавлен'
    assert 'invalid_adresses' not in data.keys()

    # Case3
    address = generate_public_ip()
    mandatory_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': address,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', mandatory_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['added_addresses'] == [], 'Case3. Добавлен лишний ip-адрес'
    assert address in data['invalid_adresses'][0].keys()
    assert data['invalid_adresses'][0].get(address) == 'The limit is reached', 'Case3. Отсутствует сообщение об ошибке'


def test_add_user_with_the_same_ip(xorp_and_tredy_hosts):
    """
    Тест проверяет метод add_ip. Кейс2.
    Создаем пользователя, добавляем ему ip-адрес.
    Создаем еще одного пользователя и пытаемся добавить ему ip-адрес первого пользователя.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    ip_address = generate_public_ip()
    mandatory_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': ip_address,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', mandatory_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['added_addresses'][0] == ip_address
    assert 'invalid_adresses' not in data.keys()

    new_login, new_password = generate_login_password()
    create_user(xorp_and_tredy_hosts, new_login, new_password)
    # Пытаемся добавить ему адрес, ранее добавленный первому пользователю
    mandatory_params_case_2 = {
        'key': API_PUBLIC_KEY,
        'ident': new_login,
        'ip': ip_address,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', mandatory_params_case_2)
    make_verification(response)

    try:
        data = response.json()['data']
        invalid_adress = data['invalid_adresses'][0]
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['added_addresses'] == []
    assert invalid_adress[ip_address] == 'Address already added to another user'


def test_add_three_ips(xorp_and_tredy_hosts):
    """
    Тест проверяет метод add_ip. Кейс3.
    Создаем пользователя. Создаем ему профиль.
    Пытаемся добавить три ip-адреса с комментариями.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    ip_list = [generate_public_ip() for _ in range(3)]
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    full_ip_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': ip_list,
        'profile': profile_id,
        'comment': ['ip_1_comment', 'ip_2_comment', 'ip_3_comment'],
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', full_ip_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['added_addresses'] == ip_list


def test_clear_ip(xorp_and_tredy_hosts):
    """
    Тест проверяет метод clear_ip.
    Создается пользователь. Добавляем ему ip-адреса.
    Определяем айдишник дефолтного профиля.
    Удаляем добавленные пользователю ip-адреса.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    ip_list = [generate_public_ip() for _ in range(3)]
    ip_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': ip_list,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', ip_params)
    make_verification(response)
    profiles_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'profiles', profiles_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    # Инвертируем словарь для поиска айдишника профиля по его названию
    profile_id = [key for key, value in data.items() if value == 'Default'][0]

    clear_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'profile': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'clear_ip', clear_params)
    make_verification(response)
    response = make_request(xorp_and_tredy_hosts, 'list_ip', clear_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert 'ip' in data
    assert not data['ip']


def test_list_ip_compulsory(xorp_and_tredy_hosts):
    """
    Тест проверяет метод list_ip с одним обязательным параметром.
    Создается пользователь. Добавляем ему ip-адреса на дефолтный профиль.
    Создаем пользователю второй профиль. Добавляем на него ip-адреса.
    Определяем айдишник дефолтного профиля.
    Получаем список ip-адрессов с обоих профилей.
    Валидируем результат запроса.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    default_ip = generate_public_ip()
    ip_for_profile = generate_public_ip()
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    profiles_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'profiles', profiles_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    default_id = eval([key for key, value in data.items() if value == 'Default'][0])

    # Накатываем айпишники на каждый профиль отдельно, т.к. совместно запрос не проходит
    ip_params_default = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': default_ip,
        'comment': 'comment_list_default_ip',
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', ip_params_default)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['added_addresses'][0] == default_ip, 'Адрес не добавлен {}'.format(response.json())

    make_verification(response)
    ip_params_my_profile = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': ip_for_profile,
        'profile': profile_id,
        'comment': 'comment_list_ip_my_profile',
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', ip_params_my_profile)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data['added_addresses'][0] == ip_for_profile, 'Адрес не добавлен {}'.format(response.json())

    make_verification(response)
    list_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'list_ip', list_params)
    make_verification(response)

    try:
        data = response.json()['data']
        default = data['ip'][0]
        profile = data['ip'][1]
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert default['profile'] == int(default_id)
    assert default['comment'] == 'comment_list_default_ip'
    assert default['address'] == default_ip

    assert profile['profile'] == int(profile_id)
    assert profile['comment'] == 'comment_list_ip_my_profile'
    assert profile['address'] == ip_for_profile


def test_list_ip_optional(xorp_and_tredy_hosts):
    """
    Тест проверяет метод list_ip с обязательным и дополнительным параметрами.
    Создается пользователь. Добавляем ему ip-адреса на дефолтный профиль.
    Создаем пользователю второй профиль. Добавляем на него ip-адреса.
    Определяем айдишник дефолтного профиля.
    Получаем список ip-адрессов с обоих профилей.
    Валидируем результат запроса.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    ip_for_profile = generate_public_ip()
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    ip_params_my_profile = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': ip_for_profile,
        'profile': profile_id,
        'comment': 'comment_list_ip_my_profile',
    }
    response = make_request(xorp_and_tredy_hosts, 'add_ip', ip_params_my_profile)
    make_verification(response)
    list_params_full = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'profile': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'list_ip', list_params_full)
    make_verification(response)

    try:
        data = response.json()['data']
        profile = data['ip'][0]
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert profile['profile'] == int(profile_id)
    assert profile['comment'] == 'comment_list_ip_my_profile'
    assert profile['address'] == ip_for_profile


def test_update_ip(xorp_and_tredy_hosts):
    """
    Тест проверяет метод update_ip по добавлению DDNS.
    Кейс1. Создается пользователь. Добавляем ему DDNS.
    Кейс2. Содаем еще одного пользователя. Добавляем ему DDNS пользователя из Кейс1.
    Кейс3. Добавляем пользователю из Кейс2 второй DDNS на дефолтный профиль.
    Кейс4. Создаем пользователю из Кейс2 новый профиль. Добавляем DDNS на новый профиль.
    """
    # Кейс1.
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    public_ip = generate_public_ip()
    update_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': public_ip,
    }
    # Пока нет api-метода для получения списка динамических адресов, валидировать можем только по состоянию ответа
    response = make_request(xorp_and_tredy_hosts, 'update_ip', update_params)

    assert response.status_code == 200, 'Кейс1. Статус-код ответа != 200'
    assert response.json()['status'] == 'ok', 'Кейс1. ' + response.json()['data'].get('message')

    # Кейс2.
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    update_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': public_ip,
    }
    response = make_request(xorp_and_tredy_hosts, 'update_ip', update_params)

    assert response.status_code == 200, 'Кейс2. Статус-код ответа != 200'
    assert response.json()['status'] == 'ok', 'Кейс2. ' + response.json()['data'].get('message')

    # Кейс 3. Последовательно добавляем два разных айпишника, привязывая их к разным хостам на дефолтном профиле
    update_params_first_hostname = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': generate_public_ip(),
        'hostname': 'first_hostname',
    }
    update_params_second_hostname = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': generate_public_ip(),
        'hostname': 'second_hostname',
    }
    response = make_request(xorp_and_tredy_hosts, 'update_ip', update_params_first_hostname)

    assert response.status_code == 200, 'Кейс3.first_hostname. Статус-код ответа != 200'
    assert response.json()['status'] == 'ok', 'Кейс3.first_hostname. ' + response.json()['data'].get('message')

    response = make_request(xorp_and_tredy_hosts, 'update_ip', update_params_second_hostname)

    assert response.status_code == 200, 'Кейс3.second_hostname. Статус-код ответа != 200'
    assert response.json()['status'] == 'ok', 'Кейс3.second_hostname. ' + response.json()['data'].get('message')

    # Кейс4.
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    update_params_profile = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': generate_public_ip(),
        'profile': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'update_ip', update_params_profile)

    assert response.status_code == 200, 'Кейс4. Статус-код ответа != 200'
    assert response.json()['status'] == 'ok', 'Кейс4. ' + response.json()['data'].get('message')


def test_remove_ip(xorp_and_tredy_hosts):
    """
    Тест проверяет метод remove_ip.
    Создаем пользователя, добавляем ему айпишник.
    Удаляем добавленный айпишник. Валидируем по статусу ответа.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    public_ip = generate_public_ip()
    mandatory_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'ip': public_ip,
    }
    response = make_request(xorp_and_tredy_hosts, 'update_ip', mandatory_params)
    make_verification(response)
    response = make_request(xorp_and_tredy_hosts, 'remove_ip', mandatory_params)
    make_verification(response)


@pytest.mark.parametrize('xorp_and_tredy_hosts',

    ['xorp_host', pytest.param('tredy_host', marks=pytest.mark.xfail)],
    # Xfail - из-за ожидаемой ошибке на тредях по добавлению VPN. #1530
    indirect=["xorp_and_tredy_hosts"],
)
def test_add_vpn(xorp_and_tredy_hosts):
    """
    Тест проверяет метод add_vpn.
    Создаем пользователя. Создаем пользователю профиль.
    Добавляем VPN на созданный профиль. Проверяем, что VPN добавился.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    add_vpn_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'name': 'vpn_name',
        'profile_id': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_vpn', add_vpn_params)
    make_verification(response)
    data = response.json()['data']
    expected_keys = [
        'BEGIN CERTIFICATE',
        'END CERTIFICATE',
        'BEGIN PRIVATE KEY',
        'END PRIVATE KEY',
    ]

    assert all(key in data['ovpn'] for key in expected_keys)

    check_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'get_vpn_list', check_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data[0]['profile'] == 'my_profile_test'
    assert data[0]['name'] == 'vpn_name'


@pytest.mark.parametrize('xorp_and_tredy_hosts',

    ['xorp_host', pytest.param('tredy_host', marks=pytest.mark.xfail)],
    # Xfail - из-за ожидаемой ошибке на тредях по добавлению VPN. #1530
    indirect=["xorp_and_tredy_hosts"],
)
def test_clear_vpn_for_profile(xorp_and_tredy_hosts):
    """
    Тест проверяет метод clear_vpn_for_profile.
    Создаем пользователя. Создаем пользователю профиль.
    Добавляем VPN на созданный профиль. Проверяем, что VPN добавился.
    Удаляем VPN c созданного профиля. Проверяем, что VPN удалился.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    add_vpn_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'name': 'vpn_name',
        'profile_id': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_vpn', add_vpn_params)
    make_verification(response)
    data = response.json()['data']
    expected_keys = [
        'BEGIN CERTIFICATE',
        'END CERTIFICATE',
        'BEGIN PRIVATE KEY',
        'END PRIVATE KEY',
    ]

    assert all(key in data['ovpn'] for key in expected_keys)

    check_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'get_vpn_list', check_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data[0]['profile'] == 'my_profile_test'
    assert data[0]['name'] == 'vpn_name'

    clear_params = {
        'key': API_PUBLIC_KEY,
        'profile_id': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'clear_vpn_for_profile', clear_params)
    make_verification(response)
    response = make_request(xorp_and_tredy_hosts, 'get_vpn_list', check_params)
    make_verification(response)

    assert response.json()['data'] == [], 'Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json())


@pytest.mark.parametrize('xorp_and_tredy_hosts',

    ['xorp_host', pytest.param('tredy_host', marks=pytest.mark.xfail)],
    # Xfail - из-за ожидаемой ошибке на тредях по добавлению VPN. #1530
    indirect=["xorp_and_tredy_hosts"],
)
def test_get_vpn_list(xorp_and_tredy_hosts):
    """
    Тест проверяет метод get_vpn_list.
    Создаем пользователя. Добавляем пользователю VPN.
    Получаем список VPN. Валидируем полученный ответ.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    profiles_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'profiles', profiles_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    profile_id = [k for k, v in data.items() if v == 'Default'][0]

    add_vpn_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'name': 'vpn_name',
        'profile_id': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_vpn', add_vpn_params)
    make_verification(response)
    data = response.json()['data']
    expected_keys = [
        'BEGIN CERTIFICATE',
        'END CERTIFICATE',
        'BEGIN PRIVATE KEY',
        'END PRIVATE KEY',
    ]

    assert all(key in data['ovpn'] for key in expected_keys)

    check_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'get_vpn_list', check_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data[0]['profile'] == 'Default'
    assert data[0]['name'] == 'vpn_name'


@pytest.mark.parametrize('xorp_and_tredy_hosts',

    ['xorp_host', pytest.param('tredy_host', marks=pytest.mark.xfail)],
    # Xfail - из-за ожидаемой ошибке на тредях по добавлению VPN. #1530
    indirect=["xorp_and_tredy_hosts"],
)
def test_clear_vpn_for_user(xorp_and_tredy_hosts):
    """
    Тест проверяет метод clear_vpn_for_profile.
    Создаем пользователя. Привязываем VPN к дефолтному профилю.
    Создаем пользователю профиль. Привязываем VPN к созданному профилю.
    Удаляем все VPN. Проверяем, что все VPN удалены.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    profiles_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'profiles', profiles_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    profile_id = [k for k, v in data.items() if v == 'Default'][0]

    add_vpn_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'name': 'vpn_name_default',
        'profile_id': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_vpn', add_vpn_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    expected_keys = [
        'BEGIN CERTIFICATE',
        'END CERTIFICATE',
        'BEGIN PRIVATE KEY',
        'END PRIVATE KEY',
    ]

    assert all(key in data['ovpn'] for key in expected_keys)

    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    add_vpn_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'name': 'vpn_name_my_profile',
        'profile_id': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_vpn', add_vpn_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    expected_keys = [
        'BEGIN CERTIFICATE',
        'END CERTIFICATE',
        'BEGIN PRIVATE KEY',
        'END PRIVATE KEY',
    ]

    assert all(key in data['ovpn'] for key in expected_keys)

    check_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'get_vpn_list', check_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data[0]['profile'] == 'Default'
    assert data[0]['name'] == 'vpn_name_default'
    assert data[1]['profile'] == 'my_profile_test'
    assert data[1]['name'] == 'vpn_name_my_profile'

    response = make_request(xorp_and_tredy_hosts, 'clear_vpn_for_user', check_params)
    make_verification(response)
    response = make_request(xorp_and_tredy_hosts, 'get_vpn_list', check_params)
    make_verification(response)

    assert response.json()['data'] == []


@pytest.mark.parametrize('xorp_and_tredy_hosts',

    ['xorp_host', pytest.param('tredy_host', marks=pytest.mark.xfail)],
    # Xfail - из-за ожидаемой ошибке на тредях по добавлению VPN. #1530
    indirect=["xorp_and_tredy_hosts"],
)
def test_remove_vpn(xorp_and_tredy_hosts):
    """
    Тест проверяет метод remove_vpn.
    Создаем пользователя. Добавляем пользователю VPN.
    Запрашиваем айдишник созданного VPN.
    Удаляем VPN. Проверяем факт удаления VPN.
    """
    login, password = generate_login_password()
    create_user(xorp_and_tredy_hosts, login, password)
    profiles_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'profiles', profiles_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    profile_id = [k for k, v in data.items() if v == 'Default'][0]

    add_vpn_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
        'name': 'vpn_name',
        'profile_id': profile_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'add_vpn', add_vpn_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    expected_keys = [
        'BEGIN CERTIFICATE',
        'END CERTIFICATE',
        'BEGIN PRIVATE KEY',
        'END PRIVATE KEY',
    ]

    assert all(key in data['ovpn'] for key in expected_keys)

    check_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'get_vpn_list', check_params)
    make_verification(response)

    try:
        data = response.json()['data']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "data" в ответе: {}'.format(response.json()))

    assert data[0]['profile'] == 'Default'
    assert data[0]['name'] == 'vpn_name'

    vpn_id = data[0]['id']
    remove_param = {
        'key': API_PUBLIC_KEY,
        'id': vpn_id,
    }
    response = make_request(xorp_and_tredy_hosts, 'remove_vpn', remove_param)
    make_verification(response)
    check_params = {
        'key': API_PUBLIC_KEY,
        'ident': login,
    }
    response = make_request(xorp_and_tredy_hosts, 'get_vpn_list', check_params)
    make_verification(response)

    assert response.json()['data'] == []


@pytest.mark.parametrize(
    "xorp_and_tredy_hosts, nat_ip", [
        ('xorp_host', '193.58.251.101'),
        ('tredy_host', '195.46.39.101'),
    ],
    indirect=["xorp_and_tredy_hosts"]
)
def test_update_nat(xorp_and_tredy_hosts, nat_ip):
    """
    Тест проверяет метод update_nat.
    Создаем пользователя. Добавляем ему профиль.
    Привязываем созданный профиль к DNS адресу.
    """
    login, password = generate_login_password()
    # Используем для теста первый адрес из списка
    create_user(xorp_and_tredy_hosts, login, password)
    profile_id = create_profile(xorp_and_tredy_hosts, login, password)
    update_params = {
        'key': API_PUBLIC_KEY,
        'profile_id': profile_id,
        'address': nat_ip,
    }
    response = make_request(xorp_and_tredy_hosts, 'update_nat', update_params)
    make_verification(response)


def test_no_traceback_provider(xorp_and_tredy_hosts):
    """
    Негативный тест-кейс на проверку отсутствия трейсбэка
    с указанием доступных тарифов.
    """
    params = {'key': API_PUBLIC_KEY}
    response = make_request(xorp_and_tredy_hosts, 'non_existing_method', params)

    error_message = 'Expected Status Code is 200, but we get {code}'.format(code=response.status_code)

    assert response.status_code == 200, error_message

    try:
        error = response.json()['error']
    except KeyError:
        pytest.fail('Ошибка поиска значения по ключу "error" в ответе: {}'.format(response.json()))

    message = error['message']
    searching_pattern = 'Available methods'
    response_string = response.text

    assert message == 'Method not found'
    assert searching_pattern not in response_string
