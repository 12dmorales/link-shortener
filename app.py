from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import geoip2.database
import shortuuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Ruta de la base de datos
db = SQLAlchemy(app)

# Cargar la base de datos de GeoIP
geoip_reader = geoip2.database.Reader('GeoLite2-Country.mmdb')

# Modelo de la base de datos
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(20), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)
    countries = db.Column(db.JSON, default={})  # Diccionario para almacenar clics por país

# Ruta principal: Acortar enlaces
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['original_url']
        extension = request.form.get('extension', '')

        # Generar código corto único
        short_code = extension if extension else shortuuid.uuid()[:8]

        # Guardar en la base de datos
        new_link = Link(original_url=original_url, short_code=short_code)
        db.session.add(new_link)
        db.session.commit()

        return render_template('index.html', short_url=f"http://localhost:5000/{short_code}")

    return render_template('index.html')

# Redirección y registro de clics
@app.route('/<short_code>')
def redirect_to_url(short_code):
    link = Link.query.filter_by(short_code=short_code).first()

    if link:
        # Registrar clic
        link.clicks += 1

        # Obtener país del usuario
        ip = request.remote_addr
        try:
            country = geoip_reader.country(ip).country.name
        except:
            country = 'Desconocido'

        # Actualizar estadísticas por país
        if country in link.countries:
            link.countries[country] += 1
        else:
            link.countries[country] = 1

        db.session.commit()

        return redirect(link.original_url)
    else:
        return "Enlace no encontrado", 404

# Estadísticas del enlace
@app.route('/stats/<short_code>')
def stats(short_code):
    link = Link.query.filter_by(short_code=short_code).first()

    if link:
        return render_template('stats.html', link=link)
    else:
        return "Enlace no encontrado", 404

# Crear la base de datos manualmente
def create_database():
    with app.app_context():
        db.create_all()
        print("Base de datos creada correctamente.")

# Iniciar la aplicación
if __name__ == '__main__':
    create_database()  # Crear la base de datos antes de ejecutar la aplicación
    app.run(debug=True)