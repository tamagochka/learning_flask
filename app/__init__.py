from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler

app = Flask(__name__)
app.config.from_object(Config)

login = LoginManager(app)
# редиректить пользователя на страницу логина, при попытке анонимно зайти на защищенную страницу
login.login_view = 'login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

if not app.debug:  # настройка почты для отправки сообщений об ошибках
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            # в случае использования стороннего почтового сервиса лучше установить равным app.config['MAIL_USERNAME']
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'],
            subject='Microblog failure',
            credentials=auth,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

from app import routes, models, errors
