import os
import json
import boto3
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from pydantic import ValidationError
from datetime import datetime
import uuid
from models.grades import GradeModel, UpdateGradeModel, GradeCreateModel
import psycopg2

app = Flask(__name__)

# --- 1️⃣ Obtener credenciales de DB desde AWS Secrets Manager ---
SECRET_ARN = os.environ.get("DB_SECRET_ARN")
REGION = os.environ.get("AWS_REGION", "us-east-1")  # Ajusta tu región

db_username = db_password = db_host = db_name = None

if SECRET_ARN:
    client = boto3.client("secretsmanager", region_name=REGION)
    secret_value = client.get_secret_value(SecretId=SECRET_ARN)
    secret_dict = json.loads(secret_value["SecretString"])
    
    db_username = secret_dict.get("username")
    db_password = secret_dict.get("password")
    # Puedes pasar host y nombre DB vía variables de entorno
    db_host = os.environ.get("DB_HOST", "my-rds-endpoint")
    db_name = os.environ.get("DB_NAME", "appdb")
    
    DB_URI = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:5432/{db_name}"
else:
    # Fallback local para desarrollo
    DB_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///test.db")

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- 2️⃣ Inicialización de SQLAlchemy ---
db = SQLAlchemy(app)

# --- 3️⃣ Definición del modelo de BBDD ---
class GradeDB(db.Model):
    __tablename__ = "grades"
    
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Clase = db.Column(db.String(100), nullable=False)
    Alumno = db.Column(db.String(100), nullable=False)
    Nota = db.Column(db.Integer, nullable=False)
    Fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<GradeDB {self.Alumno} - {self.Clase}>'

# --- 4️⃣ Manejador de errores de Pydantic ---
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"errors": e.errors()}), 400

# --- 5️⃣ Endpoints ---
@app.route('/grades', methods=['GET', 'POST'])
def handle_grades():
    if request.method == 'POST':
        data = request.get_json()
        try:
            validated_data = GradeCreateModel.model_validate(data)
        except ValidationError as e:
            return jsonify({"errors": e.errors()}), 400

        data_dict = validated_data.model_dump()
        if 'Fecha' in data_dict and data_dict['Fecha']:
            data_dict['Fecha'] = datetime.fromisoformat(data_dict['Fecha'])

        new_grade_db = GradeDB(**data_dict)
        try:
            db.session.add(new_grade_db)
            db.session.commit()
            response_model = GradeModel.model_validate(new_grade_db)
            return jsonify(response_model.model_dump()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al guardar en la base de datos", "details": str(e)}), 500
    else:  # GET
        all_grades_db = db.session.execute(db.select(GradeDB)).scalars().all()
        response_list = [GradeModel.model_validate(grade).model_dump() for grade in all_grades_db]
        return jsonify(response_list), 200

@app.route('/grades/<uuid:grade_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_grade_by_id(grade_id):
    grade_db = db.session.get(GradeDB, grade_id)
    if not grade_db:
        return jsonify({"error": f"Elemento con ID {grade_id} no encontrado."}), 404

    if request.method == 'GET':
        response_model = GradeModel.model_validate(grade_db)
        return jsonify(response_model.model_dump()), 200

    elif request.method == 'PUT':
        data = request.get_json()
        try:
            update_data = UpdateGradeModel.model_validate(data)
        except ValidationError as e:
            return jsonify({"errors": e.errors()}), 400

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == 'Fecha' and value is not None:
                value = datetime.fromisoformat(value)
            setattr(grade_db, key, value)

        try:
            db.session.commit()
            response_model = GradeModel.model_validate(grade_db)
            return jsonify(response_model.model_dump()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al actualizar la base de datos", "details": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(grade_db)
            db.session.commit()
            return jsonify({"mensaje": f"Elemento con ID {grade_id} eliminado."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al eliminar de la base de datos", "details": str(e)}), 500

# --- 6️⃣ Inicialización de la base de datos ---
def setup_database(app):
    with app.app_context():
        db.create_all()

# --- 7️⃣ Ejecutar la app ---
if __name__ == '__main__':
    setup_database(app)
    app.run(debug=True, port=5000)

