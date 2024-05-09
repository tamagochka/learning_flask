from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Inokentiy'}
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
    return render_template('index.html', title='Home', user=user, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # validate_on_submit() будет возвращать False, когда браузер отправляет запрос GET на получение веб-страницы
    # поэтому происходит просто отрисовка страницы
    # при получении запроса POST производит сбор данных из формы и проверку их в соответствии с заданными validators
    # если все в порядке, то вернет True, если хотя бы одно поле не пройдет проверку, то вернет False
    # и форма будет отображена как при GET запросе
    if form.validate_on_submit():
        # отображает сообщение пользователю, оно отправляется в шаблон, после чего все сообщения отправленные во flash
        # могут быть отображены с использованием get_flashed_messages(), после запроса сообщений через
        # get_flashed_messages() они от туда удаляются и больше не отображаются
        flash(f'Login requested for user {form.username.data}, remember_me={form.remember_me.data}')
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign in', form=form)
