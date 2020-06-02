"""
Module with utility functions
"""
from random import choice
import string


def generate_email_name():
    """
    utility to generate random name and email

    :return: tuple(email, name)
    """
    name = [choice(string.ascii_letters) for _ in range(5)]
    email_tail = '@foo.bar'
    # join to string
    name = ''.join(name)
    email = name + email_tail

    return email, name
