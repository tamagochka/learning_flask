from datetime import datetime, timezone
from typing import Optional
from time import time
import jwt
from sqlalchemy import String, ForeignKey, Table, Column, Integer, func, select, or_
from sqlalchemy.orm import Mapped, mapped_column, WriteOnlyMapped, relationship, aliased

import app
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from app import app

followers = Table(
    'followers',
    db.metadata,
    Column('follower_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('followed_id', Integer, ForeignKey('user.id'), primary_key=True)
)


# загрузчик пользователя проверяет наличие пользователя с указанным id в БД для обеспечения работы flask-login
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


# UserMixin добавление специальных методов в класс пользователя для обеспечения работы flask-login
class User(UserMixin, db.Model):
    # для задания имени таблицы вручную, иначе оно будет сгенерировано автоматич. на основе имени класса в шнейк-кейсе
    # tablename = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256))
    # не создается фактически в БД, а является высокоуровневым представлением связи между таблицами
    posts: WriteOnlyMapped['Post'] = relationship(back_populates='author')
    about_me: Mapped[Optional[str]] = mapped_column(String(140))
    last_seen: Mapped[Optional[datetime]] = mapped_column(default=lambda: datetime.now(timezone.utc))
    following: WriteOnlyMapped['User'] = relationship(  # все пользователи, на которых подписан пользователь
        secondary=followers,  # таблица ассоциаций, используемая для связи пользователей и подписчиков
        primaryjoin=(followers.c.follower_id == id),  # условие связи объекта с таблицей ассоциаций
        secondaryjoin=(followers.c.followed_id == id),  # усл. связи объекта с таблицей ассоциаций на др. стороне связи
        back_populates='followers'
    )
    followers: WriteOnlyMapped['User'] = relationship(  # все пользователи, которые подписаны на данного
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following'
    )

    def __repr__(self):  # метод класса, определяющий каким образом отображать значения экземпляров класса при их выводе
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        # digest - хэш для получения аватара по адресу эл. почты с сервиса gravatar.com
        # d=identicon - какое изображение предоставлять пользователям у которых нет аватара в сервисе
        # s={size} - размер предоставляемого аватара
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = select(func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = select(func.count()).select_from(self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        # использование алисов обязательно, чтобы была возможность различать о ком идет речь в запросе
        Author = aliased(User)
        Follower = aliased(User)
        return (
            select(Post)  # выбрать из таблицы Post
            # все поля и присоединить к ней поля из таблицы Author(User), связанные с Post.author (авторы постов)
            .join(Post.author.of_type(Author))  # присоединить к инф. о постах инф. об авторе поста
            # выбрать из полученной таблицы все поля
            # и присоединить к ней поля из таблицы Follower(User), связанные с Author.followers (подписчики автора)
            # получится таблица, содержащая всех подписчиков и посты, которые они должны получить
            # post.id post.text post.user_id == author.id author.username follower.id follower.username
            .join(Author.followers.of_type(Follower), isouter=True)
            # isouter - не отбрасывать поля с левой стороны, у которых нет соответствия с правой
            # будут получены и посты тех авторов, у которых нед подписоты
            # слева таблица Post+Author справа Follower
            # если не указать isouter, то посты авторов, у которых нет подписчиков будут отброшены,
            # будут только те поля у которых есть соответствие и справа и слева
            # выбрать из полученной таблицы поля для текущего пользователя
            .where(or_(  # т.е. посты которые он должен увидеть
                Follower.id == self.id,  # посты авторов, на которые он подписан
                Author.id == self.id  # посты автором которых он является
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())  # сортировать посты по времени их добавления по полю timestamp
        )

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)


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
p = db.session.scalars(q).all()  # получить все записи постов из таблицы post
p = db.session.scalars(q).first()  # получить первую запись из таблицы post

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

q = select(User).where(User.username == 'john')
db.session.scalar(q)  # вернет одну запись, если она есть, иначе None
 
'''
