"""
Pipeline ETL y Context-Enriched Chunking para Documentos Normativos (RAG)
========================================================================
Este script extrae texto de archivos PDF o TXT legales, elimina el ruido
institucional (encabezados, pies de página, sellos de agua), reconstruye
párrafos cortados por saltos de línea y aplica Context-Enriched Chunking,
inyectando la jerarquía normativa (Fuente, Título, Capítulo y Artículo)
al inicio de cada bloque separado por el delimitador '===CHUNK==='.

Requisitos:
    pip install pypdf
"""

import os
import re
import argparse
from typing import List, Dict
import pypdf


# =====================================================================
# 1. DICCIONARIO DE CONFIGURACIÓN POR JURISDICCIÓN (REGLAS DE HIGIENE)
# =====================================================================
PROFILES: Dict[str, Dict] = {
    "cuernavaca": {
        "source_label": "Reglamento de Tránsito de Cuernavaca",
        "noise_phrases": [
            "Consejería Jurídica del Poder Ejecutivo del Estado de Morelos",
            "Consejería Juridica del Poder Ejecutivo del Estado de Morelos",
            "Dirección General de Legislación",
            "Subdirección de Jurismática",
            "Reglamento de Tránsito y Vialidad para el Municipio de Cuernavaca",
            "Última Reforma:",
            "Aprobación",
            "Publicación",
            "Vigencia",
            "Expidió",
            "Periódico Oficial",
        ],
        "noise_regex": [
            r"^\d+\s+de\s+\d+$",
            r"^\d{4}/\d{2}/\d{2}$",
            r"^\.{3,}$",
        ],
    },
    "federal": {
        "source_label": "Reglamento de Tránsito Federal",
        "noise_phrases": [
            "SEGUNDA SECCION",
            "PODER EJECUTIVO",
            "SECRETARIA DE SEGURIDAD PUBLICA",
            "Al margen un sello con el Escudo Nacional",
            "DIARIO OFICIAL",
        ],
        "noise_regex": [
            r"^\d+\s+de\s+\d+$",
        ],
    },
    "morelos": {
        "source_label": "Ley de Movilidad Morelos",
        "noise_phrases": [
            "Consejería Juridica del Poder Ejecutivo del Estado de Morelos",
            "Consejería Jurídica del Poder Ejecutivo del Estado de Morelos",
            "Dirección General de Normatividad",
            "Subdirección de Jurismática",
            "Ley de Movilidad, Transporte y Seguridad Vial del Estado de Morelos",
            "Última Reforma:",
            "Aprobación",
            "Promulgación",
            "Publicación",
            "Vigencia",
            "Expidió",
            "Periódico Oficial",
            "BRA VILVERA",
            "UIENES LA",
            "ABAJAN CON-SUS",
            "VISAVW",
            "2024-2030",
        ],
        "noise_regex": [
            r"^\d+\s+de\s+\d+$",
            r"^\d{4}/\d{2}/\d{2}$",
            r"^\.{3,}$",
        ],
    },
}


# =====================================================================
# 2. CAPA DE EXTRACCIÓN (PDF / TXT)
# =====================================================================
def extract_raw_lines(filepath: str) -> List[str]:
    """Extrae las líneas crudas desde un archivo .pdf o .txt."""
    ext = os.path.splitext(filepath)[1].lower()
    lines = []

    if ext == ".pdf":
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))
    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")
    else:
        raise ValueError(f"Formato de archivo no soportado: {ext}. Usa .pdf o .txt")

    return lines


# =====================================================================
# 3. CAPA DE DATA HYGIENE (LIMPIEZA Y RECONSTRUCCIÓN DE PÁRRAFOS)
# =====================================================================
def clean_and_merge_lines(raw_lines: List[str], profile: Dict) -> List[str]:
    """
    Filtra encabezados/pies de página y une líneas cortadas a mitad de oración,
    respetando los inicios de Títulos, Capítulos, Artículos, Fracciones e Incisos.
    """
    clean_lines = []
    noise_phrases = profile.get("noise_phrases", [])
    noise_regex = [re.compile(pattern) for pattern in profile.get("noise_regex", [])]

    for line in raw_lines:
        ls = line.strip()
        if not ls:
            continue

        # 1. Filtrar por frases de ruido institucional conocidas
        if any(phrase.lower() in ls.lower() for phrase in noise_phrases):
            continue

        # 2. Filtrar por patrones regex (paginación, fechas sueltas, líneas punteadas)
        if any(regex.match(ls) for regex in noise_regex):
            continue

        clean_lines.append(ls)

    # Patrón que identifica el inicio de una unidad estructural legal
    structural_pattern = re.compile(
        r"^(TÍTULO\s+[IVXLCDM\w]+|CAPÍTULO\s+[IVXLCDM\w]+|SECCIÓN\s+[IVXLCDM\w]+|"
        r"Artículo\s+\d+|ARTÍCULO\s+\d+|TRANSITORIOS|DISPOSICIONES\s+TRANSITORIAS|"
        r"ARTÍCULOS\s+TRANSITORIOS|[IVXLCDM]+[\.\-\)]|\d+[\.\-\)]|[a-zA-Z][\)\.\-])"
    )

    merged_lines = []
    for line in clean_lines:
        if structural_pattern.match(line):
            merged_lines.append(line)
        else:
            if merged_lines:
                merged_lines[-1] += " " + line
            else:
                merged_lines.append(line)

    return merged_lines


