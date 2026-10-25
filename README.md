# Multi-Jurisdictional Legal-RAG Assistant (RAG MVP)

Prototype of a legal assistant based on **Retrieval-Augmented Generation (RAG)** designed to query, cross-reference, and cite traffic, mobility, and transportation regulations across three jurisdiction levels in Mexico: **Municipal (Cuernavaca), State (Morelos), and Federal (Highways and Bridges)**.

**Test the Agent Live here [Dify Web App](https://udify.app/chat/4DLVIDv2ZFbZYAgA) (Requires Google AI API activation to work)**

## Project Objective

This project was born as a practical exercise in data engineering and LLM orchestration (developed in a 2.5-day sprint) to explore the real challenges behind automated legal assistance tools, such as exact source traceability, hallucination mitigation, and the segmentation of extensive legal corpora.

**Note on Development and AI Assistance**

This ETL pipeline was not written line by line in a traditional manual way; it was designed and orchestrated under an AI-Assisted Engineering approach. Using large language models as development copilots, human authorship focused on what was truly critical: architecture design, definition of business rules (Data Hygiene), edge case validation in legal documents, and quality control of the resulting data (Ground Truth Validation). AI accelerated syntax synthesis; strategy and legal logic were one hundred percent custom-designed.

## Architecture and Tech Stack

* **RAG Workflow Orchestration:** [Dify](https://dify.ai/) (Visual chatflow).

* **Documentary ETL & Preprocessing:** Python (`pypdf`, `re`) for institutional noise cleaning and hierarchical structuring.

* **Language Model (LLM):** Google Gemini Flash family (via Google AI Studio API - *BYOK* scheme).

* **Segmentation Strategy:** Custom *Context-Enriched Chunking* using explicit delimiters (`===CHUNK===`).

### Integrated Regulatory Corpus

1. **Municipal Level:** Traffic and Roadway Regulations of the Municipality of Cuernavaca, Morelos (`159 chunks`).
   ​2. **State Level:** Mobility, Transportation and Road Safety Law of the State of Morelos (`284 chunks`).

2. **Federal Level:** Traffic Regulations on Federal Jurisdiction Highways and Bridges (`302 chunks`).

## Technical Challenges, Obstacles, and Usage Considerations

During the development and stress testing (*QA*) of the assistant, we faced critical challenges inherent to legal document indexing. It is essential to keep the following points in mind to understand the tool's behavior:

### 1. The Challenge of Semantics and Legal Vocabulary

One of the biggest obstacles in RAG systems applied to law is the discrepancy between the **user's colloquial language** and the **strict terminology of the laws**.

* **The problem:** Queries formulated with everyday or imprecise terms (for example, referring colloquially to an infraction or vehicle type without its official technical denomination) can trigger false negatives or null responses, since the vector search engine calculates direct mathematical similarities.

* **Usage recommendation:** Quality, precision, and result optimization depend directly on the semantics and terms used in the query. Drafting questions using related or complementary legal concepts greatly helps the agent retrieve the correct article.

### 2. Prevention of False Negatives against Negative Questions or Prohibitions

Laws and regulations do not operate under absolute prohibitions for all cases, but rather through regulatory frameworks, rights habilitations, or exceptions (for example, the regulation of vulnerable groups or special permits).

* **The problem:** Queries formulated in a negative sense (e.g., inquiring about non-existent prohibitions) tend to confuse traditional models oriented toward strict literalness, leading them to respond prematurely that "there is no information."

* **Applied solution:** System rules and hyperparameters were calibrated to interpret the underlying normative intent and avoid blocks due to false legal gaps.

### 3. Mitigation of "Orphan Chunks"

When indexing extensive legal documents using generic line breaks, clauses (`I, II...`) and sub-clauses were separated from their article header, losing context.

* **Solution:** A Python ETL pipeline was implemented to clean institutional noise (official gazettes, stamps, and pagination) and dynamically inject hierarchy metadata into each block (`[Source | Title | Chapter | Article]`).

## Current Limitations and Future Work (Roadmap)

* **Hybrid Reranking Implementation:** Integrate a *Cross-Encoder Reranking* model to refine the relevance order of retrieved chunks.

* **Query Expansion Layer:** Incorporate an intermediate query rewriting node that automatically translates citizen slang into legal terminology before vector search.

## 📂 Repository Content

* `/data/processed/`: Cleaned and metadata-enriched `.txt` files ready for vectorization.

* `/scripts/`: Python code used for processing and cleaning the laws.

* `/prompts/`: Iterations and final version of the *System Prompt*.
