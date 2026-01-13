import streamlit as st
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

from analisis_proyecto import (
    normalizar_columnas,
    asegurar_columnas,
    calcular_totales_periodo,
    calcular_variaciones_periodo,
    responder_pregunta,
    generar_reporte_correo
)

st.set_page_config(page_title="Chatbot Financiero", layout="wide")
st.title("📊 Chatbot de Análisis Financiero")

# ======================================================
# CARGA DATOS
# ======================================================
st.subheader("📥 Cargar base histórica")

base = st.file_uploader("Sube el MASTERDATA", type=["xlsx"])
if not base:
    st.stop()

df_base = asegurar_columnas(normalizar_columnas(pd.read_excel(base)))

st.subheader("➕ Cargar mes nuevo (opcional)")
nuevo = st.file_uploader("Sube mes nuevo", type=["xlsx"])

if nuevo:
    df_mes = asegurar_columnas(normalizar_columnas(pd.read_excel(nuevo)))
    df = pd.concat([df_base, df_mes], ignore_index=True)
    df = df.drop_duplicates(subset=["PERIODO", "IDH"], keep="last")
else:
    df = df_base.copy()

# ======================================================
# ANÁLISIS
# ======================================================
totales = calcular_totales_periodo(df)
variaciones = calcular_variaciones_periodo(totales)

periodo = st.selectbox("Selecciona periodo", totales.index.tolist(), index=len(totales)-1)

# ======================================================
# KPIs
# ======================================================
st.subheader("📌 KPIs")

c1, c2, c3 = st.columns(3)
c1.metric("L14", f"{totales.loc[periodo,'L14']:,.0f}", f"{variaciones.loc[periodo,'L14']:.2f}%")
c2.metric("Volumen", f"{totales.loc[periodo,'VOL']:,.0f}", f"{variaciones.loc[periodo,'VOL']:.2f}%")
c3.metric("Costo Unitario", f"{totales.loc[periodo,'COSTO_UNITARIO']:,.2f}", f"{variaciones.loc[periodo,'COSTO_UNITARIO']:.2f}%")

# ======================================================
# GRÁFICAS
# ======================================================
st.subheader("📈 Evolución")

for col, title in [("L14","L14"),("VOL","Volumen"),("COSTO_UNITARIO","Costo Unitario")]:
    fig, ax = plt.subplots()
    totales[col].plot(marker="o", ax=ax)
    ax.set_title(title)
    ax.grid(True)
    st.pyplot(fig)

# ======================================================
# CHAT
# ======================================================
st.subheader("💬 Chatbot")

pregunta = st.text_input("Escribe tu pregunta")

if pregunta:
    df_p = df[df["PERIODO"] == periodo]
    t_p = totales.loc[[periodo]]
    v_p = variaciones.loc[[periodo]]
    respuesta = responder_pregunta(df_p, t_p, v_p, pregunta, periodo)
    st.text_area("Respuesta", respuesta, height=200)

# ======================================================
# CORREO
# ======================================================
st.subheader("📧 Correo automático")

correo = generar_reporte_correo(variaciones, totales, periodo)
st.text_area("Correo generado", correo, height=300)

correo_encoded = correo.replace("\n", "%0D%0A")
st.markdown(
    f"""
    <a href="mailto:?subject=Resultados {periodo}&body={correo_encoded}">
    <button style="background:#0078D4;color:white;padding:10px;border:none;">
    Abrir Outlook
    </button>
    </a>
    """,
    unsafe_allow_html=True
)





