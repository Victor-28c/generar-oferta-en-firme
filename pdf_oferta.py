"""
pdf_oferta.py — Dibuja la oferta en firme en PDF (A4, 4 páginas) con ReportLab.

No hace cuentas: recibe los datos que escribió el asesor (`d`) y los resultados
de calculos.py (`r`). Todo dato vacío sale como [corchete] en verde, para que
se note qué falta.
"""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (Flowable, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from calculos import COBERTURA, Resultados
from formato import num, pesos

# =========================================================
# COLORES Y ESTILOS
# =========================================================

G950 = colors.HexColor("#052C16")
G900 = colors.HexColor("#0B3D20")
G800 = colors.HexColor("#145A30")
G700 = colors.HexColor("#2E7D32")
G500 = colors.HexColor("#4CAE4F")
G300 = colors.HexColor("#86D489")
G100 = colors.HexColor("#E6EFE3")
MINT = colors.HexColor("#C2F8C4")
SLATE = colors.HexColor("#606D84")
INK = colors.HexColor("#1D2B22")
LINE = colors.HexColor("#DDE4DF")
SOFT = colors.HexColor("#FAFCF9")
WHITE = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 15 * mm
W = PAGE_W - 2 * MARGIN

F, FB = "Helvetica", "Helvetica-Bold"


def estilo(nombre, **kw):
    base = dict(fontName=F, fontSize=9, leading=12.5, textColor=INK)
    base.update(kw)
    return ParagraphStyle(nombre, **base)


S_BODY = estilo("body")
S_INTRO = estilo("intro", fontSize=9.6, leading=13.5)
S_NOTE = estilo("note", fontSize=7.4, leading=10, textColor=SLATE)
S_LABEL = estilo("label", fontName=FB, fontSize=6.3, leading=8, textColor=SLATE)
S_VALUE = estilo("value", fontSize=9, leading=12)
S_SMALL = estilo("small", fontSize=7.8, leading=10.5, textColor=SLATE)
S_SMALL_W = estilo("smallw", fontSize=8.2, leading=11, textColor=G100)
S_CARD_T = estilo("cardt", fontName=FB, fontSize=8.8, leading=11.5, textColor=G950)
S_KPI_V = estilo("kpiv", fontName=FB, fontSize=13, leading=16, textColor=G950)
S_BIG = estilo("big", fontName=FB, fontSize=13.5, leading=17, textColor=G950)
S_CELL_K = estilo("cellk", fontSize=8.6, leading=11, textColor=SLATE)
S_CELL_V = estilo("cellv", fontSize=8.8, leading=11.5)
S_CELL_KB = estilo("cellkb", fontName=FB, fontSize=8.8, leading=11.5, textColor=G950)
S_TH = estilo("th", fontName=FB, fontSize=6.6, leading=8, textColor=G100)
S_STAT = estilo("stat", fontName=FB, fontSize=8.4, leading=11, textColor=G950)
S_STAT_W = estilo("statw", fontName=FB, fontSize=8.4, leading=11, textColor=WHITE)
S_H3 = estilo("h3", fontName=FB, fontSize=10.5, leading=13, textColor=G950)
S_CTA_T = estilo("ctat", fontName=FB, fontSize=13, leading=16, textColor=WHITE)
S_CTA_L = estilo("ctal", fontName=FB, fontSize=6.4, leading=8, textColor=G300)
S_CTA_V = estilo("ctav", fontName=FB, fontSize=9.5, leading=12, textColor=WHITE)
S_ARROW = estilo("arrow", fontName=FB, fontSize=16, leading=18, textColor=G500, alignment=TA_CENTER)


# =========================================================
# TEXTO: valor o [corchete]
# =========================================================

def ph(texto: str, oscuro: bool = False) -> str:
    """Marca de dato pendiente."""
    if oscuro:
        return f'<font color="#C2F8C4">[{escape(texto)}]</font>'
    return f'<font color="#2E7D32" backColor="#E6EFE3">[{escape(texto)}]</font>'


def v(valor, pendiente: str, oscuro: bool = False) -> str:
    """El valor escrito por el asesor o, si está vacío, el [corchete]."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return ph(pendiente, oscuro)
    return escape(str(valor))


def vn(valor, pendiente: str, formato=num, dec: int = 0, oscuro: bool = False) -> str:
    """Número con formato colombiano o [corchete]."""
    if valor is None:
        return ph(pendiente, oscuro)
    return escape(formato(valor, dec))


def P(texto: str, s: ParagraphStyle = S_BODY) -> Paragraph:
    return Paragraph(texto, s)


# =========================================================
# PIEZAS DIBUJADAS
# =========================================================

class Portada(Flowable):
    """Bloque verde de arriba: tipo de oferta, título, comunidad, número, fechas."""

    def __init__(self, comunidad, numero, emision, valida_hasta, dias):
        super().__init__()
        self.comunidad, self.numero = comunidad, numero
        self.emision, self.valida_hasta, self.dias = emision, valida_hasta, dias
        self.width, self.height = W, 54 * mm

    def wrap(self, *_):
        return self.width, self.height

    def _txt(self, c, x, y, valor, pendiente, font=F, size=9, color=WHITE):
        if valor or pendiente is None:
            c.setFillColor(color)
            texto = str(valor)
        else:
            c.setFillColor(MINT)
            texto = f"[{pendiente}]"
        c.setFont(font, size)
        c.drawString(x, y, texto)
        return c.stringWidth(texto, font, size)

    def draw(self):
        c, w, h = self.canv, self.width, self.height
        c.saveState()
        path = c.beginPath()
        path.roundRect(0, 0, w, h, 12)
        c.clipPath(path, stroke=0, fill=0)
        c.linearGradient(0, h, w, 0, (G950, G900, G800), positions=(0, 0.6, 1))
        # sol
        cx, cy = w - 18 * mm, h - 14 * mm
        c.setStrokeColor(MINT)
        for radio, alfa in ((30 * mm, 0.12), (22 * mm, 0.25)):
            c.setStrokeAlpha(alfa)
            c.setLineWidth(1.4)
            c.circle(cx, cy, radio, stroke=1, fill=0)
        c.setStrokeAlpha(0.55)
        c.setLineWidth(3)
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (0.7, 0.7), (-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7)):
            c.line(cx + dx * 15 * mm, cy + dy * 15 * mm, cx + dx * 19 * mm, cy + dy * 19 * mm)
        c.setFillColor(MINT)
        c.setFillAlpha(0.85)
        c.circle(cx, cy, 10 * mm, stroke=0, fill=1)
        c.setFillAlpha(1)
        c.setStrokeAlpha(1)
        c.restoreState()

        x0 = 8 * mm
        # píldora "OFERTA EN FIRME"
        c.setStrokeColor(MINT)
        c.setLineWidth(0.7)
        c.roundRect(x0, h - 13 * mm, 38 * mm, 6.2 * mm, 3.1 * mm, stroke=1, fill=0)
        c.setFillColor(MINT)
        c.circle(x0 + 3.6 * mm, h - 9.9 * mm, 0.9 * mm, stroke=0, fill=1)
        c.setFont(FB, 6.8)
        c.drawString(x0 + 6 * mm, h - 11.1 * mm, "OFERTA EN FIRME", charSpace=1.1)
        # título
        c.setFillColor(WHITE)
        c.setFont(FB, 19)
        c.drawString(x0, h - 21.5 * mm, "Oferta de vinculación a la")
        c.drawString(x0, h - 28.5 * mm, "Comunidad Energética")
        self._txt(c, x0, h - 34.5 * mm, self.comunidad, "Nombre de la comunidad", F, 10, G100)
        # cajitas de datos
        cajas = [
            ("OFERTA N.º", [(self.numero, "0000")], 26 * mm),
            ("FECHA DE EMISIÓN", [(self.emision, "DD/MM/AAAA")], 34 * mm),
            ("VÁLIDA HASTA", [(self.valida_hasta, "DD/MM/AAAA"), (" · ", None), (f"{self.dias} días" if self.dias else "", "30 días")], 52 * mm),
        ]
        x = x0
        for etiqueta, partes, ancho in cajas:
            c.setFillColor(WHITE)
            c.setFillAlpha(0.08)
            c.setStrokeColor(WHITE)
            c.setStrokeAlpha(0.18)
            c.roundRect(x, 4.5 * mm, ancho, 10.5 * mm, 2.5 * mm, stroke=1, fill=1)
            c.setFillAlpha(1)
            c.setStrokeAlpha(1)
            c.setFillColor(G300)
            c.setFont(FB, 5.8)
            c.drawString(x + 3 * mm, 11.3 * mm, etiqueta, charSpace=0.8)
            xx = x + 3 * mm
            for valor, pendiente in partes:
                xx += self._txt(c, xx, 6.8 * mm, valor, pendiente, FB, 9)
            x += ancho + 3 * mm


class Tarjetas(Flowable):
    """Fila de tarjetas redondeadas. Cada tarjeta es una lista de Paragraph.

    numeros: dibuja un círculo con el número de paso.
    flechas: pone » entre tarjetas.
    acento: rayita verde arriba de cada tarjeta.
    """

    def __init__(self, tarjetas, rellenos=None, numeros=False, flechas=False, acento=False,
                 borde=True, pad=3.2 * mm, gap=2.5 * mm):
        super().__init__()
        self.tarjetas = tarjetas
        self.rellenos = rellenos or [WHITE] * len(tarjetas)
        self.numeros, self.flechas, self.acento, self.borde = numeros, flechas, acento, borde
        self.pad, self.gap = pad, gap
        self.flecha_w = 6 * mm if flechas else 0

    def _ancho_tarjeta(self, avail):
        n = len(self.tarjetas)
        sep = self.flecha_w if self.flechas else self.gap
        return (avail - sep * (n - 1)) / n

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        aw = self._ancho_tarjeta(avail_w) - 2 * self.pad
        extra = 6.5 * mm if self.numeros else (1.5 * mm if self.acento else 0)
        alto = 0
        self._altos = []
        for contenido in self.tarjetas:
            hs = [p.wrap(aw, avail_h)[1] for p in contenido]
            altura = sum(hs) + 1.2 * mm * (len(hs) - 1)
            self._altos.append(hs)
            alto = max(alto, altura)
        self.height = alto + 2 * self.pad + extra
        return self.width, self.height

    def draw(self):
        c = self.canv
        tw = self._ancho_tarjeta(self.width)
        sep = self.flecha_w if self.flechas else self.gap
        for i, contenido in enumerate(self.tarjetas):
            x = i * (tw + sep)
            c.setFillColor(self.rellenos[i])
            c.setStrokeColor(LINE)
            c.setLineWidth(0.7)
            c.roundRect(x, 0, tw, self.height, 3 * mm, stroke=1 if self.borde else 0, fill=1)
            y = self.height - self.pad
            if self.acento:
                c.setFillColor(G500)
                c.roundRect(x + self.pad, self.height - 1.1 * mm, 9 * mm, 1.1 * mm, 0.5 * mm, stroke=0, fill=1)
                y -= 1.5 * mm
            if self.numeros:
                c.setFillColor(G500)
                c.circle(x + self.pad + 2.6 * mm, y - 2.6 * mm, 2.6 * mm, stroke=0, fill=1)
                c.setFillColor(WHITE)
                c.setFont(FB, 8)
                c.drawCentredString(x + self.pad + 2.6 * mm, y - 3.6 * mm, str(i + 1))
                y -= 6.5 * mm
            for p, hp in zip(contenido, self._altos[i]):
                y -= hp
                p.drawOn(c, x + self.pad, y)
                y -= 1.2 * mm
            if self.flechas and i < len(self.tarjetas) - 1:
                c.setFillColor(G500)
                c.setFont(FB, 15)
                c.drawCentredString(x + tw + sep / 2, self.height / 2 - 2 * mm, "»")


class Encabezado(Flowable):
    """Círculo con el número de sección, título y línea debajo."""

    def __init__(self, numero, titulo):
        super().__init__()
        self.numero, self.titulo = numero, titulo

    def wrap(self, aw, ah):
        self.width, self.height = aw, 9.5 * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(G950)
        c.circle(3 * mm, 5.6 * mm, 3 * mm, stroke=0, fill=1)
        c.setFillColor(MINT)
        c.setFont(FB, 8.5)
        c.drawCentredString(3 * mm, 4.6 * mm, str(self.numero))
        c.setFillColor(G950)
        c.setFont(FB, 12.5)
        c.drawString(8.5 * mm, 4.3 * mm, self.titulo)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.line(0, 0.6 * mm, self.width, 0.6 * mm)


class Formula(Flowable):
    """[mes más bajo] × 80 % = [energía garantizada], en cajitas."""

    def __init__(self, mes_bajo_txt, energia_txt, pendiente_mes, pendiente_energia):
        super().__init__()
        self.mes_bajo_txt, self.energia_txt = mes_bajo_txt, energia_txt
        self.pm, self.pe = pendiente_mes, pendiente_energia

    def wrap(self, aw, ah):
        self.width, self.height = aw, 12 * mm
        return self.width, self.height

    def _caja(self, c, x, ancho, etiqueta, valor, pendiente, oscura=False):
        c.setFillColor(G950 if oscura else WHITE)
        c.setStrokeColor(G950 if oscura else LINE)
        c.setLineWidth(0.7)
        c.roundRect(x, 0, ancho, self.height, 2.5 * mm, stroke=1, fill=1)
        c.setFillColor(G300 if oscura else SLATE)
        c.setFont(FB, 5.8)
        c.drawCentredString(x + ancho / 2, self.height - 4 * mm, etiqueta)
        if valor:
            c.setFillColor(WHITE if oscura else G950)
            texto = valor
        else:
            c.setFillColor(MINT if oscura else G700)
            texto = f"[{pendiente}]"
        c.setFont(FB, 9.5)
        c.drawCentredString(x + ancho / 2, 3 * mm, texto)

    def draw(self):
        c = self.canv
        x = 0
        self._caja(c, x, 40 * mm, "TU MES MÁS BAJO", self.mes_bajo_txt, self.pm)
        x += 40 * mm
        c.setFillColor(G700)
        c.setFont(FB, 13)
        c.drawCentredString(x + 4 * mm, 4 * mm, "×")
        x += 8 * mm
        self._caja(c, x, 26 * mm, "COBERTURA", f"{int(COBERTURA * 100)} %", "")
        x += 26 * mm
        c.setFillColor(G700)
        c.setFont(FB, 13)
        c.drawCentredString(x + 4 * mm, 4 * mm, "=")
        x += 8 * mm
        self._caja(c, x, 50 * mm, "ENERGÍA GARANTIZADA", self.energia_txt, self.pe, oscura=True)


def vinetas(items, estilo_p=S_BODY):
    return ListFlowable(
        [ListItem(P(t, estilo_p), leftIndent=11) for t in items],
        bulletType="bullet", start="•", bulletColor=G500, bulletFontName=FB, bulletFontSize=11,
        leftIndent=11, bulletOffsetY=1, spaceBefore=0,
    )


def caja(contenido, fondo=SOFT, borde=LINE, pad=8):
    t = Table([[contenido]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fondo),
        ("BOX", (0, 0), (-1, -1), 0.8, borde),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ("LEFTPADDING", (0, 0), (-1, -1), pad + 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad + 2),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]))
    return t


def campos(pares):
    """Cuadrícula de 2 columnas: etiqueta arriba, valor abajo."""
    celdas = [[P(etq.upper(), S_LABEL), P(val, S_VALUE)] for etq, val in pares]
    if len(celdas) % 2:
        celdas.append("")
    filas = [celdas[i:i + 2] for i in range(0, len(celdas), 2)]
    t = Table(filas, colWidths=[W / 2, W / 2])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, LINE),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# =========================================================
# PIE DE PÁGINA: "Página X de Y"
# =========================================================

def lienzo_con_pie(texto_pie):
    class Lienzo(rl_canvas.Canvas):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._paginas = []

        def showPage(self):
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas)
            for estado in self._paginas:
                self.__dict__.update(estado)
                self.setFont(F, 7)
                self.setFillColor(SLATE)
                self.drawString(MARGIN, 9 * mm, texto_pie)
                self.drawRightString(PAGE_W - MARGIN, 9 * mm, f"Página {self._pageNumber} de {total}")
                super().showPage()
            super().save()
    return Lienzo


# =========================================================
# LA OFERTA
# =========================================================

def generar_pdf(d: dict, r: Resultados | None) -> bytes:
    """d: datos escritos en la app (textos, fechas ya formateadas, consumos).
    r: resultados de calculos.calcular (None si aún faltan datos)."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=14 * mm, bottomMargin=16 * mm,
                            title="Oferta en firme", author=d.get("comunidad") or "Comunidad energética")
    s = []

    cliente = v(d.get("cliente"), "Nombre del cliente")
    comunidad = v(d.get("comunidad"), "Nombre de la comunidad")
    responde = d.get("valida_hasta_corta")

    # ---------------- PÁGINA 1 ----------------
    s.append(Portada(d.get("comunidad"), d.get("numero"), d.get("emision"), d.get("valida_hasta"), d.get("dias")))
    s.append(Spacer(1, 5 * mm))
    punto = "" if (d.get("cliente") or "").strip().endswith(".") else "."
    s.append(P(f"Hola, {cliente}{punto} Con tu consumo de los últimos 12 meses preparamos esta oferta para que tu cuenta "
               f"reciba energía solar de la comunidad {comunidad} y pagues menos por tu energía. Aquí está todo lo "
               f"que necesitas para decidir.", S_INTRO))
    s.append(Spacer(1, 4 * mm))

    def kpi(etiqueta, valor, sub):
        return [P(etiqueta, S_LABEL), P(valor, S_KPI_V), P(sub, S_SMALL)]

    s.append(Tarjetas([
        kpi("ENERGÍA GARANTIZADA", vn(r and r.energia_garantizada, "___"), "kWh al mes, todos los meses"),
        kpi("PRECIO POR kWh", vn(r and r.precio_ce, "$___", pesos, 2), "valor inicial de la comunidad"),
        kpi("AHORRO ESTIMADO", vn(r and r.ahorro_neto_anio1, "$___", pesos), "neto, el primer año"),
        kpi("RESPONDE ANTES DEL", v(responde, "DD/MM"), "por WhatsApp o correo"),
    ], rellenos=[G100, WHITE, WHITE, WHITE], acento=True))
    s.append(Spacer(1, 1.5 * mm))
    s.append(P("La energía garantizada se explica en la sección 4. El ahorro es una estimación (sección 5).", S_NOTE))
    s.append(Spacer(1, 4 * mm))

    tipo_usuario = d.get("tipo_usuario") or ""
    if tipo_usuario == "Residencial" and d.get("estrato"):
        tipo_usuario = f"Residencial estrato {d['estrato']}"
    contrib = d.get("paga_contribucion")
    contrib_txt = ("Sí, 20 % · según tu factura" if contrib else "No · según tu factura") if contrib is not None else None

    s.append(Encabezado(1, "Tus datos"))
    s.append(Spacer(1, 2.5 * mm))
    s.append(campos([
        ("Nombre o razón social", cliente),
        ("Documento", f'{v(d.get("tipo_doc"), "CC / NIT / CE")} {v(d.get("num_doc"), "Número")}'),
        ("NIU (cuenta en tu factura)", v(d.get("niu"), "NIU")),
        ("Frontera comercial (código SIC, si aplica)", v(d.get("sic"), "Código SIC")),
        ("Dirección del predio", v(d.get("direccion"), "Dirección, municipio, departamento")),
        ("Tipo de usuario", v(tipo_usuario, "Residencial / Comercial / Industrial / Oficial")),
        ("¿Pagas contribución de solidaridad?", v(contrib_txt, "Sí, 20 % / No")),
        ("Comercializador · Operador de red", f'{v(d.get("comercializador"), "Comercializador")} · {v(d.get("operador"), "Operador de red")}'),
        ("Tipo de medidor", v(d.get("medidor"), "Convencional / Bidireccional / Inteligente")),
        ("Contacto", f'{v(d.get("tel_cliente"), "Teléfono")} · {v(d.get("correo_cliente"), "Correo")}'),
    ]))
    s.append(Spacer(1, 4 * mm))

    s.append(Encabezado(2, "Quién te hace esta oferta"))
    s.append(Spacer(1, 2.5 * mm))
    planta = (f'{v(d.get("tipo_planta"), "Solar fotovoltaica")} · {vn(d.get("kwp"), "___", num, 0)} kWp · '
              f'{v(d.get("ubicacion_planta"), "Ubicación")}')
    s.append(campos([
        ("Comunidad energética", f"{comunidad} · Autogeneración colectiva"),
        ("Representante de la comunidad", v(d.get("representante"), "Nombre y documento")),
        ("Registro ante el Ministerio de Minas y Energía", v(d.get("registro_mme"), "Número de registro / en trámite")),
        ("Contacto del representante", f'{v(d.get("tel_rep"), "Teléfono")} · {v(d.get("correo_rep"), "Correo")}'),
        ("Planta", planta),
        ("Comercializador de la comunidad", v(d.get("comercializador_ce"), "Nombre del comercializador")),
        ("Entrada en operación estimada", v(d.get("entrada_operacion"), "DD/MM/AAAA")),
    ]))

    # ---------------- PÁGINA 2 ----------------
    s.append(PageBreak())
    s.append(Encabezado(3, "Tu consumo de los últimos 12 meses"))
    s.append(Spacer(1, 2 * mm))
    s.append(P(f'Fuente: {v(d.get("fuente_consumo"), "tu factura y el historial de tu operador de red")}.', S_SMALL))
    s.append(Spacer(1, 2 * mm))

    meses = d.get("meses") or [""] * 12
    consumos = d.get("consumos") or [None] * 12
    i_bajo = None
    if r is not None:
        i_bajo = consumos.index(r.mes_bajo)
    celdas = []
    for i in range(12):
        etiqueta = v(meses[i] if i < len(meses) else "", "Mes/Año")
        valor = vn(consumos[i] if i < len(consumos) else None, "kWh")
        if consumos[i] is not None:
            valor += " kWh"
        celdas.append([P(etiqueta, estilo(f"m{i}", fontSize=7, leading=9, textColor=SLATE, alignment=TA_CENTER)),
                       P(f"<b>{valor}</b>", estilo(f"mv{i}", fontSize=8.6, leading=11, alignment=TA_CENTER))])
    t = Table([celdas[:6], celdas[6:]], colWidths=[W / 6] * 6)
    estilo_meses = [
        ("BOX", (0, 0), (-1, -1), 0.7, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.7, LINE),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if i_bajo is not None:
        estilo_meses.append(("BACKGROUND", (i_bajo % 6, i_bajo // 6), (i_bajo % 6, i_bajo // 6), MINT))
    t.setStyle(TableStyle(estilo_meses))
    s.append(t)
    s.append(Spacer(1, 2.5 * mm))

    mes_bajo_txt = (f"{escape(r.mes_bajo_etiqueta)} · {num(r.mes_bajo)} kWh" if r
                    else f'{ph("Mes/Año", True)} · {ph("___", True)} kWh')
    promedio_txt = f"{num(r.promedio)} kWh/mes" if r else f'{ph("___")} kWh/mes'
    s.append(Tarjetas([
        [P(f"Mes de menor consumo:&nbsp;&nbsp;{mes_bajo_txt}", S_STAT_W)],
        [P(f"Consumo promedio:&nbsp;&nbsp;{promedio_txt}", S_STAT)],
    ], rellenos=[G950, G100], borde=False, pad=3 * mm))
    s.append(Spacer(1, 6 * mm))

    s.append(Encabezado(4, "Lo que te garantizamos"))
    s.append(Spacer(1, 2.5 * mm))
    energia_txt = vn(r and r.energia_garantizada, "___")
    compensacion = v(d.get("compensacion"), "mecanismo de compensación por definir")
    s.append(caja([
        P(f"Energía garantizada: {energia_txt} kWh al mes, todos los meses", S_BIG),
        Spacer(1, 3 * mm),
        Formula(f"{num(r.mes_bajo)} kWh" if r else "", f"{num(r.energia_garantizada)} kWh/mes" if r else "",
                "___ kWh", "___ kWh/mes"),
        Spacer(1, 3.5 * mm),
        vinetas([
            "Si algún mes consumes menos que eso, recibes lo que consumas ese mes.",
            "La garantía aplica siempre que la planta pueda entregar su energía a la red. No aplica ante fallas "
            "de la red del operador, fuerza mayor o cambios en la regulación.",
            f"Si algún mes no recibes la energía garantizada por causas a cargo de la comunidad: {compensacion}.",
        ]),
    ], fondo=colors.HexColor("#F3F9F1"), borde=G500, pad=10))
    s.append(Spacer(1, 5 * mm))

    s.append(P("Cómo te llega esta energía", S_H3))
    s.append(Spacer(1, 2.5 * mm))
    s.append(Tarjetas([
        [P("La planta genera", S_CARD_T),
         P("La planta solar de la comunidad entrega su energía a la red. A ti te corresponde tu parte cada mes.", S_SMALL)],
        [P("Tu factura baja", S_CARD_T),
         P("Tu comercializador descuenta esos kWh de tu consumo y solo te cobra por ellos el costo de "
           "comercialización (Cv).", S_SMALL)],
        [P("Pagas menos", S_CARD_T),
         P("Le pagas a la comunidad esos kWh a su precio, que es menor a lo que pagas hoy por kWh.", S_SMALL)],
    ], flechas=True))

    # ---------------- PÁGINA 3 ----------------
    s.append(PageBreak())
    s.append(Encabezado(5, "Lo que pagas y lo que ahorras"))
    s.append(Spacer(1, 2.5 * mm))

    def fila(k, val, total=False):
        return [P(k, S_CELL_KB if total else S_CELL_K), P(f"<b>{val}</b>" if total else val, S_CELL_V)]

    cuota = d.get("cuota_admin")
    aporte = d.get("aporte_ingreso")
    cuota_txt = "No aplica" if cuota == 0 else (f"{pesos(cuota)} /mes" if cuota else ph("$___ /mes · No aplica"))
    aporte_txt = "Sin costo" if aporte == 0 else (pesos(aporte) if aporte else ph("$___ · Sin costo"))
    filas = [
        [P("CONCEPTO", S_TH), P("VALOR", S_TH)],
        fila("Energía garantizada", f"{vn(r and r.energia_garantizada, '___')} kWh/mes"),
        fila("Precio del kWh de la comunidad (inicial)", f"{vn(r and r.precio_ce, '$___', pesos, 2)} /kWh"),
        fila("Costo de comercialización (Cv) que sigue cobrando tu comercializador", f"{vn(d.get('cv'), '$___', pesos, 2)} /kWh"),
        fila("Total que pagas por cada kWh de la comunidad", f"{vn(r and r.total_kwh, '$___', pesos, 2)} /kWh"),
        fila("Lo que pagas hoy por kWh (con contribución, si la pagas)", f"{vn(r and r.paga_hoy_kwh, '$___', pesos, 2)} /kWh"),
        fila("Ahorro por kWh", f"{vn(r and r.ahorro_kwh, '$___', pesos, 2)} /kWh"),
        fila("Ahorro estimado al mes", vn(r and r.ahorro_mes, "$___", pesos)),
        fila("Ahorro estimado al año", vn(r and r.ahorro_anio, "$___", pesos)),
        fila("Cuota de administración de la comunidad", cuota_txt),
        fila("Aporte de ingreso (una sola vez)", aporte_txt),
        fila("Ahorro neto estimado el primer año", vn(r and r.ahorro_neto_anio1, "$___", pesos), total=True),
        fila("Cómo se paga", v(d.get("forma_pago"), "Cobro mensual de la comunidad / en la factura del comercializador")),
    ]
    t = Table(filas, colWidths=[W * 0.56, W * 0.44])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), G950),
        ("BACKGROUND", (0, 1), (0, -1), SOFT),
        ("BACKGROUND", (0, 11), (-1, 11), G100),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.6, LINE),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    s.append(t)
    s.append(Spacer(1, 2.5 * mm))
    s.append(caja(P(
        "<b>Ahorro por kWh</b> = lo que pagas hoy por kWh – (precio de la comunidad + Cv). "
        "<b>Ahorro al mes</b> = energía garantizada × ahorro por kWh. "
        "<b>Ahorro neto del primer año</b> = ahorro al año – 12 × cuota de administración – aporte de ingreso.<br/>"
        "Pagas los kWh que la comunidad te asigna cada mes. El precio por kWh de la comunidad se puede reajustar "
        "en el mismo porcentaje en que cambie la tarifa de tu comercializador.", S_SMALL)))
    s.append(Spacer(1, 6 * mm))

    s.append(Encabezado(6, "Qué necesitas para entrar"))
    s.append(Spacer(1, 2.5 * mm))
    s.append(vinetas([
        f'Ser usuario del servicio de energía con NIU activo {v(d.get("req_al_dia"), "y estar al día con tu factura")}.',
        "Que tu predio esté en el mismo mercado de comercialización y conectado a la misma red de distribución "
        f'que la planta ({v(d.get("operador"), "operador de red")}).',
        f'Que tu cuenta quede con el comercializador de la comunidad ({v(d.get("comercializador_ce"), "nombre")}). '
        f'Si hoy tienes otro, {v(d.get("cambio_comercializador"), "te acompañamos en el cambio")}.',
        f'Contar con el medidor requerido: {v(d.get("medidor_requerido"), "tipo de medidor")}. '
        f'{v(d.get("costo_medidor"), "Quién asume el costo")}.',
        "Autorizar que la comunidad y el comercializador usen tu información de consumo para la liquidación.",
    ]))

    # ---------------- PÁGINA 4 ----------------
    s.append(PageBreak())
    s.append(Encabezado(7, "Condiciones de la oferta"))
    s.append(Spacer(1, 2.5 * mm))
    valida_hasta = v(d.get("valida_hasta"), "DD/MM/AAAA")
    s.append(vinetas([
        f"<b>Oferta en firme:</b> sus condiciones no cambian hasta el {valida_hasta}.",
        "<b>Aceptarla no requiere firma.</b> Con tu aceptación quedan acordadas estas condiciones; los documentos "
        "que firmes después las formalizan y no las cambian.",
        "<b>Ahorro:</b> las cifras de ahorro son estimadas y dependen de la tarifa de tu comercializador, que "
        "cambia mes a mes. Lo garantizado es la energía, no un valor de ahorro.",
        f'<b>Entrada en operación:</b> si la planta no empieza a entregarte energía antes del '
        f'{v(d.get("fecha_limite_inicio"), "DD/MM/AAAA")}, puedes desistir sin ningún costo.',
        f'<b>Permanencia y salida:</b> {v(d.get("permanencia"), "Sin permanencia mínima / permanencia de __ meses")}. '
        f'{v(d.get("retiro"), "Cómo puede retirarse el usuario")}.',
        "<b>Marco normativo:</b> la comunidad se rige por el Decreto 2236 de 2023, las Resoluciones CREG 174 de "
        "2021 y 101 072 de 2025, y las normas que las modifiquen. Conservas tus derechos como usuario de "
        "servicios públicos.",
        f'<b>Datos personales:</b> tratamos tu información conforme a la Ley 1581 de 2012. Política de '
        f'tratamiento: {v(d.get("enlace_datos"), "enlace")}.',
    ]))
    s.append(Spacer(1, 6 * mm))

    s.append(Encabezado(8, "Cómo aceptar y qué sigue"))
    s.append(Spacer(1, 2.5 * mm))
    s.append(Tarjetas([
        [P("Responde", S_CARD_T), P(f"Acepta o rechaza antes del {v(responde, 'DD/MM')} por WhatsApp o correo.", S_SMALL)],
        [P("Elige cómo vincularte", S_CARD_T), P("Mandato, o PPA + acuerdo de la comunidad. Te enviamos los documentos.", S_SMALL)],
        [P("Firma", S_CARD_T), P("Firmas los documentos del camino que elegiste.", S_SMALL)],
        [P("Registro", S_CARD_T), P("Registramos tu cuenta en la comunidad e informamos a tu comercializador.", S_SMALL)],
        [P("Empiezas", S_CARD_T), P(f'Recibes tu energía desde {v(d.get("fecha_inicio"), "DD/MM/AAAA")}.', S_SMALL)],
    ], numeros=True, gap=2 * mm, pad=2.8 * mm))
    s.append(Spacer(1, 6 * mm))

    # Recuadro final para aceptar o rechazar
    izquierda = [
        P("¿Aceptas o rechazas esta oferta?", S_CTA_T), Spacer(1, 2 * mm),
        P(f'Escríbenos antes del {v(d.get("valida_hasta"), "DD/MM/AAAA", True)} e indica tu nombre, tu documento y '
          f'si aceptas o rechazas la oferta N.º {v(d.get("numero"), "0000", True)}. Si no respondes, la oferta vence '
          f'sin ningún costo para ti.', S_SMALL_W),
    ]
    canal = TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1B4A2E")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#3E6B50")),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])
    wa = Table([[[P("WHATSAPP", S_CTA_L), P(v(d.get("whatsapp"), "número", True), S_CTA_V)]]], colWidths=[W * 0.36])
    wa.setStyle(canal)
    co = Table([[[P("CORREO", S_CTA_L), P(v(d.get("correo_ce"), "correo", True), S_CTA_V)]]], colWidths=[W * 0.36])
    co.setStyle(canal)
    cta = Table([[izquierda, [wa, Spacer(1, 2 * mm), co]]], colWidths=[W * 0.58, W * 0.42])
    cta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), G950),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    s.append(cta)
    s.append(Spacer(1, 4 * mm))

    firma = Table([[
        P(f'Tu asesor: <b>{v(d.get("asesor"), "Nombre del asesor")}</b> · {v(d.get("cargo_asesor"), "Cargo")}<br/>'
          f'{v(d.get("tel_asesor"), "Teléfono")} · {v(d.get("correo_asesor"), "Correo electrónico")}', S_SMALL),
        P(f"Comunidad Energética {comunidad}", estilo("der", fontSize=7.8, leading=10.5, textColor=SLATE, alignment=2)),
    ]], colWidths=[W * 0.6, W * 0.4])
    firma.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    s.append(firma)

    pie = f'Oferta N.º {d.get("numero") or "[0000]"} · Comunidad Energética {d.get("comunidad") or "[Nombre de la comunidad]"}'
    doc.build(s, canvasmaker=lienzo_con_pie(pie))
    return buf.getvalue()
