"""formato.py — Números y fechas como se escriben en Colombia (1.234.567,89)."""

from __future__ import annotations

import datetime as dt

MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_LARGOS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
                "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def num(valor: float, decimales: int = 0) -> str:
    """1234567.891 -> '1.234.567,89'"""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


def pesos(valor: float, decimales: int = 0) -> str:
    return "$" + num(valor, decimales)


def porc(valor: float, decimales: int = 1) -> str:
    return num(valor * 100, decimales) + " %"


def fecha(d: dt.date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def fecha_corta(d: dt.date | None) -> str:
    return d.strftime("%d/%m") if d else ""


def etiquetas_meses(mes_reciente: int, anio_reciente: int) -> list[str]:
    """Los 12 meses que terminan en (mes_reciente, anio_reciente), del más antiguo al más reciente.
    mes_reciente va de 1 a 12."""
    etiquetas = []
    for atras in range(11, -1, -1):
        m = mes_reciente - 1 - atras
        a = anio_reciente + m // 12
        etiquetas.append(f"{MESES_CORTOS[m % 12]} {a}")
    return etiquetas
