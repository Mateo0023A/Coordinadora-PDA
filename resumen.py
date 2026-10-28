import os
import csv
from collections import defaultdict
from flask import Blueprint, render_template, session

resumen_bp = Blueprint("resumen", __name__)

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_EQUIPOS = os.path.join(DIRECTORIO_ACTUAL, "equipos_registrados.csv")

OPCIONES_ESTADO = [
    "En bodega",
    "En repartición",
    "En uso",
    "En reparación",
    "Dado de baja",
    "Perdido"
]


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
            if len(fila) >= 10:
                equipos.append({
                    "serial": fila[0].strip(),
                    "activo": fila[1].strip() if len(fila) > 1 else "",
                    "marca": fila[2].strip() if len(fila) > 2 else "",
                    "modelo": fila[3].strip() if len(fila) > 3 else "",
                    "tipo_asignacion": fila[4].strip() if len(fila) > 4 else "Sin Asignar",
                    "ciudad": fila[5].strip() if len(fila) > 5 else "",
                    "sitio": fila[6].strip() if len(fila) > 6 else "",
                    "area": fila[7].strip() if len(fila) > 7 else "",
                    "responsable": fila[8].strip() if len(fila) > 8 else "",
                    "estado": fila[9].strip() if len(fila) > 9 else "Desconocido",
                })
    return equipos


def calcular_resumen():
    """
    Calcula los tres datos solicitados:
    1. Cuántas PDAs hay en total.
    2. Cuántas en cada estado.
    3. Cuántas en cada terminal (tipo de asignación).
    """
    equipos = leer_equipos()
    total_pdas = len(equipos)

    # 1. Conteo por Estado
    conteo_estado = {estado: 0 for estado in OPCIONES_ESTADO}
    for eq in equipos:
        st = eq["estado"].strip()
        encontrado = False
        for est_oficial in OPCIONES_ESTADO:
            if st.lower() == est_oficial.lower():
                conteo_estado[est_oficial] += 1
                encontrado = True
                break
        if not encontrado and st:
            conteo_estado[st] = conteo_estado.get(st, 0) + 1

    # Estructura enriquecida por estado con porcentaje
    resumen_estados = []
    for estado, cantidad in conteo_estado.items():
        porcentaje = round((cantidad / total_pdas * 100), 1) if total_pdas > 0 else 0
        resumen_estados.append({
            "estado": estado,
            "cantidad": cantidad,
            "porcentaje": porcentaje
        })

    # 2. Conteo por Terminal (Tipo de Asignación)
    terminales_dict = defaultdict(lambda: {
        "cantidad": 0,
        "ciudades": set(),
        "sitios": set(),
        "seriales": []
    })

    for eq in equipos:
        term = eq["tipo_asignacion"] if eq["tipo_asignacion"] else "Sin Terminal"
        terminales_dict[term]["cantidad"] += 1
        if eq["ciudad"]:
            terminales_dict[term]["ciudades"].add(eq["ciudad"])
        if eq["sitio"]:
            terminales_dict[term]["sitio_nombre"] = eq["sitio"]
            terminales_dict[term]["sitios"].add(eq["sitio"])
        terminales_dict[term]["seriales"].append(eq["serial"])

    # Estructura enriquecida por terminal ordenada alfabéticamente
    resumen_terminales = []
    for terminal in sorted(terminales_dict.keys()):
        info = terminales_dict[terminal]
        porcentaje = round((info["cantidad"] / total_pdas * 100), 1) if total_pdas > 0 else 0
        ciudades_str = ", ".join(sorted(info["ciudades"])) if info["ciudades"] else "N/A"
        sitios_str = ", ".join(sorted(info["sitios"])) if info["sitios"] else "N/A"

        resumen_terminales.append({
            "terminal": terminal,
            "cantidad": info["cantidad"],
            "porcentaje": porcentaje,
            "ciudades": ciudades_str,
            "sitios": sitios_str,
            "seriales": info["seriales"]
        })

    return {
        "total_pdas": total_pdas,
        "por_estado": resumen_estados,
        "por_terminal": resumen_terminales
    }


@resumen_bp.route("/resumen", methods=["GET"])
@resumen_bp.route("/usuario/resumen", methods=["GET"])
def resumen_pdas():
    """Pantalla con el resumen general de PDAs (total, por estado y por terminal)."""
    if "rol" not in session:
        session["rol"] = "usuario"

    datos_resumen = calcular_resumen()

    return render_template(
        "resumen.html",
        total_pdas=datos_resumen["total_pdas"],
        resumen_estados=datos_resumen["por_estado"],
        resumen_terminales=datos_resumen["por_terminal"]
    )
