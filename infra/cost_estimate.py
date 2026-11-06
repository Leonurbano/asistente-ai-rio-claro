"""
Validación de presupuesto — corre este script para confirmar que $100 USD
alcanzan, con los precios públicos de Azure (nov-2026, región East US,
sujeto a cambio: verificar en https://azure.microsoft.com/pricing/ antes
de confiar en esto para una decisión real de gasto grande).
"""

# Precios gpt-4o-mini (USD por 1M tokens) — Azure OpenAI / Foundry Models
PRECIO_INPUT_POR_1M = 0.15
PRECIO_OUTPUT_POR_1M = 0.60

# Supuestos de uso explícitos (ajusta si tu plan de pruebas es distinto)
MENSAJES_DESARROLLO = 150   # pruebas tuyas mientras construyes
MENSAJES_DEMO_EQUIPO = 40    # ensayos de tu equipo antes de entregar
MENSAJES_EVALUADOR = 30     # lo que el profesor/revisor probará
TOKENS_INPUT_PROMEDIO = 600   # mensaje del usuario + system prompt + contexto recuperado
TOKENS_OUTPUT_PROMEDIO = 250  # respuesta del agente

OTROS_COSTOS_FIJOS = {
    "File Search (almacenamiento de vectores, ~2-3 semanas, <100MB)": 1.00,
    "Azure Functions (plan de consumo)": 0.00,
    "Static Web Apps (plan gratuito)": 0.00,
    "Azure Key Vault (operaciones)": 0.50,
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
