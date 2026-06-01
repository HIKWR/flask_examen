from flask import Flask, render_template, request, redirect, url_for, flash, session as flask_s
from os import getenv
from sqlalchemy import Column, create_engine, Integer, VARCHAR, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from requests import get
from random import choice

load_dotenv()

## CONFIG SQL
MYSQL_HOST = getenv('mysql_host')
MYSQL_USER = getenv('mysql_user')
MYSQL_PASSWORD = getenv('mysql_password')
MYSQL_DATABASE = getenv('mysql_database')

Base = declarative_base()

engine = create_engine(f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}')

session = sessionmaker(bind=engine)

session = session()

class Usuarios(Base):
    __tablename__= 'usuarios'
    id=Column(Integer, primary_key=True)
    username=Column(VARCHAR(50))
    email=Column(VARCHAR(50))
    password_hash=Column(VARCHAR(512))
    fecha_registro=Column(Date)
    ultimo_login=Column(Date)

class Favoritos(Base):
    __tablename__ = 'favoritos'
    id=Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('usuarios.id'))
    name = Column(VARCHAR(50))
    gender = Column(VARCHAR(50))
    image = Column(VARCHAR(512))

Base.metadata.create_all(engine)


#APP
app = Flask(__name__)
app.config['SECRET_KEY'] = getenv('secreto')

## POST
@app.route('/register', methods=['POST'])
def register_submit():
    username = request.form.get('username','')
    email = request.form.get('email','').strip().lower()
    password = request.form.get('pass', '')

    if not username or not email or not password:
        flash('Faltan datos', 'danger')
        return redirect(url_for('register'))

    req_usuario = session.query(Usuarios).filter_by(username=username).first()

    if req_usuario:
        flash('El usuario ya existe en la base de datos', 'danger')
        return redirect(url_for('register'))
    
    usuario = Usuarios(username=username, email=email, password_hash=generate_password_hash(password), fecha_registro=datetime.now(tz=timezone.utc), ultimo_login=None)
    session.add(usuario)
    session.flush()
    session.commit()

    flask_s.permanent = True

    flask_s['user_name'] = usuario.username
    flask_s['last_login'] = usuario.ultimo_login
    flask_s['register_date'] = usuario.fecha_registro

    flash('Usuario logueado exitosamente', 'success')
    return redirect(url_for('dashboard'))
    

@app.route('/login', methods=['POST'])
def login_submit():
    email = request.form.get('email','').strip().lower()
    password = request.form.get('pass', '')

    if not email or not password:
        flash('Faltan datos', 'danger')
        return redirect(url_for('login'))

    req_usuario = session.query(Usuarios).filter_by(email=email).first()

    if not req_usuario:
        flash('El usuario no existe', 'danger')
        return redirect(url_for('login'))
    
    req_usuario.ultimo_login = datetime.now(tz=timezone.utc)
    session.commit()
    
    flask_s.permanent = True
    flask_s['user_name'] = req_usuario.username
    flask_s['last_login'] = req_usuario.ultimo_login
    flask_s['register_date'] = req_usuario.fecha_registro

    flash('Usuario logueado exitosamente', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    if not session.permanent:
        flash('Debes iniciar sesión', 'success')
        return redirect(url_for('login'))
    
    flask_s.clear()

    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('index'))

@app.route('/favoritos', methods=['POST'])
def favoritos_submit():
    print(request.form)

    flask_s['lista_fav'] = []

    for fav in request.form:
        fav = {
            'name':fav.get('name'),
            'species':fav.get('species'),
            'image':fav.get('image')
        }
        flask_s['lista_fav'].append(fav)
        
    print(flask_s['lista_fav'])
    flash('Personajes añadidos correctamente')
    return 'patata'

## GET
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not flask_s.permanent:
        flash('Debes iniciar sesión', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/personajes')
def favoritos():
    if not flask_s.permanent:
        flash('Debes iniciar sesión', 'success')
        return redirect(url_for('login'))
    
    req = get('https://futuramaapi.com/api/characters')

    lista_char = req.json()

    lista = []

    for i in range(10):
        char = choice(lista_char['items'])

        lista.append(char)

    flask_s['lista_char'] = lista

    return render_template('personajes.html')

def page_not_found(error):
    return render_template('404.html')

if __name__ == '__main__':
    app.register_error_handler(404, page_not_found)
    app.run(debug=True, port=3000)

