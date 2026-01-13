"""
Proyecto: Chatbot Analítico KPIs Colombia
Autor: Santiago Garcia
Descripción:
Este módulo contiene toda la lógica de negocio para el análisis de KPIs:
- Limpieza y normalización de datos (robusto a errores en Excel / Power BI)
- Cálculo de totales y variaciones mes a mes
- Análisis por marca e IDH
- Generación automática de resumen ejecutivo
- Motor básico de preguntas tipo chatbot

Este archivo NO contiene interfaz gráfica.
La interfaz (Streamlit) importa y consume estas funciones.
"""
