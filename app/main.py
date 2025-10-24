from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from pydantic import ValidationError
from datetime import datetime
import uuid

# Importamos los modelos Pydantic
# GradeCreateModel: para POST (entrada)
# UpdateGradeModel: para PUT (entrada)
# GradeModel: para GET (salida)
from models.grades import GradeModel, UpdateGradeModel, GradeCreateModel

app = Flask(__name__)

# app.py

# Apunta al puerto 5433, que es el que abrimos en el host
DB_URI = "postgresql://postgres:mysecretpassword@localhost:5432/grades_db"
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Desactiva warnings

# --- 2. Inicialización de SQLAlchemy ---
db = SQLAlchemy(app)


# --- 3. Definición del Modelo de Base de Datos (SQLAlchemy) ---
# Este es el modelo que define la TABLA en PostgreSQL.
# No es el modelo Pydantic.

class GradeDB(db.Model):
    __tablename__ = "grades"
    
    # Usamos db.Uuid para el tipo UUID nativo de PostgreSQL
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    Clase = db.Column(db.String(100), nullable=False)
    Alumno = db.Column(db.String(100), nullable=False)
    Nota = db.Column(db.Integer, nullable=False)
    
    # Usamos db.DateTime. La BBDD gestionará las fechas.
    Fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    # onupdate=... : se actualiza automáticamente en cada UPDATE
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<GradeDB {self.Alumno} - {self.Clase}>'


# --- Manejador de Errores de Validación Pydantic ---
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"errors": e.errors()}), 400


# --- 4. Refactorización de Endpoints ---

## 1. Ruta [GET ALL] y [CREATE] (/grades)
@app.route('/grades', methods=['GET', 'POST'])
def handle_grades():

    # --- (Create) Crear un nuevo elemento ---
    if request.method == 'POST':
        data = request.get_json()
        
        # Validamos con el modelo de CREACIÓN (sin id, sin timestamps)
        try:
            validated_data = GradeCreateModel.model_validate(data)
        except ValidationError as e:
            return jsonify({"errors": e.errors()}), 400

        # Convertimos el modelo Pydantic a un dict
        data_dict = validated_data.model_dump()
        
        # Convertimos la fecha ISO (string) a objeto datetime si existe
        if 'Fecha' in data_dict and data_dict['Fecha']:
            data_dict['Fecha'] = datetime.fromisoformat(data_dict['Fecha'])

        # Creamos la instancia del modelo de BBDD (SQLAlchemy)
        new_grade_db = GradeDB(**data_dict)

        # Añadimos a la sesión y guardamos en la BBDD
        try:
            db.session.add(new_grade_db)
            db.session.commit()
            
            # Devolvemos el objeto completo (usando el modelo de RESPUESTA)
            # 'model_validate' lee el objeto new_grade_db gracias a from_attributes=True
            response_model = GradeModel.model_validate(new_grade_db)
            return jsonify(response_model.model_dump()), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al guardar en la base de datos", "details": str(e)}), 500

    # --- (Read All) Obtener todos los elementos ---
    elif request.method == 'GET':
        # Consultamos la BBDD
        all_grades_db = db.session.execute(db.select(GradeDB)).scalars().all()
        
        # Convertimos cada objeto de BBDD a un modelo Pydantic de respuesta
        response_list = [GradeModel.model_validate(grade).model_dump() for grade in all_grades_db]
        
        return jsonify(response_list), 200

## 2. Ruta [GET BY ID], [UPDATE] y [DELETE] (/grades/<id>)
# El ID ahora es un UUID
@app.route('/grades/<uuid:grade_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_grade_by_id(grade_id):
    
    # Buscamos el objeto en la BBDD.
    # get_or_404 es un helper de Flask-SQLAlchemy que devuelve 404 si no lo encuentra.
    grade_db = db.session.get(GradeDB, grade_id)
    if not grade_db:
         return jsonify({"error": f"Elemento con ID {grade_id} no encontrado."}), 404

    # --- (Read) Obtener un elemento por ID ---
    if request.method == 'GET':
        # Convertimos el objeto BBDD a modelo Pydantic de respuesta
        response_model = GradeModel.model_validate(grade_db)
        return jsonify(response_model.model_dump()), 200

    # --- (Update) Actualizar un elemento existente ---
    elif request.method == 'PUT':
        data = request.get_json()

        try:
            # Validamos con el modelo de ACTUALIZACIÓN (opcional)
            update_data = UpdateGradeModel.model_validate(data)
        except ValidationError as e:
            return jsonify({"errors": e.errors()}), 400

        # Obtenemos un dict solo con los campos que el cliente ENVIÓ
        update_dict = update_data.model_dump(exclude_unset=True)

        # Actualizamos el objeto de BBDD campo por campo
        for key, value in update_dict.items():
            # Convertimos fecha string a objeto datetime
            if key == 'Fecha' and value is not None:
                value = datetime.fromisoformat(value)
            setattr(grade_db, key, value)
        
        # El timestamp 'updated_at' se actualizará automáticamente (ver 'onupdate' en el modelo)

        try:
            db.session.commit()
            
            # Devolvemos el objeto actualizado
            response_model = GradeModel.model_validate(grade_db)
            return jsonify(response_model.model_dump()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al actualizar la base de datos", "details": str(e)}), 500

    # --- (Delete) Eliminar un elemento ---
    elif request.method == 'DELETE':
        try:
            db.session.delete(grade_db)
            db.session.commit()
            return jsonify({"mensaje": f"Elemento con ID {grade_id} eliminado."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al eliminar de la base de datos", "details": str(e)}), 500


# --- 5. Creación de las tablas ---
# Esto crea las tablas definidas en los modelos (ej. GradeDB)
# si no existen al iniciar la app.
# Para producción, se recomienda usar migraciones (Alembic).

def setup_database(app):
    with app.app_context():
        db.create_all()

# --- Ejecución de la App ---
if __name__ == '__main__':
    setup_database(app) # Crea las tablas antes de correr
    app.run(debug=True, port=5000)