# =====================================================================
# 4. MOTOR DE CONTEXT-ENRICHED CHUNKING (MÁQUINA DE ESTADOS)
# =====================================================================
def build_enriched_chunks(
    merged_lines: List[str],
    source_label: str,
    max_chunk_chars: int = 1200,
) -> List[str]:
    """
    Recorre las líneas limpias manteniendo en memoria el Título, Capítulo y Artículo
    actual. Si un artículo con muchas fracciones supera `max_chunk_chars`, lo divide
    en sub-bloques pero inyecta siempre el encabezado jerárquico y el primer párrafo
    del artículo para evitar 'orphan chunks'.
    """
    chunks = []
    current_title = "DISPOSICIONES GENERALES"
    current_chapter = "CAPÍTULO INICIAL"
    current_article = "Preámbulo"
    current_article_intro = ""
    current_buffer = []
    current_len = 0

    def flush_buffer():
        nonlocal current_buffer, current_len
        if not current_buffer:
            return
        header = f"[Fuente: {source_label} | {current_title} | {current_chapter} | {current_article}]"
        if current_article_intro and current_article_intro not in current_buffer[0]:
            body = f"{header}\n{current_article_intro}\n" + "\n".join(current_buffer)
        else:
            body = f"{header}\n" + "\n".join(current_buffer)
        chunks.append(body)
        current_buffer = []
        current_len = 0

    article_regex = re.compile(r"^(?:Artículo|ARTÍCULO)\s+(\d+)\s*[\.\-]?\s*(.*)")

    for item in merged_lines:
        if item.upper().startswith("TÍTULO"):
            flush_buffer()
            current_title = item
            continue

        if item.upper().startswith("CAPÍTULO") or item.upper().startswith("SECCIÓN"):
            flush_buffer()
            current_chapter = item
            continue

        if "TRANSITORIO" in item.upper() or "TRANSITORIA" in item.upper():
            flush_buffer()
            current_title = "TRANSITORIOS"
            current_chapter = "Disposiciones Transitorias"
            current_article = "Transitorios"
            current_article_intro = ""
            current_buffer.append(item)
            current_len += len(item)
            continue

        m_art = article_regex.match(item)
        if m_art:
            flush_buffer()
            art_num = m_art.group(1)
            art_text = m_art.group(2)
            current_article = f"Artículo {art_num}"
            current_article_intro = (
                f"Artículo {art_num}.- {art_text[:200]}..."
                if len(art_text) > 200
                else f"Artículo {art_num}.- {art_text}"
            )
            current_buffer.append(f"Artículo {art_num}.- {art_text}")
            current_len += len(item)
        else:
            if current_len + len(item) > max_chunk_chars and current_buffer:
                flush_buffer()
            current_buffer.append(item)
            current_len += len(item)

    flush_buffer()
    return chunks


# =====================================================================
# 5. CLI PRINCIPAL
# =====================================================================
def process_document(input_path: str, output_path: str, profile_name: str, max_chars: int = 1200):
    if profile_name not in PROFILES:
        raise ValueError(f"Perfil '{profile_name}' no reconocido. Opciones: {list(PROFILES.keys())}")

    profile = PROFILES[profile_name]
    print(f"[*] Extrayendo texto de: {input_path}")
    raw_lines = extract_raw_lines(input_path)

    print(f"[*] Aplicando Data Hygiene con perfil '{profile_name}'...")
    merged_lines = clean_and_merge_lines(raw_lines, profile)

    print(f"[*] Generando Context-Enriched Chunks (máx {max_chars} chars por bloque)...")
    chunks = build_enriched_chunks(merged_lines, profile["source_label"], max_chars)

    output_text = "\n\n===CHUNK===\n\n".join(chunks)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    print(f"[+] ¡Proceso completado! Total de chunks generados: {len(chunks)}")
    print(f"[+] Archivo guardado en: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline ETL y Context-Enriched Chunking para normativas legales en Dify RAG."
    )
    parser.add_argument("--input", "-i", required=True, help="Ruta del archivo de entrada (.pdf o .txt)")
    parser.add_argument("--output", "-o", required=True, help="Ruta del archivo de salida (.txt)")
    parser.add_argument(
        "--profile",
        "-p",
        required=True,
        choices=["cuernavaca", "federal", "morelos"],
        help="Perfil de limpieza según la jurisdicción del documento",
    )
    parser.add_argument(
        "--max-chars",
        "-m",
        type=int,
        default=1200,
        help="Longitud máxima aproximada por chunk antes de dividir fracciones (default: 1200)",
    )

    args = parser.parse_args()
    process_document(args.input, args.output, args.profile, args.max_chars)
