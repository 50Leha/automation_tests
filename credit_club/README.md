Для запуска теста требуется:

1. Python, версии не ниже 3.6.8
2. Пакетный менеджер pip3 (sudo apt-get install python3-pip)
3. В корне проекта credit_club запустить команду pip3 install -r requirements.txt
4. Скачать ChromeDriver c сайта https://sites.google.com/a/chromium.org/chromedriver/downloads (выбрать версию драйвера, соответствующую версии браузера Chrome*)
4. Переместить разархивированный файл с СhromeDriver в нужную папку и разрешить запускать chromedriver как исполняемый файл:
    sudo mv chromedriver /usr/local/bin/chromedriver
    sudo chown root:root /usr/local/bin/chromedriver
    sudo chmod +x /usr/local/bin/chromedriver
5. В корне проекта выполнить скрипт: echo 'test' > test.txt
6. В корне проекта запустить тест: pytest -v credit_club.py
________________
* Версию Chrome можно узнать, введя в адресной строке браузера: chrome://settings/help
