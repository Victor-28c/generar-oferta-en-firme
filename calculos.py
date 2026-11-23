"""
calculos.py — Las cuentas de la oferta en firme.

No dibuja nada ni pide datos: recibe las entradas y devuelve los resultados,
los bloqueos (no se puede generar la oferta) y las alertas (se puede, pero hay
que revisarla).
"""

from __future__ import annotations

from dataclasses import dataclass

from formato import num, pesos, porc

# =========================================================
# PARÁMETROS (política comercial y regulación)
# =========================================================

COBERTURA = 0.80            # parte del mes de menor consumo que se garantiza
TASA_CONTRIBUCION = 0.20    # contribución de solidaridad (comerciales, industriales, estratos 5 y 6)
PDE_MAXIMO = 0.099          # la norma pide < 10 % por usuario (Art. 20 num. 1, Res. CREG 101 072 de 2025)
CONSUMO_MINIMO_KWH = 4_500  # por debajo de esto no se cotiza (RN-011)
UMBRAL_MES_ATIPICO = 0.60   # mes más bajo < 60 % del promedio -> revisar si fue puntual
AHORRO_MINIMO = 0.10        # ahorro mínimo aceptable por kWh para el usuario
PISO_PRECIO = 641.61        # $/kWh: precio de la comunidad con el que el vehículo gana el mínimo (Excel)


@dataclass
class Entradas:
    consumos: list[float]       # 12 meses, del más antiguo al más reciente (kWh)
    meses: list[str]            # etiqueta de cada mes, en el mismo orden
    cu: float                   # costo unitario de su comercializador ($/kWh)
    cv: float | None            # costo de comercialización ($/kWh)

    # CONTRIBUCIÓN: esta variable se llena al escanear la factura y se confirma
    # si el usuario paga o no paga contribución. Si paga, vale 20 %; si no, vale 0.
    paga_contribucion: bool

    # Descuento sobre el CU con el que se fija el precio inicial (lo elige el asesor).
    descuento: float

    cuota_admin: float = 0.0          # $/mes (0 = no aplica)
    aporte_ingreso: float = 0.0       # $ una sola vez (0 = sin costo)
    generacion_planta: float = 0.0    # kWh/mes de la planta (opcional, solo para revisar el PDE)
    estrato: int | None = None        # solo residenciales


@dataclass
class Resultados:
    promedio: float
    mes_bajo: float
    mes_bajo_etiqueta: str
    energia_garantizada: float
    cobertura_promedio: float
    contribucion: float
    precio_ce: float
    total_kwh: float
    paga_hoy_kwh: float
    ahorro_kwh: float
    ahorro_pct_kwh: float
    ahorro_mes: float
    ahorro_anio: float
    costos_anio1: float
    ahorro_neto_anio1: float
    pde: float | None


