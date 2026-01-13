import streamlit as st
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt

# -----------------------------
# IMPORTAR CORE
# -----------------------------
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

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
# ANÁLISIS
# -----------------------------
totales = calcular_totales_periodo(df)
variaciones = calcular_variaciones_periodo(totales)

# -----------------------------
# SELECTOR PERIODO
# -----------------------------
st.subheader("📅 3. Selección de periodo")

periodo = st.selectbox(
    "Selecciona el periodo para el análisis",
    totales.index.tolist(),
    index=len(totales) - 1
)

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
# GRÁFICAS (SEPARADAS)
# -----------------------------
st.subheader("📈 Evolución temporal")

# --- L14 ---
fig1, ax1 = plt.subplots()
totales["L14"].plot(marker="o", ax=ax1)
ax1.set_title("L14 por periodo")
ax1.grid(True)
st.pyplot(fig1)

# --- VOL ---
fig2, ax2 = plt.subplots()
totales["VOL"].plot(marker="o", ax=ax2)
ax2.set_title("Volumen por periodo")
ax2.grid(True)
st.pyplot(fig2)

# --- COSTO UNITARIO ---
fig3, ax3 = plt.subplots()
totales["COSTO_UNITARIO"].plot(marker="o", ax=ax3)
ax3.set_title("Costo unitario por periodo")
ax3.grid(True)
st.pyplot(fig3)

# -----------------------------
# INSIGHTS AUTOMÁTICOS
# -----------------------------
st.subheader("🧠 Insights automáticos")

var_cu = variaciones.loc[periodo, "COSTO_UNITARIO"]

if var_cu > 0:
    st.warning("🔺 El costo unitario aumentó vs mes anterior. Revisar mix y variaciones.")
else:
    st.success("🔻 El costo unitario disminuyó. Buen control de costos.")

df_periodo = df[df["PERIODO"] == periodo]

# -----------------------------
# CHAT
# -----------------------------
st.subheader("💬 Pregunta al chatbot")

pregunta = st.text_input(
    "Ejemplos: 'Top idh', 'variacion l14', 'costo unitario ultimo'"
)

if pregunta:
    respuesta = responder_pregunta(
    df_periodo,
    totales.loc[[periodo]],
    variaciones.loc[[periodo]],
    pregunta,
    periodo=periodo
)
    st.text_area("Respuesta", respuesta, height=200)

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

# BOTÓN OUTLOOK
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

