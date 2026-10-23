# Asistente Jurídico Vial Multijurisdiccional (RAG MVP)

Prototipo de un asistente legal basado en **Retrieval-Augmented Generation (RAG)** diseñado para consultar, cruzar y citar normativas de tránsito, movilidad y transporte en tres niveles de jurisdicción en México: **Municipal (Cuernavaca), Estatal (Morelos) y Federal (Carreteras y Puentes)**.

**[Probar el Agente en Vivo aquí (Dify Web App)](TU_LINK_PUBLICO_DE_DIFY_AQUI)**  
*(Nota: El demo opera sobre una cuota gratuita de API limitada por minuto; si recibes un error de límite de cuota, intenta nuevamente en unos minutos).*

---

**Nota sobre el Desarrollo y la Asistencia de IA**

Este pipeline ETL no fue escrito línea por línea de manera manual tradicional; fue diseñado y orquestado bajo un enfoque de AI-Assisted Engineering. Utilizando grandes modelos de lenguaje como copilotos de desarrollo, la autoría humana se centró en lo verdaderamente crítico: el diseño de la arquitectura, la definición de las reglas de negocio (Data Hygiene), la validación de casos borde (edge cases) en documentos jurídicos y el control de calidad de los datos resultantes (Ground Truth Validation). La IA aceleró la síntesis de sintaxis; la estrategia y la lógica jurídica fueron cien por ciento de diseño propio.

---

## Objetivo del Proyecto

Este proyecto nació como un ejercicio práctico de ingeniería de datos y orquestación de LLMs (desarrollado en un sprint de 2.5 días) para explorar los retos reales detrás de herramientas de asistencia jurídica (como la trazabilidad de fuentes, mitigación de alucinaciones y segmentación de documentos legales). 

El objetivo fue construir un **MVP funcional** que respondiera dudas ciudadanas en lenguaje natural citando explícitamente el artículo, fracción y reglamento aplicable en menos de 300 caracteres.

---

## Arquitectura y Stack Tecnológico

* **Orquestación del Flujo RAG:** [Dify](https://dify.ai/) (Chatflow visual).
* **Preprocesamiento y ETL Documental:** Python (`pypdf`, `re`) para limpieza de ruido institucional y estructuración jerárquica.
* **Modelo de Lenguaje (LLM):** Familia Google Gemini Flash (vía Google AI Studio API - esquema *BYOK*).
* **Estrategia de Segmentación:** *Context-Enriched Chunking* personalizado mediante delimitadores explícitos (`===CHUNK===`).

### Corpus Normativo Integrado
1. **Nivel Municipal:** Reglamento de Tránsito y Vialidad del Municipio de Cuernavaca, Morelos (`159 chunks`).
2. **Nivel Estatal:** Ley de Movilidad, Transporte y Seguridad Vial del Estado de Morelos (`284 chunks`).
3. **Nivel Federal:** Reglamento de Tránsito en Carreteras y Puentes de Jurisdicción Federal (`302 chunks`).

---

## Retos Técnicos Superados (Ingeniería de Datos y RAG)

### 1. El problema de los "Orphan Chunks" (Fragmentos Huérfanos)
Al indexar documentos legales extensos mediante saltos de línea simples (`\n`), las fracciones e incisos (ej. `I.`, `II.`, `a)`) quedaban separados del encabezado de su artículo. Además, los encabezados y pies de página del Periódico Oficial contaminaban la búsqueda semántica.
* **Solución:** Se desarrolló un pipeline en Python que limpia el ruido institucional, reconstruye párrafos rotos e inyecta una cabecera de metadatos en cada bloque antes de enviarlo a la base vectorial:
  `[Fuente: Ley de Movilidad Morelos | TÍTULO OCTAVO | CAPÍTULO I | Artículo 127]`[cite: 112]

### 2. Alcance y Vacíos de Jurisdicción
Durante las pruebas iniciales, consultas cotidianas como *"¿Puedo circular en bicicleta por una autopista?"* o dudas sobre *scooters eléctricos* arrojaban respuestas vacías porque el reglamento municipal no regula tramos federales ni micromovilidad moderna.
* **Solución:** Se escaló la base de conocimiento de un solo documento local a una arquitectura multijurisdiccional de tres capas, permitiendo al nodo *Knowledge Retrieval* recuperar contexto cruzado.

### 3. Determinismo y Control de Alucinaciones
En el ámbito legal, inventar un monto de multa o citar un artículo equivocado invalida la herramienta.
* **Solución:** Ajuste de hiperparámetros (baja temperatura, desactivación de *Grounding* web abierto para forzar lectura exclusiva del corpus) y diseño de un *System Prompt* con reglas de citación obligatoria, refutación de premisas falsas y restricción de longitud (máximo 300 caracteres para lectura rápida).

---

## Limitaciones Actuales del MVP y Trabajo Futuro (Roadmap)

Al ser una prueba de concepto (PoC), el sistema presenta áreas de oportunidad identificadas durante la auditoría de respuestas:
* **Implementación de Reranking Híbrido:** Actualmente depende de la recuperación nativa; integrar un modelo de *Cross-Encoder Reranking* (ej. Cohere Rerank) mejoraría la precisión cuando se consultan las 3 leyes simultáneamente.
* **Capa de Query Expansion (Reescritura de Consultas):** Agregar un nodo LLM ligero previo al *Retrieval* que traduzca jerga ciudadana (*"andar en bici donde sea"*) a terminología jurídica (*"restricciones de circulación para vehículos de tracción humana"*) antes de buscar en la base vectorial.
* **Validación Programática de Citas:** Implementar una verificación post-generación para asegurar que ninguna fracción citada haya sido cruzada entre artículos extensos.

---

## Contenido del Repositorio

* `/data/processed/`: Archivos `.txt` limpios y enriquecidos con metadatos listos para vectorización.
* `/scripts/`: Código en Python utilizado para el procesamiento y limpieza de las leyes.
* `/prompts/`: Iteraciones y versión final del *System Prompt*.
