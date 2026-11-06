"""
Valida el principio de EQUIDAD a nivel de contenido: la base de conocimiento
que carga el agente debe representar a las 5 sucursales, no solo a la que
tenía "más y mejores datos" (la pregunta textual del PDF oficial).
"""
import os

from guardrails import SUCURSALES

KB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "caso-rio-claro.md")


def test_las_5_sucursales_aparecen_en_la_base_de_conocimiento():
    with open(KB_PATH, encoding="utf-8") as f:
        content = f.read()
    faltantes = [s for s in SUCURSALES if s not in content]
    assert not faltantes, f"Sucursales ausentes de la base de conocimiento: {faltantes}"


def test_el_catalogo_normalizado_tiene_stock_para_cada_sucursal():
    with open(KB_PATH, encoding="utf-8") as f:
        content = f.read()
    tabla = content.split("## 6. Catálogo de productos")[1].split("## 7.")[0]
    for s in SUCURSALES:
        assert s in tabla, f"La tabla de catálogo no incluye columna/stock de {s}"
