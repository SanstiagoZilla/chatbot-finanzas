import streamlit as st
import pandas as pd
import os

from core.analisis_proyecto import (
    normalizar_columnas,
    asegurar_columnas,
    calcular_totales_periodo,
    calcular_variaciones_periodo,
    generar_reporte_correo,
    responder_pregunta
)

st.set_page_config(page_title="Chatbot Finanzas", layout="wide")

st.title("📊 Chatbot de Análisis Financiero")
st.caption("Carga mensual + análisis automático")

BASE_HISTORICA = "MASTERDATA_PROYECTO.xlsx"

# -----------------------------
# Cargar base histórica
# -----------------------------
if not os.path.exists(BASE_HISTORICA):
    st.error("No se encontró MASTERDATA_PROYECTO.xlsx")
    st.stop()

df_base = pd.read_excel(BASE_HISTORICA)
df_base = normalizar_columnas(df_base)
df_base = asegurar_columnas(df_base)

st.success("Base histórica cargada")

# -----------------------------
# Subir mes nuevo
# -----------------------------
st.subheader("📤 Cargar mes nuevo")

uploaded_file = st.file_uploader(
    "Sube el archivo mensual (plantilla estándar)",
    type=["xlsx"]
)

if uploaded_file:
    df_nuevo = pd.read_excel(uploaded_file)
    df_nuevo = normalizar_columnas(df_nuevo)
    df_nuevo = asegurar_columnas(df_nuevo)

    # Unir histórico + nuevo
    df_total = pd.concat([df_base, df_nuevo], ignore_index=True)

    # Blindaje contra duplicados
    df_total = df_total.drop_duplicates(
        subset=["PERIODO", "IDH"],
        keep="last"
    )

    st.success("Mes agregado correctamente")

    # -----------------------------
    # Análisis
    # -----------------------------
    totales = calcular_totales_periodo(df_total)
    variaciones = calcular_variaciones_periodo(totales)

    st.subheader("📈 Totales por periodo")
    st.dataframe(totales.round(2))

    st.subheader("📉 Variaciones (%)")
    st.dataframe(variaciones.round(2))

    # -----------------------------
    # Correo
    # -----------------------------
    st.subheader("📧 Generar correo")

    periodo = st.selectbox(
        "Selecciona periodo a reportar",
        totales.index.tolist(),
        index=len(totales.index) - 1
    )

    correo = generar_reporte_correo(
        variaciones.loc[:periodo],
        totales.loc[:periodo]
    )

    st.text_area("Correo generado", correo, height=280)

    # -----------------------------
    # Chat
    # -----------------------------
    st.subheader("💬 Pregúntale al bot")

    pregunta = st.text_input("Ejemplo: Top idh, costo unitario ultimo")

    if pregunta:
        respuesta = responder_pregunta(df_total, totales, variaciones, pregunta)
        st.text_area("Respuesta", respuesta, height=200)