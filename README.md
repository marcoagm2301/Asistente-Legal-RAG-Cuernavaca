# Asistente Jurídico Vial Multijurisdiccional (RAG MVP)

Prototipo de un asistente legal basado en **Retrieval-Augmented Generation (RAG)** diseñado para consultar, cruzar y citar normativas de tránsito, movilidad y transporte en tres niveles de jurisdicción en México: **Municipal (Cuernavaca), Estatal (Morelos) y Federal (Carreteras y Puentes)**.

**Probar el Agente en Vivo aquí [Dify Web App](https://udify.app/chat/4DLVIDv2ZFbZYAgA) (Necesita activación de API de Google IA para su funcionamiento)**  

---

## Objetivo del Proyecto

Este proyecto nació como un ejercicio práctico de ingeniería de datos y orquestación de LLMs (desarrollado en un sprint de 2.5 días) para explorar los retos reales detrás de herramientas de asistencia jurídica automatizada, tales como la trazabilidad exacta de fuentes, la mitigación de alucinaciones y la segmentación de corpus legales extensos.

---

**Nota sobre el Desarrollo y la Asistencia de IA**

Este pipeline ETL no fue escrito línea por línea de manera manual tradicional; fue diseñado y orquestado bajo un enfoque de AI-Assisted Engineering. Utilizando grandes modelos de lenguaje como copilotos de desarrollo, la autoría humana se centró en lo verdaderamente crítico: el diseño de la arquitectura, la definición de las reglas de negocio (Data Hygiene), la validación de casos borde (edge cases) en documentos jurídicos y el control de calidad de los datos resultantes (Ground Truth Validation). La IA aceleró la síntesis de sintaxis; la estrategia y la lógica jurídica fueron cien por ciento de diseño propio.

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

## Retos Técnicos, Obstáculos y Consideraciones de Uso

Durante el desarrollo y las pruebas de estrés (*QA*) del asistente, nos enfrentamos a desafíos críticos inherentes a la indexación de documentos jurídicos. Es fundamental tener en cuenta los siguientes puntos para comprender el comportamiento de la herramienta:

### 1. El Desafío de la Semántica y el Vocabulario Jurídico
Uno de los mayores obstáculos en los sistemas RAG aplicados al derecho es la discrepancia entre el **lenguaje coloquial del usuario** y la **terminología estricta de las leyes**. 
* **El problema:** Consultas formuladas con términos cotidianos o imprecisos (por ejemplo, referirse coloquialmente a una infracción o a un tipo de vehículo sin su denominación técnica oficial) pueden provocar falsos negativos o respuestas nulas, ya que el motor de búsqueda vectorial calcula similitudes matemáticas directas.
* **Recomendación de uso:** La calidad, precisión y optimización de los resultados dependen directamente de la semántica y los términos empleados en la consulta. Redactar preguntas utilizando conceptos jurídicos afines o complementarios facilita enormemente que el agente recupere el artículo correcto.

### 2. Prevención de Falsos Negativos ante Preguntas en Negativo o Prohibiciones
Las leyes y reglamentos no operan bajo prohibiciones absolutas para todos los supuestos, sino mediante marcos regulatorios, habilitaciones de derechos o excepciones (por ejemplo, la regulación de grupos vulnerables o permisos especiales). 
* **El problema:** Preguntas formuladas en sentido negativo (ej. indagando por prohibiciones inexistentes) suelen confundir a los modelos tradicionales orientados a una literalidad estricta, llevándolos a responder de manera prematura que "no hay información".
* **Solución aplicada:** Se calibraron las reglas del sistema y los hiperparámetros para interpretar la intención normativa subyacente y evitar bloqueos por falsos vacíos legales.

### 3. Mitigación de "Orphan Chunks" (Fragmentos Huérfanos)
Al indexar documentos legales extensos mediante saltos de línea genéricos, las fracciones (`I, II...`) y los incisos quedaban separados del encabezado de su artículo, perdiendo contexto.
* **Solución:** Se implementó un pipeline de ETL en Python que limpia el ruido institucional (periódicos oficiales, sellos y paginación) e inyecta dinámicamente metadatos de jerarquía en cada bloque (`[Fuente | Título | Capítulo | Artículo]`).

---

## Limitaciones Actuales y Trabajo Futuro (Roadmap)

* **Implementación de Reranking Híbrido:** Integrar un modelo de *Cross-Encoder Reranking* para refinar el orden de relevancia de los fragmentos recuperados.
* **Capa de Query Expansion:** Incorporar un nodo intermedio de reescritura de consultas que traduzca automáticamente la jerga ciudadana a terminología jurídica antes de la búsqueda vectorial.

---

## 📂 Contenido del Repositorio

* `/data/processed/`: Archivos `.txt` limpios y enriquecidos con metadatos listos para vectorización.
* `/scripts/`: Código en Python utilizado para el procesamiento y limpieza de las leyes.
* `/prompts/`: Iteraciones y versión final del *System Prompt*.
