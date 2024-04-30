# Импорт необходимых модулей и классов
from flask import Flask, render_template, request, redirect, flash, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

# Создаем экземпляр приложения Flask
app = Flask(__name__)

# Конфигурация базы данных и секретного ключа для безопасности
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'e97033b8b0e5347cb4ea4f6a1ad5d7d6'

# Инициализация SQLAlchemy для работы с базой данных
db = SQLAlchemy(app)

# Инициализация Flask-Login для управления аутентификацией пользователей
login_manager = LoginManager(app)

# Определение модели пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    tasks = db.relationship('Task', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)

# Определение модели задачи
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Task('{self.title}', '{self.date_created}', '{self.completed}')"

# Определение класса формы для создания задачи
class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Add Task')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.content}', '{self.date_posted}')"


class CommentForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired()], render_kw={'placeholder': ''})
    submit = SubmitField('Add Comment')


# Создание всех таблиц в базе данных, если они еще не существуют
with app.app_context():
    db.create_all()


# Функция для загрузки пользователя Flask-Login на основе его идентификатора
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))


# Определение маршрута для главной страницы
@app.route('/')
def index():
    return render_template('index.html')


# Определение маршрута для страницы регистрации пользователей
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Получение данных из формы
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Проверка наличия пользователя с таким же именем или email
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Пользователь с таким именем уже существует', 'error_register')
            return redirect('/register')

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Пользователь с такой почтой уже существует', 'error_register')
            return redirect('/register')

        # Проверка соответствия пароля и его подтверждения
        if password != confirm_password:
            flash('Пароль и его подтверждение не совпадают', 'error_register')
            return redirect('/register')

        # Создание нового пользователя и добавление его в базу данных
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация прошла успешно!', 'success_register')
        return redirect('/login')

    return render_template('register.html')


# Определение маршрута для секретной страницы
@app.route('/secret')
@login_required
def secret():
    message = f"Welcome to the Secret Page, {current_user.username}. "
    message += "This is a secret page accessible only to authenticated users. "
    message += f"<a href='{url_for('index')}'>Go to Home</a>"
    return message


# Определение маршрута для страницы входа пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user and user.password == password:
            login_user(user)
            flash('Вы успешно авторизовались', 'success_login')
            return redirect('/')
        else:
            flash('Неверные имя или пароль', 'error_login')

    return render_template('login.html')


# Определение маршрута для выхода пользователя из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли', 'success')
    return redirect('/')


# Определение маршрута для создания задачи
@app.route('/create_task', methods=['POST'])
@login_required
def create_task():
    form = TaskForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        new_task = Task(title=title, description=description, author=current_user)
        db.session.add(new_task)
        db.session.commit()
        flash('Task created successfully!', 'success')
    else:
        flash('Failed to create task. Please check your input.', 'error')
    return redirect(url_for('todo'))


# Определение маршрута для отображения всех задач
@app.route('/todo')
@login_required
def todo():
    form = TaskForm()
    tasks = current_user.tasks
    return render_template('todo.html', form=form, tasks=tasks)


# Определение маршрута для отображения конкретной задачи
@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def task(task_id):
    task = Task.query.get_or_404(task_id)
    comments = Comment.query.filter_by(task_id=task_id).all()  # Получаем все комментарии для данной задачи
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        comment_text = comment_form.content.data
        new_comment = Comment(content=comment_text, user_id=current_user.id, task_id=task_id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
        return redirect(url_for('task', task_id=task_id))

    return render_template('task.html', task=task, comments=comments, comment_form=comment_form)


# Определение маршрута для обновления статуса задачи на "выполнено"
@app.route('/complete_task/<int:task_id>', methods=['POST', 'PUT'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    flash('Task marked as completed', 'success')
    return redirect(url_for('todo'))


@app.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        abort(403)  # Forbidden
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('todo'))


@app.route('/add_comment/<int:task_id>', methods=['POST'])
@login_required
def add_comment(task_id):
    form = CommentForm()
    if form.validate_on_submit():
        content = form.comment_text.data
        # Создаем новый комментарий с указанием текущего пользователя
        new_comment = Comment(content=content, user_id=current_user.id, task_id=task_id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
        return redirect(url_for('task', task_id=task_id))
    flash('Failed to add comment. Please check your input.', 'error')
    return redirect(url_for('task', task_id=task_id))


# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True, port=8080, host='192.168.0.107')