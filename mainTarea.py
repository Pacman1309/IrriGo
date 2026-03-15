import os
import decimal
import datetime
from flask import Flask, request, jsonify
import mysql.connector
from flask.json.provider import DefaultJSONProvider

app = Flask(__name__)
BASE_URL = '/api/v1'

# ==========================================
# Configuración de Serialización JSON
# ==========================================
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat() + "Z"
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)

app.json = CustomJSONProvider(app)

# ==========================================
# Diccionario de Recursos OpenAPI -> MySQL
# ==========================================
RESOURCE_MAP = {
    "usuarios": {"table": "Usuario", "pk": "IDusuario"},
    "predios": {"table": "Predio", "pk": "IDpredio"},
    "usuarios-predios": {"table": "Usuario_predio", "pk": "composite"}, # ID ej: "1-2"
    "registros-auditoria": {"table": "RegistroAuditoria", "pk": "IDregistro"},
    "modulos-control": {"table": "ModuloControl", "pk": "ID_Modulo"},
    "areas-riego": {"table": "AreaRiego", "pk": "ID_Area"},
    "sensores": {"table": "Sensor", "pk": "IDsensor"},
    "configuraciones-cultivos": {"table": "ConfiguracionCultivo", "pk": "ID_Configuracion"},
    "alertas": {"table": "Alerta", "pk": "ID_Alerta"},
    "mediciones-historicas": {"table": "MedicionHistorica", "pk": "ID_Medicion"}
}

# ==========================================
# Conexión a Base de Datos
# ==========================================
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DATABASE', 'IrriGo')
    )

def execute_query(query, params=(), fetch=False, fetch_one=False, commit=False):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetch:
            return cursor.fetchall()
        if fetch_one:
            return cursor.fetchone()
        return cursor.lastrowid
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()

# ==========================================
# Endpoints Dinámicos (Colecciones: GET, POST)
# ==========================================
@app.route(f'{BASE_URL}/<resource>', methods=['GET', 'POST'])
def handle_collection(resource):
    if resource not in RESOURCE_MAP:
        return jsonify({"code": "404", "message": "Ruta de recurso no encontrada"}), 404

    cfg = RESOURCE_MAP[resource]
    table = cfg['table']

    try:
        if request.method == 'GET':
            records = execute_query(f"SELECT * FROM {table}", fetch=True)
            return jsonify(records), 200

        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"code": "400", "message": "Petición inválida o cuerpo vacío"}), 400

            cols = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            
            last_id = execute_query(query, list(data.values()), commit=True)

            if cfg['pk'] == 'composite':
                # En IDs compuestos devolvemos el payload inicial porque last_id no aplica
                return jsonify(data), 201
            else:
                created = execute_query(f"SELECT * FROM {table} WHERE {cfg['pk']} = %s", [last_id], fetch_one=True)
                return jsonify(created), 201

    except mysql.connector.Error as e:
        return jsonify({"code": "500", "message": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"code": "500", "message": f"Error interno: {str(e)}"}), 500

# ==========================================
# Endpoints Dinámicos (Ítems: GET, PUT, DELETE)
# ==========================================
@app.route(f'{BASE_URL}/<resource>/<id>', methods=['GET', 'PUT', 'DELETE'])
def handle_item(resource, id):
    if resource not in RESOURCE_MAP:
        return jsonify({"code": "404", "message": "Ruta de recurso no encontrada"}), 404

    cfg = RESOURCE_MAP[resource]
    table = cfg['table']
    pk = cfg['pk']

    # Manejo de ID compuesto para /usuarios-predios/{id}
    if pk == 'composite':
        try:
            id1, id2 = id.split('-')
            where_clause = "IDusuario = %s AND IDpredio = %s"
            where_params = [id1, id2]
        except ValueError:
            return jsonify({"code": "400", "message": "Formato de ID compuesto inválido. Usa 'IDusuario-IDpredio'"}), 400
    else:
        where_clause = f"{pk} = %s"
        where_params = [id]

    try:
        # Validar existencia (Común para GET, PUT, DELETE)
        existing = execute_query(f"SELECT * FROM {table} WHERE {where_clause}", where_params, fetch_one=True)
        if not existing:
            return jsonify({"code": "404", "message": "Recurso no encontrado"}), 404

        if request.method == 'GET':
            return jsonify(existing), 200

        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({"code": "400", "message": "Petición inválida o cuerpo vacío"}), 400

            set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            params = list(data.values()) + where_params
            
            execute_query(query, params, commit=True)
            
            updated = execute_query(f"SELECT * FROM {table} WHERE {where_clause}", where_params, fetch_one=True)
            return jsonify(updated), 200

        if request.method == 'DELETE':
            execute_query(f"DELETE FROM {table} WHERE {where_clause}", where_params, commit=True)
            return '', 204

    except mysql.connector.Error as e:
        return jsonify({"code": "500", "message": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"code": "500", "message": f"Error interno: {str(e)}"}), 500

if __name__ == '__main__':
    # Puerto definido en el YAML
    app.run(host='0.0.0.0', port=3000, debug=True)