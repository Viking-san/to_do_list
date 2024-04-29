from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

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

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)


# Создание всех таблиц в базе данных, если они еще не существуют
with app.app_context():
    db.create_all()


# Функция для загрузки пользователя Flask-Login на основе его идентификатора
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Определение маршрута для главной страницы
@app.route('/')
def hello_world():
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
            return 'Пользователь с таким именем уже существует.'

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return 'Пользователь с такой почтой уже существует.'

        # Проверка соответствия пароля и его подтверждения
        if password != confirm_password:
            return 'Пароль и его подтверждение не совпадают.'

        # Создание нового пользователя и добавление его в базу данных
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


# Определение маршрута для секретной страницы
@app.route('/secret')
def secret():
    # Проверка аутентификации пользователя
    if current_user.is_authenticated:
        # Сообщение для аутентифицированного пользователя
        message = f"Welcome to the Secret Page, {current_user.username}. "
        message += "This is a secret page accessible only to authenticated users. "
        message += f"<a href='{url_for('hello_world')}'>Go to Home</a>"
        return message
    else:
        # Сообщение для неаутентифицированного пользователя
        message = f"You need to <a href='{url_for('login')}'>log in</a> or go to "
        message += f"<a href='{url_for('hello_world')}'>Home</a>"
        return message


# Определение маршрута для страницы входа пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user and user.password == password:
            # Аутентификация пользователя и перенаправление на главную страницу
            login_user(user)
            flash('Вы успешно авторизовались', 'success')
            return redirect('/')
        else:
            # Ошибка при вводе неверного имени или пароля
            flash('Неверные имя или пароль', 'error')

    return render_template('login.html')


# Определение маршрута для выхода пользователя из системы
@app.route('/logout')
@login_required
def logout():
    # Выход пользователя и перенаправление на главную страницу
    logout_user()
    flash('Вы успешно вышли', 'success')
    return redirect('/')


# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)