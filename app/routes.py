from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import select
from app.models import User
from urllib.parse import urlsplit
from datetime import datetime, timezone


@app.route('/')
@app.route('/index')
@login_required  # страница защищена от неавторизованных пользователей
def index():
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # если пользователь за логинен, то переадресуем его на главную
        return redirect(url_for('index'))
    form = LoginForm()
    # validate_on_submit() будет возвращать False, когда браузер отправляет запрос GET на получение веб-страницы
    # поэтому происходит просто отрисовка страницы
    # при получении запроса POST производит сбор данных из формы и проверку их в соответствии с заданными validators
    # если все в порядке, то вернет True, если хотя бы одно поле не пройдет проверку, то вернет False
    # и форма будет отображена как при GET запросе
    if form.validate_on_submit():
        # получаем данные пользователя из БД
        user = db.session.scalar(select(User).where(User.username == form.username.data))
        # если пользователя несуществует или его пароль не верный, то выводим ошибку и заново отрисовываем страницу
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        # если все верно, то логиним пользователя и если стоит галочка запомнить, то запоминаем его
        # будет установлена переменная current_user, после чего проверяя ее можно узнать залогинен ли пользователь
        login_user(user, remember=form.remember_me.data)
        # если пользователь был отправлен на страницу логина с защищенной страницы, то адрес страницы, к которой он
        # хотел получить доступ будет передан странице логина в запросе в аргументе next
        # после успешного логина, его необходимо отправить обратно на ту страницу на которую он хотел попасть
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':  # если адрес защищенной страницы не задан
            next_page = url_for('index')  # то отправляем пользователя на главную
        return redirect(next_page)
        # urlsplit и netloc используются для определения с какой страницы был отправлен пользователь на страницу логина
        # для повышения безопасности, т.к. злоумышленник может вставить в аргумент next URL вредоносного сайта,
        # поэтому приложение переадресует только в том случае, если URL является относительным, что гарантирует
        # что перенаправление произойдет в пределах того же сайта, что и приложение
        # для чего URL разбивается ф-цией urlsplit, а затем проверяется установлен ли netloc
    return render_template('login.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # если пользователь залогинен, то редиректим его на главную
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():  # обрабатывем нажатие кнопки в форме (регистрируем нового пользователя)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')  # значение указанное вместо <username> будет передано в функцию в качестве параметра
@login_required
def user(username):  # страница профиля пользователя
    # если пользователя нет, то клиенту будет отправлена ошибка 404
    user = db.first_or_404(select(User).where(User.username == username))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


# ф-ция, которая выполняется перед каждой ф-цией просмотра (перед каждым запросом к сайту)
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)  # запоминает время последнего посещения сайта пользователем
        db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('You changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':  # если GET запрос, то заполняем поля формы текущими значениями
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit profile', form=form)
