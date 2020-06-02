"""
Module with API-tests
"""
import json
import pytest
import requests
from requests.exceptions import ConnectionError, ReadTimeout

from utils import generate_email_name


URL = 'http://localhost:4000/subscriptions'
TIME_VALUES = ['5d', '12h', '3d4h']


@pytest.fixture()
def get_subscriber_test_data():
    """
    fixture for get_subscriber test.
    """
    # Setup add three subscriptions to the main list.
    for _ in range(3):
        email, name = generate_email_name()

        payload = {
            'email': f'{email}',
            'name': f'{name}',
            'time': choice(TIME_VALUES)
        }
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.request("POST", URL, headers=headers, data=json.dumps(payload), timeout=5)
        except (ReadTimeout, ConnectionError):
            print('Connection setup time exceeds maximum permissible value')
            assert 0
        assert response.status_code == 200

    yield

    # Teardown
    try:
        response = requests.delete(URL, timeout=5)
    except (ReadTimeout, ConnectionError):
        print('Connection setup time exceeds maximum permissible value')
        assert 0


@pytest.fixture()
def delete_subscriber_test_data():
    """
    fixture for delete test.
    """
    # Setup add three subscriptions to the main list
    headers = {'Content-Type': 'application/json'}

    for _ in range(3):
        email, name = generate_email_name()

        payload = {
            'email': f'{email}',
            'name': f'{name}',
            'time': choice(TIME_VALUES)
        }

        try:
            response = requests.request("POST", URL, headers=headers, data=json.dumps(payload), timeout=5)
        except (ReadTimeout, ConnectionError):
            print('Connection setup time exceeds maximum permissible value')
            assert 0
        assert response.status_code == 200

    # to know exactly how many items in list
    try:
        response = requests.get(URL)
    except (ReadTimeout, ConnectionError):
        print('Connection setup time exceeds maximum permissible value')
        assert 0
    assert response.status_code == 200

    items = len(response.json())

    yield items


def test_add_subscriber():
    """
    check api method for adding a new subscription.
    """
    email, name = generate_email_name()
    payload = {
        'email': f'{email}',
        'name': f'{name}',
        'time': choice(TIME_VALUES)
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.request("POST", URL, headers=headers, data=json.dumps(payload), timeout=5)
    except (ReadTimeout, ConnectionError):
        pytest.fail('Connection setup time exceeds maximum permissible value')

    try:
        id = response.json()['id']
    except KeyError:
        pytest.fail('During id getting KeyError has occured')

    assert response.status_code == 200

    # verification of addition a new subscription
    response = requests.get(URL)
    subscriptions = response.json()
    flag = False

    for item in subscriptions:
        if item['id'] == id:
            flag = True

    assert flag, f'Subscription with params: email={email}, name={name} was not added'


def test_get_subscriber(get_subscriber_test_data):
    """
    check api method for getting a subscriptionlist.
    """
    try:
        response = requests.get(URL)
    except (ReadTimeout, ConnectionError):
        pytest.fail('Connection setup time exceeds maximum permissible value')

    assert response.status_code == 200
    assert len(response.json()) >= 3


def test_delete_subscriber(delete_subscriber_test_data):
    """
    check api method for deleting subscriptions from list.
    """
    try:
        response = requests.delete(URL)
    except (ReadTimeout, ConnectionError):
        pytest.fail('Connection setup time exceeds maximum permissible value')

    assert response.status_code == 200

    try:
        removed = response.json()['removed']
    except KeyError:
        pytest.fail('During removed getting KeyError has occured')

    items_to_delete = delete_subscriber_test_data
    assert removed == items_to_delete
