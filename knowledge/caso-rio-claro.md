# Base de conocimiento — Distribuidora Río Claro

> Este documento es la fuente de verdad que carga el agente (File Search). Todo su contenido proviene del brief oficial `Proyecto_AI-901_Rio_Claro Final.pdf`. El agente debe citar las secciones de este documento al responder, nunca inventar datos fuera de él.

## 1. Perfil de la empresa

Distribuidora Río Claro es una distribuidora familiar de productos de limpieza e higiene con 22 años en el mercado, 140 empleados y 5 sucursales: **Guadalajara, Zapopan, León, Querétaro y Aguascalientes**. Vende a hoteles, restaurantes, escuelas y pequeñas tiendas. Compra a ~60 proveedores y atiende a ~1,800 clientes activos. No tiene área de TI formal; una sola persona de soporte administra correo y red.

## 2. Por qué buscan IA

En el último año perdieron dos clientes hoteleros grandes por falta de respuesta oportuna, y cuentas por pagar pagó dos veces la misma factura a un proveedor. La dirección pide: (1) dejar de capturar facturas a mano, (2) un asistente que responda a clientes y empleados en minutos.

## 3. Inventario del desorden (fuentes de datos)

| Fuente | Estado actual | Ejemplo del problema |
|---|---|---|
| Facturas de proveedores | PDF y fotos en correos personales de 3 compradores distintos, sin carpeta ni nombre estándar | Misma factura como PDF y foto → pagada dos veces |
| Catálogo de productos | Un Excel por sucursal, columnas y nombres distintos | "Cloro 1L", "CLORO LITRO", "Blanqueador 1000ml" son el mismo producto con 3 claves |
| Quejas y dudas de clientes | WhatsApp, llamadas, correos — nada centralizado | Un hotel reclamó 4 veces por el mismo retraso sin que nadie conectara los casos |
| Políticas internas | Word desactualizado en USB y en la cabeza del gerente | 3 versiones distintas de la política de devoluciones |
| Permisos y datos sensibles | Contraseña compartida de una carpeta con nóminas, precios y datos de clientes | Un vendedor puede ver lo que gana el gerente de otra sucursal |

## 4. Restricciones del proyecto

- Presupuesto limitado: piloto pequeño, justificar cada servicio.
- Sin personal técnico: la solución la debe poder usar gente de bodega y ventas, algunos solo desde celular o por voz.
- No se puede "empezar de cero": la operación no se detiene.
- Confianza: Laura y los gerentes temen que la IA "los reemplace" o invente cifras — debe quedar claro que la IA apoya y siempre hay una persona que revisa.

## 5. Personajes (para diseñar y probar el prototipo)

| Personaje | Preocupación | Éxito es... |
|---|---|---|
| Don Ernesto, director general | Perder clientes grandes, no saber cuánto vende cada sucursal | Reporte de ventas donde las 5 sucursales coincidan |
| Laura, cuentas por pagar | Que la IA se equivoque con dinero o la reemplace | Pasar de ~12 hrs/semana de captura a <2, cero pagos duplicados |
| Mariana, gerente de sucursal León | Clientes molestos sin seguimiento | Responder a cualquier cliente en <15 minutos, sin importar la sucursal |
| Toño, jefe de bodega | No usa computadora, todo por teléfono | Preguntar por voz desde el celular y obtener respuesta correcta |
| Carlos, soporte y sistemas | Ser el único responsable de algo que no conoce | Accesos por persona, secretos guardados, poder apagar el sistema si falla |

## 6. Catálogo de productos — ejemplo de datos normalizados (para la demo del prototipo)

> Este es un ejemplo ilustrativo construido por el equipo del proyecto para que el agente tenga datos reales que buscar. Normaliza el problema descrito en la sección 3 (mismo producto, 3 claves distintas) en una sola fuente de verdad por sucursal.

| SKU único | Nombre normalizado | Guadalajara (stock) | Zapopan (stock) | León (stock) | Querétaro (stock) | Aguascalientes (stock) |
|---|---|---|---|---|---|---|
| RC-0001 | Cloro líquido 1L | 120 | 85 | 60 | 95 | 40 |
| RC-0002 | Jabón líquido para manos 1L | 200 | 150 | 90 | 110 | 70 |
| RC-0003 | Papel higiénico (paquete 12 rollos) | 300 | 220 | 180 | 160 | 130 |

## 7. Políticas internas vigentes (versión única consolidada)

**Política de devoluciones (vigente, reemplaza las 3 versiones contradictorias en papel):** un cliente puede devolver producto cerrado dentro de 15 días naturales con factura o nota de remisión. Producto de limpieza abierto no tiene devolución por higiene, salvo defecto de fábrica comprobado por el gerente de sucursal.

## 8. Ejemplo de factura con dato dudoso (para probar el guardrail de "revisión humana")

Factura `PROV-00231`, proveedor "Limpiadores del Bajío", fecha ilegible en la imagen, total parcialmente cubierto por una mancha: se alcanza a leer "$4,8_ _.00". El agente debe responder que el total no es legible con certeza y marcar la factura para revisión humana, **nunca inventar la cifra faltante**.
