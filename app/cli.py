from app import app
import os
import click

# интерфейс командной строки flask


@app.cli.group()  # группа команд перевода, для упрощения использования функций flask-babel
def translate():  # корневая ф-ция
    """ Команды перевода и локализации """
    pass


@translate.command()
def update():
    """ Обновить исходные файлы переводов для всех языков """
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel update -i messages.pot -d app/translations'):
        raise RuntimeError('update command failed')
    os.remove('messages.pot')


@translate.command()
def compile():
    """ Сборка всех языковых файлов """
    if os.system('pybabel compile -d app/translations'):
        raise RuntimeError('compile command failed')


@translate.command()
@click.argument('lang')
def init(lang):
    """ Инициализировать добавление еще одного языка """
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel init -i messages.pot -d app/translations -l ' + lang):
        raise RuntimeError('init command failed')
    os.remove('messages.pot')
