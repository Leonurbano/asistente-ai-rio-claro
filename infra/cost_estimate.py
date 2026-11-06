"""
Validación de presupuesto que corrí antes de desplegar, para confirmar que
los $100 USD de Azure for Students alcanzaban (precios públicos, nov-2026).

Nota: los precios de abajo son de gpt-4o-mini, el modelo con el que validé
presupuesto originalmente; el despliegue final usó gpt-5-mini, así que esto
es una referencia conservadora, no el costo exacto del modelo final.
"""

# Precios gpt-4o-mini (USD por 1M tokens) — Azure OpenAI / Foundry Models
PRECIO_INPUT_POR_1M = 0.15
PRECIO_OUTPUT_POR_1M = 0.60

# Supuestos de uso
MENSAJES_DESARROLLO = 150   # mis pruebas mientras construía
MENSAJES_DEMO_EQUIPO = 40    # ensayos antes de entregar
MENSAJES_EVALUADOR = 30     # lo que el profesor/revisor probaría
TOKENS_INPUT_PROMEDIO = 600   # mensaje del usuario + system prompt + contexto recuperado
TOKENS_OUTPUT_PROMEDIO = 250  # respuesta del agente

OTROS_COSTOS_FIJOS = {
    "File Search (almacenamiento de vectores, ~2-3 semanas, <100MB)": 1.00,
    "Azure Functions (plan de consumo)": 0.00,
    "Storage Account - sitio web estático": 0.00,
    "Azure AI Speech (tier F0, si se usa)": 0.00,
}


def calcular():
    total_mensajes = MENSAJES_DESARROLLO + MENSAJES_DEMO_EQUIPO + MENSAJES_EVALUADOR
    total_input_tokens = total_mensajes * TOKENS_INPUT_PROMEDIO
    total_output_tokens = total_mensajes * TOKENS_OUTPUT_PROMEDIO

    costo_input = (total_input_tokens / 1_000_000) * PRECIO_INPUT_POR_1M
    costo_output = (total_output_tokens / 1_000_000) * PRECIO_OUTPUT_POR_1M
    costo_modelo = costo_input + costo_output
    costo_fijos = sum(OTROS_COSTOS_FIJOS.values())
    total = costo_modelo + costo_fijos

    print(f"Mensajes totales estimados: {total_mensajes} (desarrollo {MENSAJES_DESARROLLO} + demo {MENSAJES_DEMO_EQUIPO} + evaluador {MENSAJES_EVALUADOR})")
    print(f"Tokens de entrada totales: {total_input_tokens:,} -> ${costo_input:.4f}")
    print(f"Tokens de salida totales:  {total_output_tokens:,} -> ${costo_output:.4f}")
    print(f"Costo del modelo (gpt-4o-mini): ${costo_modelo:.4f}")
    for nombre, costo in OTROS_COSTOS_FIJOS.items():
        print(f"  + {nombre}: ${costo:.2f}")
    print(f"Costo fijo total: ${costo_fijos:.2f}")
    print(f"----")
    print(f"TOTAL ESTIMADO: ${total:.2f} de $100.00 disponibles")
    print(f"Margen restante: ${100 - total:.2f} ({(100 - total) / 100 * 100:.1f}%)")

    assert total < 20, f"El estimado (${total:.2f}) superó el umbral de seguridad de $20 — revisar supuestos"
    return total


if __name__ == "__main__":
    calcular()
