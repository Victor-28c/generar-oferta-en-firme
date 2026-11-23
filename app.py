"""
app.py — Generador de la oferta en firme (Streamlit).

Pide a mano todos los datos de la oferta, muestra los cálculos y las alertas,
y con un botón genera el PDF. Lo que se deje vacío sale en [corchetes].

Correr en local:   streamlit run app.py
"""

import datetime as dt

import streamlit as st

from calculos import COBERTURA, PISO_PRECIO, Entradas, calcular
from formato import MESES_LARGOS, etiquetas_meses, fecha, fecha_corta, num, pesos, porc
from pdf_oferta import generar_pdf

st.set_page_config(page_title="Oferta en firme", page_icon="☀️", layout="wide")

# =========================================================
# VALORES INICIALES Y DATOS DE EJEMPLO
# =========================================================

HOY = dt.date.today()
TEXTOS = ["numero", "cliente", "num_doc", "niu", "sic", "direccion", "comercializador", "operador",
          "tel_cliente", "correo_cliente", "comunidad", "representante", "registro_mme", "tel_rep", "correo_rep",
          "tipo_planta", "ubicacion_planta", "comercializador_ce", "entrada_operacion", "fuente_consumo",
          "compensacion", "req_al_dia", "cambio_comercializador", "medidor_requerido", "costo_medidor",
          "fecha_limite_inicio", "permanencia", "retiro", "enlace_datos", "whatsapp", "correo_ce", "fecha_inicio",
          "asesor", "cargo_asesor", "tel_asesor", "correo_asesor"]
NUMEROS = ["kwp", "cu", "cv", "cuota_admin", "aporte_ingreso", "generacion_planta"] + [f"c{i}" for i in range(12)]
OPCIONES = {
    "tipo_doc": ["", "CC", "NIT", "CE"],
    "tipo_usuario": ["", "Residencial", "Comercial", "Industrial", "Oficial"],
    "medidor": ["", "Convencional", "Bidireccional", "Horario", "Inteligente"],
    "contribucion": ["", "Sí paga", "No paga"],
    "forma_pago": ["", "Cobro mensual de la comunidad", "En la factura del comercializador"],
}

EJEMPLO = {
    "numero": "OF-2026-0001", "dias": 30,
    "cliente": "Lavandería Industrial Suárez S.A.S.", "tipo_doc": "NIT", "num_doc": "901.234.567-8",
    "niu": "1234567", "direccion": "Calle 10 # 20-30, Bogotá, Cundinamarca", "tipo_usuario": "Comercial",
    "contribucion": "Sí paga", "comercializador": "Enel Colombia", "operador": "Enel Colombia",
    "medidor": "Bidireccional", "tel_cliente": "300 000 0000", "correo_cliente": "contacto@ejemplo.co",
    "comunidad": "We Club Sabana", "registro_mme": "En trámite", "tipo_planta": "Solar fotovoltaica",
    "kwp": 1000.0, "ubicacion_planta": "Mosquera", "comercializador_ce": "Enel Colombia",
    "entrada_operacion": "01/03/2027", "fuente_consumo": "tu factura y el historial de Enel",
    "mes_reciente": "Octubre", "anio_reciente": 2026,
    **{f"c{i}": float(x) for i, x in enumerate([12500, 14000, 15200, 15000, 15600, 14800,
                                                15400, 16000, 15500, 15800, 16100, 14100])},
    "cu": 915.0, "cv": 130.0, "descuento": 10.0, "cuota_admin": 0.0, "aporte_ingreso": 0.0,
    "generacion_planta": 150000.0, "forma_pago": "Cobro mensual de la comunidad",
    "req_al_dia": "y estar al día con tu factura", "medidor_requerido": "bidireccional",
    "costo_medidor": "Lo asume la comunidad", "fecha_limite_inicio": "30/04/2027",
}


def iniciar():
    for k in TEXTOS:
        st.session_state.setdefault(k, "")
    for k in NUMEROS:
        st.session_state.setdefault(k, None)
    for k, opciones in OPCIONES.items():
        st.session_state.setdefault(k, opciones[0])
    st.session_state.setdefault("emision", HOY)
    st.session_state.setdefault("dias", 30)
    st.session_state.setdefault("estrato", 4)
    st.session_state.setdefault("descuento", 10.0)
    mes_pasado = (HOY.replace(day=1) - dt.timedelta(days=1))
    st.session_state.setdefault("mes_reciente", MESES_LARGOS[mes_pasado.month - 1])
    st.session_state.setdefault("anio_reciente", mes_pasado.year)


def limpiar():
    for k in TEXTOS:
        st.session_state[k] = ""
    for k in NUMEROS:
        st.session_state[k] = None
    for k, opciones in OPCIONES.items():
        st.session_state[k] = opciones[0]
    st.session_state.pop("pdf", None)


