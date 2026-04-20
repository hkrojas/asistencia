import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ── Cargar variables de entorno (.env) ──
load_dotenv()

def create_app():
    """Application factory pattern."""
    app = Flask(__name__)

    # ── Configuración ──
    app.config['DATABASE_URL'] = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/asistencia'
    )
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    # ── CORS — permitir peticiones desde la app móvil ──
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Rutas de salud ──
    @app.route('/ping', methods=['GET'])
    def ping():
        return jsonify({
            'status': 'ok',
            'message': 'Asistencia API is running 🚀'
        }), 200

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'version': '0.1.0',
            'service': 'asistencia-api'
        }), 200

    # ── Registrar Blueprints ──
    from routes.devices import devices_bp
    from routes.attendance import attendance_bp
    from routes.schedules import schedules_bp
    app.register_blueprint(devices_bp, url_prefix='/v1')
    app.register_blueprint(attendance_bp, url_prefix='/v1')
    app.register_blueprint(schedules_bp, url_prefix='/v1')

    return app


# ── Ejecución directa para desarrollo ──
if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
