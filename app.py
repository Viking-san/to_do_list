from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'e97033b8b0e5347cb4ea4f6a1ad5d7d6'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

with app.app_context():
    db.create_all()

@app.route('/')
def hello_world():
    return 'Hello world!'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        print(username, email, password, confirm_password)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return 'Пользователь с таким именем уже существует.'

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return 'Пользователь с такой почтой уже существует.'

        if password != confirm_password:
            return 'Пароль и его подтверждение не совпадают.'

        new_user = User(username=username, email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        return redirect('/')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            flash('Вы успешно авторизовались', 'success')
            return redirect('/')
        else:
            flash('Неверные имя или пароль', 'error')

    return render_template('login.html')



if __name__ == '__main__':
    app.run(debug=True)
# try use gitignore