def cargar_ejemplo():
    limpiar()
    for k, valor in EJEMPLO.items():
        st.session_state[k] = valor


iniciar()


def opcion(etiqueta, key, **kw):
    return st.selectbox(etiqueta, OPCIONES[key], key=key,
                        format_func=lambda x: x or "— sin definir (sale en corchetes) —", **kw)


def numero(etiqueta, key, **kw):
    return st.number_input(etiqueta, min_value=0.0, key=key, placeholder="vacío", **kw)


# =========================================================
# BARRA LATERAL
# =========================================================

with st.sidebar:
    st.header("☀️ Oferta en firme")
    st.button("Cargar datos de ejemplo", on_click=cargar_ejemplo)
    st.button("Limpiar todo", on_click=limpiar)
    st.caption("Lo que dejes vacío sale en el PDF como [corchete] verde, para que se note qué falta.")
    st.caption(f"Parámetros fijos: energía garantizada = {porc(COBERTURA, 0)} del mes más bajo · "
               f"piso del precio {pesos(PISO_PRECIO, 2)}/kWh.")

st.title("Generador de la oferta en firme")
st.caption("Llena las pestañas → revisa los cálculos y alertas de abajo → genera el PDF.")

t1, t2, t3, t4, t5, t6 = st.tabs(["1. Oferta", "2. Cliente", "3. Comunidad", "4. Consumo",
                                  "5. Tarifa y precio", "6. Condiciones y contacto"])

# ---------------- 1. Oferta ----------------
with t1:
    a, b, c = st.columns(3)
    a.text_input("Número de la oferta", key="numero", placeholder="OF-2026-0001")
    b.date_input("Fecha de emisión", key="emision", format="DD/MM/YYYY")
    c.number_input("Días de vigencia", min_value=1, max_value=365, step=1, key="dias")
    valida = st.session_state["emision"] + dt.timedelta(days=int(st.session_state["dias"]))
    st.info(f"Válida hasta el **{fecha(valida)}** (fecha de emisión + {st.session_state['dias']} días). "
            "El cliente tiene hasta esa fecha para aceptar o rechazar.")

# ---------------- 2. Cliente ----------------
with t2:
    st.caption("Estos datos salen de la factura y de los documentos del cliente.")
    a, b = st.columns(2)
    a.text_input("Nombre o razón social (titular de la factura)", key="cliente")
    with b:
        x, y = st.columns([1, 2])
        with x:
            opcion("Tipo de documento", "tipo_doc")
        y.text_input("Número de documento", key="num_doc")
    a, b = st.columns(2)
    a.text_input("NIU (número de cuenta en la factura)", key="niu")
    b.text_input("Código de frontera SIC (si aplica)", key="sic")
    st.text_input("Dirección del predio (dirección, municipio, departamento)", key="direccion")
    a, b, c = st.columns(3)
    with a:
        opcion("Tipo de usuario", "tipo_usuario")
    if st.session_state["tipo_usuario"] == "Residencial":
        b.number_input("Estrato", min_value=1, max_value=6, step=1, key="estrato")
    with c:
        # CONTRIBUCIÓN: se llena al escanear la factura y se confirma si paga o no.
        # Si paga, vale 20 %; si no, vale 0.
        opcion("¿Paga contribución? (según la factura)", "contribucion")
    a, b, c = st.columns(3)
    a.text_input("Comercializador actual", key="comercializador")
    b.text_input("Operador de red", key="operador")
    with c:
        opcion("Tipo de medidor", "medidor")
    a, b = st.columns(2)
    a.text_input("Teléfono del cliente", key="tel_cliente")
    b.text_input("Correo del cliente", key="correo_cliente")

# ---------------- 3. Comunidad ----------------
with t3:
    a, b = st.columns(2)
    a.text_input("Nombre de la comunidad", key="comunidad")
    b.text_input("Registro ante el Ministerio de Minas y Energía", key="registro_mme", placeholder="Número o 'En trámite'")
    a, b, c = st.columns(3)
    a.text_input("Representante (nombre y documento)", key="representante")
    b.text_input("Teléfono del representante", key="tel_rep")
    c.text_input("Correo del representante", key="correo_rep")
    a, b, c = st.columns(3)
    a.text_input("Tipo de planta", key="tipo_planta", placeholder="Solar fotovoltaica")
    with b:
        numero("Capacidad de la planta (kWp)", "kwp", step=10.0, format="%.0f")
    c.text_input("Ubicación de la planta", key="ubicacion_planta")
    a, b = st.columns(2)
    a.text_input("Comercializador de la comunidad", key="comercializador_ce")
    b.text_input("Entrada en operación estimada", key="entrada_operacion", placeholder="DD/MM/AAAA")

