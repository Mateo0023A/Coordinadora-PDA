import os
import csv
import re
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from historial import registrar_evento_historial

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_CSV = os.path.join(DIRECTORIO_ACTUAL, "equipos_registrados.csv")

# Opciones para listas desplegables
OPCIONES_MARCA = ["Zebra", "Honeywell"]
OPCIONES_AREA = ["Distribución", "Recolección", "Bodega", "Administración"]
OPCIONES_ESTADO = [
    "En bodega",
    "En repartición",
    "En uso",
    "En reparación",
    "Dado de baja",
    "Perdido"
]

registro_bp = Blueprint("registro", __name__)


def requerir_admin(f):
    """Protege la ventana de registro asegurando que el rol sea administrador."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if session.get("rol") != "admin":
            flash("Debes ingresar como Administrador para acceder al Registro de Equipos.", "warning")
            return redirect(url_for("ingreso.login_admin"))
        return f(*args, **kwargs)
    return decorada


def existe_serial(serial):
    """Verifica si el serial ya existe en el archivo CSV."""
    if not os.path.isfile(ARCHIVO_CSV):
        return False

    with open(ARCHIVO_CSV, mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        encabezado_omitido = False
        for fila in reader:
            if not encabezado_omitido:
                encabezado_omitido = True
                continue
            if fila and fila[0].strip().upper() == serial.upper():
                return True
    return False


def validar_tipo_asignacion(codigo):
    """
    Valida el código de Tipo de Asignación:
    - 5 caracteres: 3 letras mayúsculas y 2 números.
    - 1ª letra: 'M' (México) o 'C' (Colombia).
    - 2ª letra: Departamento (A-Z).
    - 3ª letra: Ciudad (A-Z).
    - Últimos 2 caracteres: Oficina (00-99).
    """
    patron = r"^[MC][A-Z]{2}\d{2}$"
    return bool(re.match(patron, codigo))


def guardar_en_csv(datos):
    """Guarda un nuevo registro en el archivo CSV asegurando los encabezados."""
    archivo_existe = os.path.isfile(ARCHIVO_CSV)
    encabezados = [
        "Serial",
        "Número de Activo",
        "Marca",
        "Modelo",
        "Tipo de Asignación",
        "Ciudad",
        "Sitio",
        "Área",
        "Responsable",
        "Estado",
        "Fecha de Compra",
        "Costo",
        "Número de Factura",
        "Proveedor",
        "Fecha de Ingreso",
        "Fecha Registro del Sistema"
    ]

    with open(ARCHIVO_CSV, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        if not archivo_existe:
            writer.writerow(encabezados)
        writer.writerow(datos)


@registro_bp.route("/registro", methods=["GET", "POST"])
@requerir_admin
def registro():
    """Formulario y procesamiento de registro de equipos (solo Administrador)."""
    fecha_actual_ingreso = datetime.now().strftime("%Y-%m-%d")

    if request.method == "POST":
        serial_raw = request.form.get("serial", "")
        serial = serial_raw.replace(" ", "").upper()

        activo = request.form.get("activo", "").strip()
        marca = request.form.get("marca", "").strip()
        modelo = request.form.get("modelo", "").strip()

        tipo_asignacion_raw = request.form.get("tipo_asignacion", "")
        tipo_asignacion = tipo_asignacion_raw.replace(" ", "").upper()

        ciudad = request.form.get("ciudad", "").strip()
        sitio = request.form.get("sitio", "").strip()
        area = request.form.get("area", "").strip()
        responsable = request.form.get("responsable", "").strip()
        estado = request.form.get("estado", "").strip()

        fecha_compra = request.form.get("fecha_compra", "").strip()
        costo_raw = request.form.get("costo", "").strip()
        numero_factura = request.form.get("numero_factura", "").strip().upper()
        proveedor = request.form.get("proveedor", "").strip()

        # Fecha de ingreso asignada de forma 100% automática con la fecha actual
        fecha_ingreso = fecha_actual_ingreso

        # Validación 1: Campos obligatorios
        if not all([serial, activo, marca, modelo, tipo_asignacion, ciudad, sitio, area, responsable, estado, fecha_compra, costo_raw, numero_factura, proveedor]):
            flash("Todos los campos son obligatorios (incluyendo Número de Factura y Proveedor).", "danger")

        # Validación 2: Serial (solo letras y números, mín 7 caracteres, no duplicados)
        elif not serial.isalnum():
            flash("El Serial solo acepta números y letras en mayúsculas (sin caracteres especiales).", "danger")
        elif len(serial) < 7:
            flash(f"El Serial debe tener como mínimo 7 caracteres (ingresaste {len(serial)}).", "danger")
        elif existe_serial(serial):
            flash(f"El Serial '{serial}' ya se encuentra registrado. No se permiten seriales duplicados.", "danger")

        # Validación 3: Número de activo (solo dígitos numéricos)
        elif not activo.isdigit():
            flash("El Número de Activo debe contener únicamente números (sin letras, espacios ni caracteres especiales).", "danger")

        # Validación 4: Tipo de Asignación (formato país, depto, ciudad y oficina)
        elif not validar_tipo_asignacion(tipo_asignacion):
            flash(
                "El Tipo de Asignación debe tener 3 letras y 2 números (ej: CAM01). "
                "La primera letra debe ser 'C' (Colombia) o 'M' (México), "
                "la 2ª el departamento, la 3ª la ciudad y los 2 números la oficina.",
                "danger"
            )

        # Validación 5: Opciones válidas de listas desplegables
        elif marca not in OPCIONES_MARCA:
            flash("La Marca seleccionada no es válida.", "danger")
        elif area not in OPCIONES_AREA:
            flash("El Área seleccionada no es válida.", "danger")
        elif estado not in OPCIONES_ESTADO:
            flash("El Estado seleccionado no es válido.", "danger")

        # Validación 6: Costo numérico válido
        elif not re.match(r"^\d+(\.\d{1,2})?$", costo_raw.replace(",", ".")):
            flash("El Costo debe ser un valor numérico positivo válido (ej: 1500000 o 2500.50).", "danger")

        else:
            try:
                datetime.strptime(fecha_compra, "%Y-%m-%d")
            except ValueError:
                flash("Formato de Fecha de Compra inválido. Debe ser una fecha válida (AAAA-MM-DD).", "danger")
                return render_template(
                    "registro.html",
                    opciones_marca=OPCIONES_MARCA,
                    opciones_area=OPCIONES_AREA,
                    opciones_estado=OPCIONES_ESTADO,
                    fecha_actual_ingreso=fecha_actual_ingreso
                )

            costo_normalizado = f"{float(costo_raw.replace(',', '.')):.2f}"
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            fila = [
                serial,
                activo,
                marca,
                modelo,
                tipo_asignacion,
                ciudad,
                sitio,
                area,
                responsable,
                estado,
                fecha_compra,
                costo_normalizado,
                numero_factura,
                proveedor,
                fecha_ingreso,
                fecha_actual
            ]

            try:
                guardar_en_csv(fila)
                # Registro automático del evento inicial en el historial
                registrar_evento_historial(
                    serial,
                    "Registro Inicial",
                    responsable,
                    estado,
                    f"Ingreso de la PDA al sistema asignada a {ciudad} - {sitio} ({tipo_asignacion}). Factura: {numero_factura}, Proveedor: {proveedor}."
                )
                flash(f"¡Equipo con Serial '{serial}' y Activo '{activo}' registrado exitosamente en el archivo CSV!", "success")
                return redirect(url_for("registro.registro"))
            except Exception as e:
                flash(f"Error al guardar en el archivo CSV: {str(e)}", "danger")

    return render_template(
        "registro.html",
        opciones_marca=OPCIONES_MARCA,
        opciones_area=OPCIONES_AREA,
        opciones_estado=OPCIONES_ESTADO,
        fecha_actual_ingreso=fecha_actual_ingreso
    )
