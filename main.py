import os
from flask import Flask
from ingreso import ingreso_bp
from registro import registro_bp
from historial import historial_bp
from resumen import resumen_bp


def crear_app():
    """Inicializa la app Flask vinculando ingreso, registro, historial y resumen."""
    app = Flask(__name__, template_folder="templates")
    app.secret_key = "clave_secreta_reto_coordinadora"

    # Registro modular de los componentes
    app.register_blueprint(ingreso_bp)
    app.register_blueprint(registro_bp)
    app.register_blueprint(historial_bp)
    app.register_blueprint(resumen_bp)

    return app


def main():
    print("Hola, bienvenidos a el reto")
    print("---------------------------------------------------------")
    print("Sistema de Gestión e Historial de PDAs Coordinadora")
    print("Servidor iniciado en:")
    print("--> http://localhost:5000")
    print("---------------------------------------------------------")

    app = crear_app()
    app.run(host="localhost", port=5000, debug=True)


if __name__ == "__main__":
    main()