# ---------------- 4. Consumo ----------------
with t4:
    st.caption("Los 12 meses salen de la factura (trae 6) y del portal del operador de red (los otros 6).")
    a, b, c = st.columns([1, 1, 2])
    a.selectbox("Mes más reciente", MESES_LARGOS, key="mes_reciente")
    b.number_input("Año", min_value=2020, max_value=2100, step=1, key="anio_reciente")
    c.text_input("Fuente del consumo (sale en la oferta)", key="fuente_consumo",
                 placeholder="tu factura y el historial de tu operador de red")
    meses = etiquetas_meses(MESES_LARGOS.index(st.session_state["mes_reciente"]) + 1,
                            int(st.session_state["anio_reciente"]))
    for fila in (range(0, 6), range(6, 12)):
        cols = st.columns(6)
        for col, i in zip(cols, fila):
            with col:
                numero(f"{meses[i]} (kWh)", f"c{i}", step=100.0, format="%.0f")

# ---------------- 5. Tarifa y precio ----------------
with t5:
    st.caption("CU y Cv salen de la factura (o de la tarifa que publica el comercializador ese mes).")
    a, b, c = st.columns(3)
    with a:
        numero("CU de su comercializador ($/kWh)", "cu", step=1.0, format="%.2f")
    with b:
        numero("Cv, costo de comercialización ($/kWh)", "cv", step=1.0, format="%.2f")
    # PRECIO POR kWh: sale del descuento sobre el CU. A futuro, este valor lo puede
    # ajustar el asesor en el CRM antes de enviar la oferta.
    c.number_input("Descuento sobre el CU (%) — lo elige el asesor", min_value=0.0, max_value=99.0,
                   step=0.5, key="descuento")
    a, b, c = st.columns(3)
    with a:
        numero("Cuota de administración ($/mes) — 0 = no aplica", "cuota_admin", step=10000.0, format="%.0f")
    with b:
        numero("Aporte de ingreso ($, una vez) — 0 = sin costo", "aporte_ingreso", step=10000.0, format="%.0f")
    with c:
        opcion("Cómo se paga", "forma_pago")
    numero("Generación mensual estimada de la planta (kWh/mes) — interno, solo para revisar el PDE",
           "generacion_planta", step=1000.0, format="%.0f")

# ---------------- 6. Condiciones y contacto ----------------
with t6:
    st.text_input("Si un mes no le llega la energía garantizada (compensación)", key="compensacion",
                  placeholder="mecanismo de compensación por definir")
    a, b = st.columns(2)
    a.text_input("Requisito de estar al día", key="req_al_dia", placeholder="y estar al día con tu factura")
    b.text_input("Si tiene otro comercializador", key="cambio_comercializador", placeholder="te acompañamos en el cambio")
    a, b = st.columns(2)
    a.text_input("Medidor requerido", key="medidor_requerido", placeholder="bidireccional")
    b.text_input("Quién asume el costo del medidor", key="costo_medidor", placeholder="Lo asume la comunidad")
    a, b = st.columns(2)
    a.text_input("Fecha límite para que la planta arranque (si no, desiste sin costo)", key="fecha_limite_inicio",
                 placeholder="DD/MM/AAAA")
    b.text_input("Fecha estimada en que empieza a recibir energía", key="fecha_inicio", placeholder="DD/MM/AAAA")
    a, b = st.columns(2)
    a.text_input("Permanencia", key="permanencia", placeholder="Sin permanencia mínima / permanencia de __ meses")
    b.text_input("Cómo puede retirarse", key="retiro")
    st.text_input("Enlace a la política de datos", key="enlace_datos")
    a, b = st.columns(2)
    a.text_input("WhatsApp para aceptar o rechazar", key="whatsapp")
    b.text_input("Correo para aceptar o rechazar", key="correo_ce")
    a, b, c, e = st.columns(4)
    a.text_input("Asesor", key="asesor")
    b.text_input("Cargo", key="cargo_asesor")
    c.text_input("Teléfono del asesor", key="tel_asesor")
    e.text_input("Correo del asesor", key="correo_asesor")

# =========================================================
# CÁLCULOS
# =========================================================

ss = st.session_state
consumos = [ss[f"c{i}"] for i in range(12)]
contribucion = {"Sí paga": True, "No paga": False}.get(ss["contribucion"])
entradas = Entradas(
    consumos=consumos, meses=meses, cu=ss["cu"] or 0, cv=ss["cv"],
    paga_contribucion=bool(contribucion), descuento=(ss["descuento"] or 0) / 100,
    cuota_admin=ss["cuota_admin"] or 0, aporte_ingreso=ss["aporte_ingreso"] or 0,
    generacion_planta=ss["generacion_planta"] or 0,
    estrato=ss["estrato"] if ss["tipo_usuario"] == "Residencial" else None,
)
bloqueos, alertas, r = calcular(entradas)

