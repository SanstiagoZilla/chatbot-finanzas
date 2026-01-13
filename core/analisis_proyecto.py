# analisis_proyecto.py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Intentamos importar RandomForest; si no existe, usamos LinearRegression como fallback
try:
    from sklearn.ensemble import RandomForestRegressor
    _HAS_RF = True
except Exception:
    try:
        from sklearn.linear_model import LinearRegression
        _HAS_RF = False
    except Exception:
        _HAS_RF = None  # no model available


# ------------------------------------------------------
# UTIL: Normalizar nombres de columnas
# ------------------------------------------------------
def normalizar_columnas(df):
    """
    Normaliza nombres de columnas: quita espacios al inicio/fin, tildes,
    símbolos no alfanuméricos (salvo _) y convierte a mayúsculas.
    """
    cols = df.columns.astype(str)
    cols = cols.str.strip()
    # Reemplazar tildes (si aplica)
    cols = cols.str.replace("Á", "A", regex=False).str.replace("É", "E", regex=False)
    cols = cols.str.replace("Í", "I", regex=False).str.replace("Ó", "O", regex=False)
    cols = cols.str.replace("Ú", "U", regex=False).str.replace("Ü", "U", regex=False)
    # Quitar caracteres extraños y reemplazar espacios por _
    cols = cols.str.replace(r"[^0-9A-Za-zÁÉÍÓÚÜáéíóúüÑñ ]+", "", regex=True)
    cols = cols.str.replace(" ", "_", regex=False)
    cols = cols.str.upper()
    df.columns = cols
    return df


# ------------------------------------------------------
# UTIL: detectar columna de volumen (VOL)
# ------------------------------------------------------
def detectar_columna_volumen(df):
    candidates = [c for c in df.columns if c.startswith("VOL") or "VOLUME" in c or "QTY" in c]
    if not candidates:
        # buscar más flexible: contiene 'VOL' en cualquier parte
        candidates = [c for c in df.columns if "VOL" in c]
    if not candidates:
        raise KeyError("No se encontró columna de volumen (VOL, VOLUMEN, QTY, etc.). Columnas disponibles: " + ", ".join(df.columns))
    # preferir exactamente "VOL" si existe
    if "VOL" in df.columns:
        return "VOL"
    return candidates[0]


# ------------------------------------------------------
# UTIL: asegurar columnas y crear PERIODO
# ------------------------------------------------------
def asegurar_columnas(df):
    """
    - Detecta o crea PERIODO a partir de AÑO+MES si hace falta.
    - Normaliza y renombra columnas clave: MARCA, IDH.
    - Asegura que L14 exista y detecta VOL.
    """
    # Asegurar mayúsculas y sin espacios (ya hecho por normalizar_columnas),
    # pero hacemos detección flexible de AÑO/MES
    cols = list(df.columns)

    # Detectar AÑO (puede aparecer como AÑO, ANO, YEAR)
    ano_col = None
    for cand in ["AÑO", "ANO", "ANIO", "YEAR"]:
        if cand in df.columns:
            ano_col = cand
            break

    # Detectar MES (MES, MONTH)
    mes_col = None
    for cand in ["MES", "MONTH"]:
        if cand in df.columns:
            mes_col = cand
            break

    # Si no existe PERIODO, intentar crear
    if "PERIODO" not in df.columns:
        if ano_col and mes_col:
            # Normalizar MES de forma segura
            df[mes_col] = (
                df[mes_col]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
                .str.zfill(2)
            )

            # Normalizar AÑO
            df[ano_col] = (
                df[ano_col]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
            )

            # Crear PERIODO
            df["PERIODO"] = df[ano_col] + "-" + df[mes_col]
        else:
            # Si no hay PERIODO ni (AÑO,MES) -> lanzar error claro
            raise ValueError("No existe columna PERIODO ni (AÑO,MES) detectables. Columnas encontradas: " + ", ".join(df.columns))

    # Renombrar posibles nombres de marca
    marca_candidates = ["MARCA", "PSV_BRAND", "BRAND"]
    marca_found = None
    for c in marca_candidates:
        if c in df.columns:
            marca_found = c
            break
    if marca_found:
        df = df.rename(columns={marca_found: "MARCA"})

    # Renombrar posibles nombres de IDH
    idh_candidates = ["IDH", "MAIN_MATERIAL_CODE", "MATERIAL_CODE", "MAIN_MATERIAL"]
    idh_found = None
    for c in idh_candidates:
        if c in df.columns:
            idh_found = c
            break
    if idh_found:
        df = df.rename(columns={idh_found: "IDH"})

    # Verificar L14
    if "L14" not in df.columns:
        # intentar con variantes
        raise ValueError("No se encontró la columna 'L14' en el archivo. Columnas: " + ", ".join(df.columns))

    # Detectar volumen y renombrar a VOL
    vol_col = detectar_columna_volumen(df)
    if vol_col != "VOL":
        df = df.rename(columns={vol_col: "VOL"})

    return df


