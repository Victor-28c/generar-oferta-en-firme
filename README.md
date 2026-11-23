# Generador de la oferta en firme

App de Streamlit que pide a mano todos los datos de la oferta en firme, muestra los
cálculos y las alertas, y con un botón genera el PDF (4 páginas, mismo diseño del
borrador). Lo que se deje vacío sale en el PDF como **[corchete] verde**.

## Archivos

| Archivo | Qué hace |
|---|---|
| `app.py` | La pantalla: pestañas para llenar los datos, cálculos, botón para generar el PDF |
| `calculos.py` | Las cuentas y las revisiones (no dibuja nada) |
| `pdf_oferta.py` | Dibuja el PDF con ReportLab (no hace cuentas) |
| `formato.py` | Números y fechas en formato colombiano |
| `requirements.txt` | Librerías: `streamlit` y `reportlab` |
| `.streamlit/config.toml` | Colores verdes de la app |

## Correrla en el computador

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en el navegador. En la barra de la izquierda está **Cargar datos de ejemplo**
para probarla sin escribir nada.

## Publicarla en Streamlit Cloud

1. Sube esta carpeta a un repositorio de GitHub.
2. Entra a https://share.streamlit.io con tu cuenta de GitHub.
3. **Create app** → escoge el repositorio, la rama y `app.py` como archivo principal → **Deploy**.

Si la app queda pública, cualquiera con el enlace puede usarla. En la configuración de
la app en Streamlit Cloud se puede limitar a personas invitadas.

## Los cálculos

1. Mes más bajo = el menor de los 12 meses.
2. Energía garantizada = mes más bajo × 80 %.
3. Precio de la comunidad = CU × (1 − descuento) − Cv.
4. Total que paga por kWh de la comunidad = precio + Cv.
5. Lo que paga hoy por kWh = CU × (1 + contribución), con contribución 20 % o 0.
6. Ahorro por kWh = lo que paga hoy − total por kWh de la comunidad.
7. Ahorro al mes = energía garantizada × ahorro por kWh; al año × 12.
8. Ahorro neto del primer año = ahorro al año − 12 × cuota de administración − aporte de ingreso.

## Revisiones

**No deja calcular** si faltan meses, el CU o el Cv, si el Cv no es menor que el CU, o si
con ese precio el usuario no ahorra.

**Avisa** (se puede generar igual) si: el consumo promedio es menor a 4.500 kWh/mes;
el mes más bajo es menos del 60 % del promedio; es residencial de estrato 1, 2 o 3
(subsidio); el precio queda bajo el piso del vehículo ($641,61/kWh); el ahorro por kWh
es menor al 10 %; el PDE da 9,9 % o más (si se escribe la generación de la planta);
o el ahorro neto del primer año queda en cero o negativo.

## Pendiente para cuando se conecte

- **Contribución:** hoy se escoge a mano; se llenará al escanear la factura.
- **Precio por kWh:** hoy sale del descuento; el asesor lo podrá ajustar en el CRM antes de enviar.
- **Consumo de 12 meses:** hoy se escribe a mano; saldrá de la factura y del portal del operador.
