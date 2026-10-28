import os
import csv
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_EQUIPOS = os.path.join(DIRECTORIO_ACTUAL, "equipos_registrados.csv")
ARCHIVO_HISTORIAL = os.path.join(DIRECTORIO_ACTUAL, "historial_equipos.csv")

OPCIONES_ESTADO = [
    "En bodega",
    "En repartición",
    "En uso",
    "En reparación",
    "Dado de baja",
    "Perdido"
]

historial_bp = Blueprint("historial", __name__)


def validar_tipo_asignacion(codigo):
    """Valida formato 3 letras mayúsculas y 2 números (1ª M o C)."""
    patron = r"^[MC][A-Z]{2}\d{2}$"
    return bool(re.match(patron, codigo))


def leer_equipos():
    """Lee todos los equipos del archivo CSV y retorna una lista de diccionarios."""
    if not os.path.isfile(ARCHIVO_EQUIPOS):
        return []

    equipos = []
    with open(ARCHIVO_EQUIPOS, mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        encabezados_leidos = False
        for fila in reader:
            if not encabezados_leidos:
                encabezados_leidos = True
                continue
            if len(fila) >= 16:
                equipos.append({
                    "serial": fila[0].strip(),
                    "activo": fila[1].strip(),
                    "marca": fila[2].strip(),
                    "modelo": fila[3].strip(),
                    "tipo_asignacion": fila[4].strip(),
                    "ciudad": fila[5].strip(),
                    "sitio": fila[6].strip(),
                    "area": fila[7].strip(),
                    "responsable": fila[8].strip(),
                    "estado": fila[9].strip(),
                    "fecha_compra": fila[10].strip(),
                    "costo": fila[11].strip(),
                    "numero_factura": fila[12].strip(),
                    "proveedor": fila[13].strip(),
                    "fecha_ingreso": fila[14].strip(),
                    "fecha_registro": fila[15].strip(),
                })
            elif len(fila) >= 14:
                equipos.append({
                    "serial": fila[0].strip(),
                    "activo": fila[1].strip(),
                    "marca": fila[2].strip(),
                    "modelo": fila[3].strip(),
                    "tipo_asignacion": fila[4].strip(),
                    "ciudad": fila[5].strip(),
                    "sitio": fila[6].strip(),
                    "area": fila[7].strip(),
                    "responsable": fila[8].strip(),
                    "estado": fila[9].strip(),
                    "fecha_compra": fila[10].strip(),
                    "costo": fila[11].strip(),
                    "numero_factura": "N/A",
                    "proveedor": "N/A",
                    "fecha_ingreso": fila[12].strip(),
                    "fecha_registro": fila[13].strip(),
                })
    return equipos


def obtener_equipo_por_serial(serial):
    """Busca un equipo específico por su Serial."""
    for eq in leer_equipos():
        if eq["serial"].upper() == serial.strip().upper():
            return eq
    return None


def actualizar_equipo_csv(serial, nueva_terminal, nuevo_responsable, nuevo_estado):
    """Actualiza la terminal, responsable y estado del equipo en equipos_registrados.csv."""
    if not os.path.isfile(ARCHIVO_EQUIPOS):
        return False

    filas_actualizadas = []
    actualizado = False

    with open(ARCHIVO_EQUIPOS, mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        encabezados = next(reader, None)
        if encabezados:
            filas_actualizadas.append(encabezados)

        for fila in reader:
            if fila and fila[0].strip().upper() == serial.strip().upper():
                # Actualizar col 4 (Terminal/Tipo asignación), col 8 (Responsable), col 9 (Estado)
                fila[4] = nueva_terminal
                fila[8] = nuevo_responsable
                fila[9] = nuevo_estado
                actualizado = True
            filas_actualizadas.append(fila)

    if actualizado:
        with open(ARCHIVO_EQUIPOS, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerows(filas_actualizadas)

    return actualizado


def leer_historial_equipo(serial):
    """Obtiene todos los eventos del historial para un serial dado."""
    historial = []
    if os.path.isfile(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            encabezado_leido = False
            for fila in reader:
                if not encabezado_leido:
                    encabezado_leido = True
                    continue
                if fila and fila[0].strip().upper() == serial.strip().upper():
                    historial.append({
                        "serial": fila[0].strip(),
                        "fecha": fila[1].strip() if len(fila) > 1 else "",
                        "evento": fila[2].strip() if len(fila) > 2 else "",
                        "responsable": fila[3].strip() if len(fila) > 3 else "",
                        "estado": fila[4].strip() if len(fila) > 4 else "",
                        "observacion": fila[5].strip() if len(fila) > 5 else "",
                    })

    # Si no tiene registros previos en historial_equipos.csv, generamos el inicial
    if not historial:
        equipo = obtener_equipo_por_serial(serial)
        if equipo:
            historial.append({
                "serial": equipo["serial"],
                "fecha": equipo["fecha_ingreso"] or equipo["fecha_registro"],
                "evento": "Registro Inicial",
                "responsable": equipo["responsable"],
                "estado": equipo["estado"],
                "observacion": f"Ingreso inicial de la PDA asignada a {equipo['ciudad']} - {equipo['sitio']} ({equipo['tipo_asignacion']})."
            })
    return historial


def registrar_evento_historial(serial, evento, responsable, estado, observacion):
    """Guarda automáticamente un evento con fecha y hora actual en historial_equipos.csv."""
    archivo_existe = os.path.isfile(ARCHIVO_HISTORIAL)
    encabezados = ["Serial", "Fecha", "Evento", "Responsable", "Estado", "Observación"]
    # Fecha y hora automática del cambio
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fila = [serial.strip().upper(), fecha_actual, evento, responsable, estado, observacion]

    with open(ARCHIVO_HISTORIAL, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        if not archivo_existe:
            writer.writerow(encabezados)
        writer.writerow(fila)


@historial_bp.route("/usuario/pdas", methods=["GET"])
def lista_pdas():
    """Listado de todas las PDAs con filtros interactivos."""
    session["rol"] = "usuario"

    filtro_serial = request.args.get("serial", "").strip()
    filtro_ciudad = request.args.get("ciudad", "").strip()
    filtro_estado = request.args.get("estado", "").strip()
    filtro_responsable = request.args.get("responsable", "").strip()

    todos_los_equipos = leer_equipos()

    ciudades_disponibles = sorted(list(set(eq["ciudad"] for eq in todos_los_equipos if eq.get("ciudad"))))
    estados_disponibles = sorted(list(set(eq["estado"] for eq in todos_los_equipos if eq.get("estado"))))
    responsables_disponibles = sorted(list(set(eq["responsable"] for eq in todos_los_equipos if eq.get("responsable"))))

    equipos_filtrados = []
    for eq in todos_los_equipos:
        if filtro_serial and (filtro_serial.upper() not in eq["serial"].upper()):
            continue
        if filtro_ciudad and (filtro_ciudad.lower() != eq.get("ciudad", "").lower()):
            continue
        if filtro_estado and (filtro_estado.lower() != eq.get("estado", "").lower()):
            continue
        if filtro_responsable and (filtro_responsable.lower() not in eq.get("responsable", "").lower()):
            continue
        equipos_filtrados.append(eq)

    return render_template(
        "usuario_pdas.html",
        equipos=equipos_filtrados,
        total_pdas=len(equipos_filtrados),
        ciudades=ciudades_disponibles,
        estados=estados_disponibles,
        responsables=responsables_disponibles,
        filtro_serial=filtro_serial,
        filtro_ciudad=filtro_ciudad,
        filtro_estado=filtro_estado,
        filtro_responsable=filtro_responsable
    )


@historial_bp.route("/usuario/pda/<serial>", methods=["GET", "POST"])
def detalle_pda(serial):
    """
    Ficha de PDA y formulario para registrar:
    - Traslado a otra terminal
    - Cambio de responsable
    - Cambio de estado
    - Comentario opcional
    Registra fecha y hora automáticamente en el CSV de historial.
    """
    session["rol"] = "usuario"
    equipo = obtener_equipo_por_serial(serial)

    if not equipo:
        flash(f"No se encontró ninguna PDA con el serial '{serial}'.", "danger")
        return redirect(url_for("historial.lista_pdas"))

    if request.method == "POST":
        terminal_input = request.form.get("terminal", "").replace(" ", "").upper()
        nuevo_responsable = request.form.get("responsable", "").strip()
        nuevo_estado = request.form.get("estado", "").strip()
        comentario = request.form.get("comentario", "").strip()

        # Validaciones
        if not terminal_input or not nuevo_responsable or not nuevo_estado:
            flash("La terminal, el responsable y el estado son campos obligatorios.", "danger")
        elif not validar_tipo_asignacion(terminal_input):
            flash(
                "El formato de la Terminal debe ser de 3 letras (iniciando por C o M) y 2 números (ej: CAM01).",
                "danger"
            )
        elif nuevo_estado not in OPCIONES_ESTADO:
            flash("El estado seleccionado no es válido.", "danger")
        else:
            # Detección de cambios
            cambios = []
            if terminal_input != equipo["tipo_asignacion"]:
                cambios.append(f"Traslado de terminal: '{equipo['tipo_asignacion']}' → '{terminal_input}'")
            if nuevo_responsable.lower() != equipo["responsable"].lower():
                cambios.append(f"Cambio de responsable: '{equipo['responsable']}' → '{nuevo_responsable}'")
            if nuevo_estado != equipo["estado"]:
                cambios.append(f"Cambio de estado: '{equipo['estado']}' → '{nuevo_estado}'")

            if not cambios and not comentario:
                flash("No se detectaron cambios en el equipo ni se ingresó un comentario.", "info")
            else:
                # Definición del tipo de evento
                if len(cambios) == 1:
                    if "Traslado de terminal" in cambios[0]:
                        tipo_evento = "Traslado a otra Terminal"
                    elif "Cambio de responsable" in cambios[0]:
                        tipo_evento = "Cambio de Responsable"
                    else:
                        tipo_evento = "Cambio de Estado"
                elif len(cambios) > 1:
                    tipo_evento = "Modificación de PDA"
                else:
                    tipo_evento = "Observación de Seguimiento"

                # Construcción del texto de observación
                partes_obs = []
                if cambios:
                    partes_obs.append("; ".join(cambios))
                if comentario:
                    partes_obs.append(f"Comentario: {comentario}")
                detalle_observacion = " | ".join(partes_obs) if partes_obs else "Sin comentarios adicionales."

                # 1. Actualizar el registro principal en equipos_registrados.csv
                actualizar_equipo_csv(serial, terminal_input, nuevo_responsable, nuevo_estado)

                # 2. Registrar en historial_equipos.csv con fecha y hora automática
                registrar_evento_historial(serial, tipo_evento, nuevo_responsable, nuevo_estado, detalle_observacion)

                flash(
                    f"¡Cambio registrado exitosamente! La PDA ha sido actualizada y el historial guardó la fecha y hora.",
                    "success"
                )
                return redirect(url_for("historial.detalle_pda", serial=serial))

    historial = leer_historial_equipo(serial)
    return render_template(
        "pda_detalle.html",
        equipo=equipo,
        historial=historial,
        opciones_estado=OPCIONES_ESTADO
    )