st.divider()
st.subheader("Cálculos de la oferta")
if contribucion is None:
    st.warning("Falta confirmar si paga contribución (pestaña 2). Mientras tanto se calcula como si **no** pagara.")
if bloqueos:
    for b in bloqueos:
        st.error(b)
    st.caption("Mientras haya errores, las cifras salen en [corchetes] en el PDF.")
else:
    m = st.columns(3)
    m[0].metric("Energía garantizada (kWh/mes)", num(r.energia_garantizada))
    m[1].metric("Precio por kWh (inicial)", pesos(r.precio_ce, 2))
    m[2].metric("Ahorro por kWh", pesos(r.ahorro_kwh, 2), f"{porc(r.ahorro_pct_kwh)} de lo que paga hoy")
    m = st.columns(3)
    m[0].metric("Ahorro al mes", pesos(r.ahorro_mes))
    m[1].metric("Ahorro al año", pesos(r.ahorro_anio))
    m[2].metric("Ahorro neto año 1", pesos(r.ahorro_neto_anio1))
    for a_ in alertas:
        st.warning(a_)
    if not alertas:
        st.success("Cumple todas las revisiones.")
    with st.expander("Ver el cálculo paso a paso"):
        st.markdown(f"""
1. **Mes más bajo:** de los 12 meses, el menor es {r.mes_bajo_etiqueta} con **{num(r.mes_bajo)} kWh**. Promedio: {num(r.promedio)} kWh/mes.
2. **Energía garantizada:** cojo {num(r.mes_bajo)} y lo multiplico por {porc(COBERTURA, 0)} → **{num(r.energia_garantizada)} kWh/mes** ({porc(r.cobertura_promedio)} de su consumo promedio).
3. **Precio de la comunidad:** cojo el CU {pesos(entradas.cu, 2)}, le quito el {porc(entradas.descuento)} y le resto el Cv {pesos(entradas.cv, 2)} → **{pesos(r.precio_ce, 2)}/kWh**.
4. **Total que paga por kWh de la comunidad:** {pesos(r.precio_ce, 2)} + Cv {pesos(entradas.cv, 2)} = **{pesos(r.total_kwh, 2)}**.
5. **Lo que paga hoy por kWh:** CU {pesos(entradas.cu, 2)} × (1 + contribución {porc(r.contribucion, 0)}) = **{pesos(r.paga_hoy_kwh, 2)}**.
6. **Ahorro por kWh:** {pesos(r.paga_hoy_kwh, 2)} − {pesos(r.total_kwh, 2)} = **{pesos(r.ahorro_kwh, 2)}**.
7. **Ahorro al mes:** {num(r.energia_garantizada)} kWh × {pesos(r.ahorro_kwh, 2)} = **{pesos(r.ahorro_mes)}**; al año × 12 = **{pesos(r.ahorro_anio)}**.
8. **Ahorro neto año 1:** {pesos(r.ahorro_anio)} − cuota y aporte {pesos(r.costos_anio1)} = **{pesos(r.ahorro_neto_anio1)}**.
""" + (f"9. **PDE de referencia:** {num(r.energia_garantizada)} ÷ {num(entradas.generacion_planta)} = **{porc(r.pde, 2)}** (tiene que ser < 10 %)." if r.pde else ""))

# =========================================================
# GENERAR EL PDF
# =========================================================

st.divider()
datos = {k: ss[k] for k in TEXTOS}
datos.update({
    "emision": fecha(ss["emision"]), "dias": ss["dias"], "valida_hasta": fecha(valida),
    "valida_hasta_corta": fecha_corta(valida), "tipo_doc": ss["tipo_doc"], "tipo_usuario": ss["tipo_usuario"],
    "estrato": ss["estrato"] if ss["tipo_usuario"] == "Residencial" else None,
    "paga_contribucion": contribucion, "medidor": ss["medidor"], "forma_pago": ss["forma_pago"],
    "kwp": ss["kwp"], "cv": ss["cv"], "cuota_admin": ss["cuota_admin"], "aporte_ingreso": ss["aporte_ingreso"],
    "meses": meses, "consumos": consumos,
})

if st.button("Generar oferta en PDF", type="primary"):
    ss["pdf"] = generar_pdf(datos, None if bloqueos else r)

if ss.get("pdf"):
    nombre = f"Oferta_{(ss['numero'] or 'borrador').replace(' ', '_')}.pdf"
    st.success("Listo. Descarga la oferta:")
    st.download_button("⬇️ Descargar PDF", ss["pdf"], file_name=nombre, mime="application/pdf")
