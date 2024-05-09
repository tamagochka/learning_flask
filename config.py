import os


class Config:
    # для генерации подписей для защиты веб-форм от подделки межсайтовых запросов
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
