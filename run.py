from app import app, db
from sqlalchemy import select
from app.models import User, Post


@app.shell_context_processor
def make_shell_context():  # создание контекста приложения для flask shell
    return {
        'db': db,
        'select': select,
        'User': User,
        'Post': Post
    }