# ------------------------------------------------------
# FASE 1: cargar datos (archivo por defecto MASTERDATA PROYECTO.xlsx, hoja BD COL)
# ------------------------------------------------------
def cargar_datos(ruta="MASTERDATA PROYECTO.xlsx", sheet_name="BD COL"):
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta} (coloca el archivo en la misma carpeta o cambia la ruta).")

    df = pd.read_excel(ruta, sheet_name=sheet_name)

    # Normalizar columnas (quita espacios, símbolos, pone mayúsculas)
    df = normalizar_columnas(df)

    # Asegurar columnas clave y crear PERIODO si hace falta
    df = asegurar_columnas(df)

    # Convertir PERIODO a string y ordenar por PERIODO
    df["PERIODO"] = df["PERIODO"].astype(str)
    # Calcular costo unitario de forma segura (evita división por cero)
    df["COSTO_UNITARIO"] = df["L14"] / df["VOL"].replace(0, np.nan)

    # Opcional: forzar tipos numéricos para L14 y VOL
    df["L14"] = pd.to_numeric(df["L14"], errors="coerce")
    df["VOL"] = pd.to_numeric(df["VOL"], errors="coerce")

    return df


# ------------------------------------------------------
# Totales por periodo y variaciones
# ------------------------------------------------------
def calcular_totales_periodo(df):
    totales = df.groupby("PERIODO")[["L14", "VOL"]].sum()
    totales["COSTO_UNITARIO"] = totales["L14"] / totales["VOL"].replace(0, np.nan)
    totales = totales.sort_index()
    return totales


def calcular_variaciones_periodo(totales):
    variaciones = totales.pct_change() * 100
    variaciones = variaciones.replace([np.inf, -np.inf], np.nan)
    return variaciones


# ------------------------------------------------------
# Totales y variaciones por marca
# ------------------------------------------------------
def totales_por_marca(df):
    cols = ["L14", "VOL"]
    marca_tot = df.groupby(["PERIODO", "MARCA"])[cols].sum()
    marca_tot["COSTO_UNITARIO"] = marca_tot["L14"] / marca_tot["VOL"].replace(0, np.nan)
    return marca_tot


def variaciones_por_marca(df):
    marca_tot = totales_por_marca(df)
    vari = marca_tot.groupby(level=1).pct_change() * 100
    vari = vari.replace([np.inf, -np.inf], np.nan)
    return vari


# ------------------------------------------------------
# Top variaciones por IDH (solo L14, VOL, COSTO_UNITARIO)
# ------------------------------------------------------
def top_variaciones_idh(df, top_n=10):
    # Agrupar por periodo e IDH
    base = df.groupby(["PERIODO", "IDH"])[["L14", "VOL"]].sum()
    base["COSTO_UNITARIO"] = base["L14"] / base["VOL"].replace(0, np.nan)

    # Calculamos variaciones % por IDH (cada IDH: compare con periodo anterior)
    variaciones = base.groupby(level=1).pct_change() * 100
    variaciones = variaciones.replace([np.inf, -np.inf], np.nan)

    # Tomar la última variación por IDH (último periodo conocido)
    ult = variaciones.groupby("IDH").tail(1)

    resultados = {}
    for kpi in ["L14", "VOL", "COSTO_UNITARIO"]:
        up = ult.sort_values(kpi, ascending=False).head(top_n).round(2)
        down = ult.sort_values(kpi, ascending=True).head(top_n).round(2)
        resultados[kpi] = {"Top_Subidas": up, "Top_Bajadas": down}

    return resultados


