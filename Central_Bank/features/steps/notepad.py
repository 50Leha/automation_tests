"""
Текстовый редактор Notepad++ должен быть установлен в директорию:
'C:\\Program Files\\Notepad++\\notepad++.exe'

Данный скрипт написан для англоязычной версии ОС Windows.
При запуске на русскоязычной версии необходимо редактировать имена процессов,
заменяя их на русскоязычные аналоги:
'File' -> '&Файл'
'Open' -> '&Открыть...'
etc...
"""
import sys
from behave import *
from pywinauto.application import Application, ProcessNotFoundError

from utils import TextNotFound, generate_text


@given('we open file in Notepad')
def step_impl(context):
    app = Application(backend="uia")
    app.start("notepad.exe")
    app.Notepad.MenuSelect('File->Open')
    app.Open.Edit.set_edit_text('test.txt')
    app.Open.Open.Click()


@when('we add some text in the Notepad file')
def step_impl(context):
    text = generate_text
    app.Notepad.type_keys(text)


@when('kill the Notepad application')
def step_impl(context):
    assert app.kill()


@then('we open Notepad file and text presents in it')
def step_impl(context):
    with open('test.txt', 'r') as file:
        try:
            string = file.readline()
            assert string == text
        except AssertionError:
            raise TextNotFound(string)


@given('we open file in Notepad++')
def step_impl(context):
    app = Application(backend="uia")

    try:
        app.start(r"C:\Program Files\Notepad++\notepad++.exe")
    except application.ProcessNotFoundError:
        print("You must first start Notepad++"
              " before running this script")
        sys.exit()

    app.Notepad.MenuSelect('File->Open')
    app.Open.Edit.set_edit_text('test.txt')
    app.Open.Open.Click()


@when('we add some text in the Notepad++ file')
def step_impl(context):
    text = generate_text
    app.Notepad.type_keys(text)


@when('kill the Notepad++ application')
def step_impl(context):
    assert app.kill()


@then('we open Notepadd++ file and text presents in it')
def step_impl(context):
    with open('test.txt', 'r') as file:
        try:
            string = file.readline()
            assert string == text
        except AssertionError:
            raise TextNotFound(string)
