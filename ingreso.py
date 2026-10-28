from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

ingreso_bp = Blueprint("ingreso", __name__)

ADMINS_VALIDOS = {
    "admin": "1234",
    "coordinador": "reto123", 
}


@ingreso_bp.route("/", methods=["GET"])
def inicio():
    """Pantalla inicial para elegir ingresar como Administrador o como Usuario."""
    return render_template("ingreso.html")


@ingreso_bp.route("/admin/login", methods=["GET", "POST"])
def login_admin():
    """Inicio de sesión para administradores."""
    if session.get("rol") == "admin":
        return redirect(url_for("registro.registro"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        if usuario in ADMINS_VALIDOS and ADMINS_VALIDOS[usuario] == password:
            session["usuario"] = usuario
            session["rol"] = "admin"
            flash(f"¡Bienvenido(a) Administrador(a) {usuario}!", "success")
            return redirect(url_for("registro.registro"))
        else:
            flash("Credenciales de Administrador incorrectas. Intenta de nuevo.", "danger")

    return render_template("login.html")


@ingreso_bp.route("/usuario", methods=["GET"])
def panel_usuario():
    """Dirige al usuario a la lista de PDAs e historial."""
    session["rol"] = "usuario"
    return redirect(url_for("historial.lista_pdas"))


@ingreso_bp.route("/logout")
def logout():
    """Cierra la sesión y retorna a la ventana inicial de selección de rol."""
    session.clear()
    flash("Has salido del sistema correctamente.", "info")
    return redirect(url_for("ingreso.inicio"))