# ------------------------------------------------------
# FASE 2: generar texto de correo (solo texto, no envío)
# ------------------------------------------------------
def generar_reporte_correo(variaciones, totales, periodo=None):
    if len(totales) < 2:
        return "No hay suficientes periodos para comparar."

    if periodo is None:
        periodo = totales.index[-1]

    idx = totales.index.get_loc(periodo)

    if idx == 0:
        return f"No existe periodo anterior para comparar {periodo}"

    ultimo = totales.iloc[idx]
    anterior = totales.iloc[idx - 1]
    var = variaciones.iloc[idx]

    def fmt(x):
        try:
            return f"{x:,.2f}"
        except Exception:
            return str(x)

    texto = f"""
Equipo,

Adjunto resumen automático — análisis de KPIs (Colombia).

PERIODO ANALIZADO: {periodo}

Resultados (vs periodo anterior):
- L14 total: {fmt(ultimo['L14'])} (anterior {fmt(anterior['L14'])})
- Volumen total: {fmt(ultimo['VOL'])} (anterior {fmt(anterior['VOL'])})
- Costo unitario: {fmt(ultimo['COSTO_UNITARIO'])}

Variaciones %:
- L14: {fmt(var['L14'])} %
- Volumen: {fmt(var['VOL'])} %
- Costo unitario: {fmt(var['COSTO_UNITARIO'])} %

Insights:
- El costo unitario {'subió' if var['COSTO_UNITARIO'] > 0 else 'bajó'} respecto al mes anterior.
- Revisar IDH y marcas con mayor impacto.

Saludos,
Análisis Automático
"""
    return texto

# ------------------------------------------------------
# FASE 3: gráficas (guarda y muestra)
# ------------------------------------------------------
def graficar_series(totales, guardar=False, carpeta="graficos"):
    if guardar and not os.path.exists(carpeta):
        os.makedirs(carpeta)

    # ---- L14 ----
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    totales["L14"].plot(marker="o", ax=ax1)
    ax1.set_title("L14 por periodo")
    ax1.set_xlabel("Periodo")
    ax1.set_ylabel("L14")
    ax1.grid(True)
    plt.tight_layout()
    if guardar:
        fig1.savefig(os.path.join(carpeta, "L14.png"))
    plt.show()

    # ---- VOL ----
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    totales["VOL"].plot(marker="o", ax=ax2)
    ax2.set_title("Volumen por periodo")
    ax2.set_xlabel("Periodo")
    ax2.set_ylabel("Volumen")
    ax2.grid(True)
    plt.tight_layout()
    if guardar:
        fig2.savefig(os.path.join(carpeta, "VOL.png"))
    plt.show()

    # ---- Costo unitario ----
    fig3, ax3 = plt.subplots(figsize=(10, 4))
    totales["COSTO_UNITARIO"].plot(marker="o", ax=ax3)
    ax3.set_title("Costo unitario por periodo")
    ax3.set_xlabel("Periodo")
    ax3.set_ylabel("Costo unitario")
    ax3.grid(True)
    plt.tight_layout()
    if guardar:
        fig3.savefig(os.path.join(carpeta, "Costo_Unitario.png"))
    plt.show()
# ------------------------------------------------------
# FASE 4: predicción simple del próximo periodo
# ------------------------------------------------------
def prediccion_simple(totales):
    # Usamos indice numérico del periodo como variable X
    t = totales.reset_index().copy()
    t["PERIODO_NUM"] = np.arange(len(t))

    X = t[["PERIODO_NUM"]].values
    y = t["COSTO_UNITARIO"].values

    # Elegir modelo disponible
    if _HAS_RF is True:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        pred = model.predict([[len(t)]])[0]
    elif _HAS_RF is False:
        # usamos linear if RF not available
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)
        pred = model.predict([[len(t)]])[0]
    else:
        # Si no hay sklearn instalado, devolvemos NaN
        pred = np.nan

    return pred


