from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, WriteOnlyMapped, relationship
from app import db


class User(db.Model):
    # для задания имени таблицы вручную, иначе оно будет сгенерировано автоматич. на основе имени класса в шнейк-кейсе
    # tablename = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256))
    # не создается фактически в БД, а является высокоуровневым представлением связи между таблицами
    posts: WriteOnlyMapped['Post'] = relationship(back_populates='author')

    def __repr__(self):  # метод класса, определяющий каким образом отображать значения экземпляров класса при их выводе
        return f'<User {self.username}>'


class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(String(140))
    timestamp: Mapped[datetime] = mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    # колонка будет связана с колонкой из таблицы Users (нельзя будет создать запись с user_id,
    # которого нет в колонке id таблицы Users
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)
    author: Mapped['User'] = relationship(back_populates='posts')

    def __repr__(self):
        return f'<Post {self.body}'


'''
примеры запросов к бд:
----------------------
from app import app, db
from app.models import User, Post
from sqlalchemy import select

app.app_context().push()

# добавить записи в бд:
u = user(username='john', email='john@example.com')
db.session.add(u)
db.session.commit()

u = user(username='susan', email='susan@example.com')
db.session.add(u)
db.session.commit()

# выбрать все записи из таблицы представленной классом User
q = select(User)
users = db.session.scalars(q).all()
print(users)
# или так:
for u in users:
    print(u.id, u.username)

# get all posts wtitten by a user
u = db.session.get(User, 1)  # получить запись пользователя по id
q = u.posts.select()  # id всех постов пользователя
p = db.session.scalars(q).all()  # получить записи постов из таблицы post

# print post author and body for all posts
q = select(Post)
posts = db.session.scalars(q)
for p in posts:
    print(p.id, p.author.username, p.body)

# get all users in reverse alphabetical order
q = select(User).order_by(User.username.desc())
db.session.scalars(q).all()

# get all users that have usernames starting with "s"
q = select(User).where(User.username.like('s%'))
db.session.scalars(q).all()
 
'''