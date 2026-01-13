import streamlit as st
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt

# -----------------------------
# IMPORTAR CORE
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "core"))

from analisis_proyecto import (
    normalizar_columnas,
    asegurar_columnas,
    calcular_totales_periodo,
    calcular_variaciones_periodo,
    generar_reporte_correo,
    responder_pregunta
)

# -----------------------------
# CONFIG STREAMLIT
# -----------------------------
st.set_page_config(
    page_title="Chatbot de Análisis Financiero",
    layout="wide"
)

st.title("📊 Chatbot de Análisis Financiero")
st.caption("Carga mensual + análisis automático")

# -----------------------------
# CARGA BASE HISTÓRICA
# -----------------------------
st.subheader("📥 1. Cargar base histórica (MASTERDATA)")

base_file = st.file_uploader(
    "Sube el archivo MASTERDATA",
    type=["xlsx"],
    key="base"
)

if not base_file:
    st.info("Sube el MASTERDATA para comenzar")
    st.stop()

df_base = pd.read_excel(base_file)
df_base = normalizar_columnas(df_base)
df_base = asegurar_columnas(df_base)

# -----------------------------
# CARGA MES NUEVO (OPCIONAL)
# -----------------------------
st.subheader("➕ 2. Cargar mes nuevo (opcional)")

month_file = st.file_uploader(
    "Sube el archivo del mes nuevo",
    type=["xlsx"],
    key="mes"
)

if month_file:
    df_mes = pd.read_excel(month_file)
    df_mes = normalizar_columnas(df_mes)
    df_mes = asegurar_columnas(df_mes)

    df = pd.concat([df_base, df_mes], ignore_index=True)
    df = df.drop_duplicates(subset=["PERIODO", "IDH"], keep="last")

    st.success("Mes nuevo integrado correctamente")
else:
    df = df_base.copy()

# -----------------------------
# ANÁLISIS GLOBAL
# -----------------------------
totales = calcular_totales_periodo(df)
variaciones = calcular_variaciones_periodo(totales)

# -----------------------------
# SELECTOR PERIODO
# -----------------------------
st.subheader("📅 3. Selección de periodo")

periodos_disponibles = totales.index.tolist()

periodo = st.selectbox(
    "Selecciona el periodo para el análisis",
    periodos_disponibles,
    index=len(periodos_disponibles) - 1
)

# Data filtrada al periodo
df_periodo = df[df["PERIODO"] == periodo]

# -----------------------------
# KPIs
# -----------------------------
st.subheader("📌 KPIs del periodo")

col1, col2, col3 = st.columns(3)

col1.metric(
    "L14",
    f"{totales.loc[periodo, 'L14']:,.0f}",
    f"{variaciones.loc[periodo, 'L14']:.2f} %"
)

col2.metric(
    "Volumen",
    f"{totales.loc[periodo, 'VOL']:,.0f}",
    f"{variaciones.loc[periodo, 'VOL']:.2f} %"
)

col3.metric(
    "Costo Unitario",
    f"{totales.loc[periodo, 'COSTO_UNITARIO']:,.2f}",
    f"{variaciones.loc[periodo, 'COSTO_UNITARIO']:.2f} %"
)

# -----------------------------
# GRÁFICAS
# -----------------------------
st.subheader("📈 Evolución temporal")

# L14
fig1, ax1 = plt.subplots()
totales["L14"].plot(marker="o", ax=ax1)
ax1.set_title("L14 por periodo")
ax1.grid(True)
st.pyplot(fig1)

# VOL
fig2, ax2 = plt.subplots()
totales["VOL"].plot(marker="o", ax=ax2)
ax2.set_title("Volumen por periodo")
ax2.grid(True)
st.pyplot(fig2)

# COSTO UNITARIO
fig3, ax3 = plt.subplots()
totales["COSTO_UNITARIO"].plot(marker="o", ax=ax3)
ax3.set_title("Costo unitario por periodo")
ax3.grid(True)
st.pyplot(fig3)

# -----------------------------
# INSIGHTS
# -----------------------------
st.subheader("🧠 Insights automáticos")

var_cu = variaciones.loc[periodo, "COSTO_UNITARIO"]

if var_cu > 0:
    st.warning(
        f"🔺 El costo unitario aumentó {var_cu:.2f}% vs mes anterior. "
        "Revisar mix, volúmenes y variaciones."
    )
else:
    st.success(
        f"🔻 El costo unitario disminuyó {abs(var_cu):.2f}%. "
        "Buen control de costos."
    )

# -----------------------------
# CHATBOT
# -----------------------------
st.subheader("💬 Pregunta al chatbot")

pregunta = st.text_input(
    "Ejemplos: 'Top IDH', 'Variación L14', 'Costo unitario del mes'"
)

if pregunta:
    try:
        respuesta = responder_pregunta(
            df=df_periodo,
            totales=totales.loc[[periodo]],
            variaciones=variaciones.loc[[periodo]],
            pregunta=pregunta,
            periodo=periodo
        )

        st.text_area("Respuesta", respuesta, height=200)

    except Exception as e:
        st.error("Ocurrió un error procesando la pregunta")
        st.exception(e)

# -----------------------------
# CORREO
# -----------------------------
st.subheader("📧 Correo automático")

correo = generar_reporte_correo(
    variaciones=variaciones,
    totales=totales,
    periodo=periodo
)

st.text_area("Correo generado", correo, height=300)

# -----------------------------
# BOTÓN OUTLOOK
# -----------------------------
st.markdown("### 📤 Enviar por Outlook")

correo_encoded = correo.replace("\n", "%0D%0A")

outlook_link = f"""
<a href="mailto:?subject=Resultados financieros {periodo}&body={correo_encoded}">
<button style="
background-color:#0078D4;
color:white;
padding:10px 20px;
border:none;
border-radius:5px;
font-size:16px;">
Abrir Outlook
</button>
</a>
"""

st.markdown(outlook_link, unsafe_allow_html=True)