# ------------------------------------------------------
# FASE 5: chat simple con reglas
# ------------------------------------------------------
def responder_pregunta(df, totales, variaciones, pregunta):
    q = pregunta.lower()

    if ("top" in q or "top 5" in q) and ("idh" in q or "material" in q):
        resultados = top_variaciones_idh(df, top_n=5)
        texto = "Top IDH (Costo Unitario) - Subidas:\n"
        texto += resultados["COSTO_UNITARIO"]["Top_Subidas"].to_string()
        texto += "\n\nTop IDH (Costo Unitario) - Bajadas:\n"
        texto += resultados["COSTO_UNITARIO"]["Top_Bajadas"].to_string()
        return texto

    if "costo unitario" in q and ("ultimo" in q or "último" in q):
        val = totales["COSTO_UNITARIO"].iloc[-1]
        return f"Costo unitario último periodo ({totales.index[-1]}): {val:,.2f}"

    if "variacion" in q and "l14" in q:
        val = variaciones["L14"].iloc[-1]
        return f"Variación % última de L14: {val:,.2f}%"

    if "marca" in q and "peor" in q:
        # ejemplo: marca con mayor subida en L14
        marca_tot = totales_por_marca(df)
        # busco último periodo
        last_period = totales.index[-1]
        try:
            df_last = marca_tot.loc[last_period]
            top = df_last.sort_values("L14", ascending=False).head(5)
            return f"Top marcas por L14 (último periodo):\n{top.to_string()}"
        except Exception:
            return "No se pudo calcular top por marca para el último periodo."

    return "No entendí la pregunta. Prueba: 'Top idh', 'costo unitario ultimo', 'variacion l14'."


# ------------------------------------------------------
# FUNCIÓN MAESTRA: ejecutar todas las fases
# ------------------------------------------------------
def probar():
    print("\n== CARGANDO DATOS ==\n")
    df = cargar_datos(ruta="MASTERDATA PROYECTO.xlsx", sheet_name="BD COL")

    print("COLUMNAS NORMALIZADAS:")
    print(df.columns.tolist())

    # Totales y variaciones por periodo
    totales = calcular_totales_periodo(df)
    variaciones = calcular_variaciones_periodo(totales)

    # Totales y variaciones por marca
    marcas_tot = totales_por_marca(df)  # DataFrame multiindex Periodo, Marca
    marcas_var = variaciones_por_marca(df)

    # Top IDH
    tops = top_variaciones_idh(df, top_n=10)

    # Imprimir resultados resumidos
    print("\n=== TOTALES POR PERIODO ===\n")
    print(totales.round(2))

    print("\n=== VARIACIONES POR PERIODO (%) ===\n")
    print(variaciones.round(2))

    print("\n=== TOTALES POR MARCA (últimos registros) ===\n")
    try:
        # mostramos el último periodo por marca
        last_period = totales.index[-1]
        print(marcas_tot.loc[last_period].round(2))
    except Exception:
        print(marcas_tot.head(10).round(2))

    # Correo
    print("\n=== CORREO GENERADO ===\n")
    print(generar_reporte_correo(variaciones, totales))

    # Chat de prueba
    print("\n=== CHAT PRUEBA ===\n")
    print(responder_pregunta(df, totales, variaciones, "Top idh que mas subieron"))

    # Predicción
    pred = prediccion_simple(totales)
    print(f"\nPredicción próximo COSTO_UNITARIO: {pred:,.2f}")

    # Gráficos (muestra)
    graficar_series(totales, guardar=False)


# Si se ejecuta como script principal
if __name__ == "__main__":
    probar()
def ejecutar_analisis_completo(df):
    """
    Ejecuta todo el pipeline a partir de un DataFrame ya cargado
    (Streamlit, Excel, Power BI, etc.)
    """
    totales = calcular_totales_periodo(df)
    variaciones = calcular_variaciones_periodo(totales)
    marcas_tot = totales_por_marca(df)
    marcas_var = variaciones_por_marca(df)
    tops = top_variaciones_idh(df, top_n=10)
    texto_correo = generar_reporte_correo(variaciones, totales)

    return {
        "totales": totales,
        "variaciones": variaciones,
        "marcas_tot": marcas_tot,
        "marcas_var": marcas_var,
        "tops": tops,
        "correo": texto_correo
    }