def calcular(e: Entradas) -> tuple[list[str], list[str], Resultados | None]:
    """Devuelve (bloqueos, alertas, resultados). Con bloqueos no hay resultados."""
    bloqueos: list[str] = []
    alertas: list[str] = []

    # ---------- Restricciones que impiden generar la oferta ----------
    if len(e.consumos) != 12 or any((c is None or c <= 0) for c in e.consumos):
        bloqueos.append("Faltan meses de consumo: se necesitan los 12, todos mayores que 0.")
    if not e.cu or e.cu <= 0:
        bloqueos.append("Falta el CU de su comercializador.")
    if e.cv is None:
        bloqueos.append("Falta el Cv (costo de comercialización).")
    elif e.cv < 0 or (e.cu and e.cv >= e.cu):
        bloqueos.append("El Cv tiene que ser mayor o igual a 0 y menor que el CU.")
    if not 0 <= e.descuento < 1:
        bloqueos.append("El descuento tiene que estar entre 0 % y menos de 100 %.")
    if bloqueos:
        return bloqueos, alertas, None

    # ---------- Consumo ----------
    promedio = sum(e.consumos) / 12
    mes_bajo = min(e.consumos)
    mes_bajo_etiqueta = e.meses[e.consumos.index(mes_bajo)]

    # ---------- Energía garantizada: 80 % del mes de menor consumo ----------
    energia = mes_bajo * COBERTURA
    cobertura_promedio = energia / promedio

    # ---------- Precio ----------
    # PRECIO POR kWh QUE SE LE VENDE AL USUARIO.
    # Este valor lo puede ajustar el asesor en el CRM antes de enviar la oferta
    # (por dentro sale de un descuento sobre el CU de su comercializador).
    precio_ce = e.cu * (1 - e.descuento) - e.cv

    total_kwh = precio_ce + e.cv          # además del precio, sigue pagando el Cv a su comercializador
    contribucion = TASA_CONTRIBUCION if e.paga_contribucion else 0.0
    paga_hoy_kwh = e.cu * (1 + contribucion)

    # ---------- Ahorro ----------
    ahorro_kwh = paga_hoy_kwh - total_kwh
    ahorro_pct_kwh = ahorro_kwh / paga_hoy_kwh
    ahorro_mes = energia * ahorro_kwh
    ahorro_anio = ahorro_mes * 12
    costos_anio1 = 12 * (e.cuota_admin or 0) + (e.aporte_ingreso or 0)
    ahorro_neto_anio1 = ahorro_anio - costos_anio1

    pde = energia / e.generacion_planta if e.generacion_planta else None

    if ahorro_kwh <= 0:
        bloqueos.append("Con ese precio el usuario no ahorra: paga lo mismo o más que hoy.")
        return bloqueos, alertas, None

    # ---------- Restricciones que piden revisión ----------
    if promedio < CONSUMO_MINIMO_KWH:
        alertas.append(f"Consumo promedio de {num(promedio)} kWh/mes, menor a {num(CONSUMO_MINIMO_KWH)} (RN-011): por debajo no se cotiza.")
    if mes_bajo < UMBRAL_MES_ATIPICO * promedio:
        alertas.append("Mes atípico: el mes más bajo es menos del 60 % del promedio. Revisar si fue puntual o es temporada.")
    if e.estrato in (1, 2, 3):
        alertas.append("Estratos 1, 2 y 3 tienen subsidio: hoy pagan menos que el CU y el ahorro calculado queda inflado.")
    if precio_ce < PISO_PRECIO:
        alertas.append(f"El precio de la comunidad ({pesos(precio_ce, 2)}) queda bajo el piso del vehículo ({pesos(PISO_PRECIO, 2)}).")
    if ahorro_pct_kwh < AHORRO_MINIMO:
        alertas.append(f"El usuario ahorra solo {porc(ahorro_pct_kwh)} por kWh; el mínimo aceptable es {porc(AHORRO_MINIMO, 0)}.")
    if pde is not None and pde >= PDE_MAXIMO:
        alertas.append(f"El PDE daría {porc(pde, 2)}: tiene que quedar por debajo de 10 % (se usa 9,9 %).")
    if ahorro_neto_anio1 <= 0:
        alertas.append("Con la cuota y el aporte de ingreso, el ahorro neto del primer año queda en cero o negativo.")

    return bloqueos, alertas, Resultados(
        promedio=promedio,
        mes_bajo=mes_bajo,
        mes_bajo_etiqueta=mes_bajo_etiqueta,
        energia_garantizada=energia,
        cobertura_promedio=cobertura_promedio,
        contribucion=contribucion,
        precio_ce=precio_ce,
        total_kwh=total_kwh,
        paga_hoy_kwh=paga_hoy_kwh,
        ahorro_kwh=ahorro_kwh,
        ahorro_pct_kwh=ahorro_pct_kwh,
        ahorro_mes=ahorro_mes,
        ahorro_anio=ahorro_anio,
        costos_anio1=costos_anio1,
        ahorro_neto_anio1=ahorro_neto_anio1,
        pde=pde,
    )
