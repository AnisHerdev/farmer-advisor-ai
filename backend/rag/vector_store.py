"""
ChromaDB Vector Store and Retriever for Farmer Advisory RAG Pipeline.
Indexes curated ICAR/agricultural advisories and provides dense/semantic retrieval.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("farmer_advisor.rag")

class AdvisoryKnowledgeBase:
    """Manages document ingestion, chunking, and ChromaDB retrieval."""

    def __init__(
        self,
        docs_dir: str = "data/advisories",
        persist_dir: str = "data/chroma",
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        self.docs_dir = docs_dir
        self.persist_dir = persist_dir
        self.embedding_model_name = embedding_model_name
        self.documents: List[Dict[str, Any]] = []
        self.chroma_client = None
        self.collection = None
        self.embedding_function = None

        self._load_local_documents()
        self._initialize_vector_store()

    def _load_local_documents(self):
        """Loads and formats structured agricultural advisory documents."""
        if not os.path.exists(self.docs_dir):
            logger.warning(f"Advisory docs directory not found: {self.docs_dir}")
            return

        for fname in os.listdir(self.docs_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.docs_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        records = json.load(f)
                        if isinstance(records, list):
                            for item in records:
                                formatted_chunk = self._format_record_to_chunk(item, fname)
                                if formatted_chunk:
                                    self.documents.append(formatted_chunk)
                except Exception as e:
                    logger.error(f"Error loading {fpath}: {e}")

        logger.info(f"Loaded {len(self.documents)} agricultural advisory chunks from {self.docs_dir}.")

    def _format_record_to_chunk(self, item: Dict[str, Any], source_file: str) -> Optional[Dict[str, Any]]:
        """Converts raw json records into rich semantic text chunks with metadata."""
        item_id = item.get("id", "GEN_01")
        crop = item.get("crop", item.get("region", "General Agriculture"))
        source = item.get("source", "ICAR Extension Advisory")
        
        # Build comprehensive searchable text representation
        lines = [f"Crop / Subject: {crop}"]
        
        if "crop_category" in item:
            lines.append(f"Category: {item['crop_category']}")
        if "season" in item:
            lines.append(f"Season: {item['season']}")
        if "sowing_window" in item:
            lines.append(f"Sowing Window & Months: {item['sowing_window']}")
        if "regions" in item:
            regions_str = ", ".join(item['regions']) if isinstance(item['regions'], list) else str(item['regions'])
            lines.append(f"Target States/Regions: {regions_str}")
        if "soil_requirement" in item:
            lines.append(f"Soil & Seed Preparation: {item['soil_requirement']}")
        if "seed_rate" in item:
            lines.append(f"Seed Rate: {item['seed_rate']}")
        if "spacing" in item:
            lines.append(f"Plant Spacing: {item['spacing']}")
        if "key_advisory" in item:
            lines.append(f"Key Sowing Advisory: {item['key_advisory']}")
            
        # Fertilizer fields
        if "recommended_npk_ratio" in item:
            lines.append(f"Recommended NPK Ratio: {item['recommended_npk_ratio']}")
        if "basal_dose" in item:
            lines.append(f"Basal Fertilizer Dose: {item['basal_dose']}")
        if "top_dressing_splits" in item:
            splits = item["top_dressing_splits"]
            split_text = "; ".join([f"{s.get('timing')}: {s.get('nutrient')}" for s in splits])
            lines.append(f"Top Dressing Splits: {split_text}")
        if "micronutrients_and_organic" in item:
            lines.append(f"Micronutrients & Organics: {item['micronutrients_and_organic']}")
        if "key_warning" in item:
            lines.append(f"Agronomic Caution / Warning: {item['key_warning']}")

        # Irrigation fields
        if "total_water_requirement" in item:
            lines.append(f"Total Water Requirement: {item['total_water_requirement']}")
        if "critical_stages_order_of_importance" in item:
            stages = item["critical_stages_order_of_importance"]
            stages_text = " | ".join([f"{s.get('stage')} ({s.get('timing_das')}): {s.get('priority')}" for s in stages])
            lines.append(f"Critical Irrigation Stages: {stages_text}")
        if "contingency_limited_water" in item:
            lines.append(f"Contingency for Limited Water: {item['contingency_limited_water']}")
        if "drip_irrigation_guideline" in item:
            lines.append(f"Drip Irrigation Practice: {item['drip_irrigation_guideline']}")

        # Pest / Disease fields
        if "pest_disease" in item:
            lines.append(f"Target Pest / Disease: {item['pest_disease']}")
        if "symptoms" in item:
            lines.append(f"Symptoms & Field Diagnosis: {item['symptoms']}")
        if "integrated_pest_management_ipm" in item:
            ipm = item["integrated_pest_management_ipm"]
            ipm_text = " ".join(ipm) if isinstance(ipm, list) else str(ipm)
            lines.append(f"Integrated Pest Management (IPM): {ipm_text}")
        if "economic_threshold_level_etl" in item:
            lines.append(f"Economic Threshold Level (ETL): {item['economic_threshold_level_etl']}")

        # Regional guidelines
        if "key_directives" in item:
            dirs = " ".join(item["key_directives"]) if isinstance(item["key_directives"], list) else str(item["key_directives"])
            lines.append(f"State Policy & Extension Directives: {dirs}")

        lines.append(f"Official Authority: {source}")
        
        full_text = "\n".join(lines)
        return {
            "id": item_id,
            "crop": str(crop),
            "source_file": source_file,
            "source": source,
            "text": full_text,
            "metadata": {
                "id": item_id,
                "crop": str(crop),
                "source": source,
                "file": source_file
            }
        }

    def _initialize_vector_store(self):
        """Initializes ChromaDB with persistent storage and embeds documents."""
        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(self.persist_dir, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)

            # Check or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="indian_farmer_advisories",
                metadata={"description": "ICAR and State Agricultural Advisories"}
            )

            # Ingest if collection is empty
            if self.collection.count() == 0 and self.documents:
                logger.info(f"Indexing {len(self.documents)} documents into ChromaDB collection...")
                ids = [doc["id"] for doc in self.documents]
                texts = [doc["text"] for doc in self.documents]
                metadatas = [doc["metadata"] for doc in self.documents]

                # ChromaDB handles default sentence-transformers or text embeddings
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
                logger.info("ChromaDB indexing complete.")
            else:
                logger.info(f"ChromaDB ready with {self.collection.count()} indexed documents.")

        except Exception as e:
            logger.warning(f"ChromaDB persistent initialization note (falling back to memory retriever if needed): {e}")

    def retrieve(self, query: str, top_k: int = 3, crop_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining ChromaDB dense semantic vector search
        with domain entity awareness (Crop & Agronomic Topic boosting).
        """
        # 1. Detect target crop entity if present in query
        detected_crop = crop_filter
        if not detected_crop:
            known_crops = [
                ("cotton", "Cotton"), ("jute", "Jute"), ("patson", "Jute"),
                ("tomato", "Tomato"), ("tamatar", "Tomato"),
                ("wheat", "Wheat"), ("gehun", "Wheat"),
                ("paddy", "Paddy / Rice"), ("rice", "Paddy / Rice"), ("dhan", "Paddy / Rice"),
                ("mustard", "Mustard / Rapeseed"), ("sarson", "Mustard / Rapeseed"),
                ("chickpea", "Chickpea / Bengal Gram"), ("gram", "Chickpea / Bengal Gram"), ("chana", "Chickpea / Bengal Gram"),
                ("onion", "Onion"), ("pyaz", "Onion")
            ]
            q_lower = query.lower()
            for kw, canon in known_crops:
                if kw in q_lower:
                    detected_crop = canon
                    break

        results = []

        if self.collection:
            try:
                # Query ChromaDB with semantic search
                n_res = min(10, max(1, self.collection.count()))
                query_response = self.collection.query(
                    query_texts=[query],
                    n_results=n_res
                )

                if query_response and query_response.get("documents") and query_response["documents"][0]:
                    docs = query_response["documents"][0]
                    metas = query_response["metadatas"][0]
                    distances = query_response.get("distances", [[0.0] * len(docs)])[0]

                    scored_candidates = []
                    for doc_text, meta, dist in zip(docs, metas, distances):
                        # Semantic similarity score from distance
                        sem_score = max(0.1, min(1.0, 1.0 / (1.0 + float(dist))))
                        doc_crop = meta.get("crop", "")
                        
                        # Hybrid entity boost: +0.40 if matching detected crop
                        entity_boost = 0.0
                        if detected_crop and detected_crop.lower() in doc_crop.lower():
                            entity_boost = 0.40
                        elif detected_crop and detected_crop.lower() not in doc_crop.lower():
                            entity_boost = -0.30

                        final_score = sem_score + entity_boost
                        scored_candidates.append((final_score, sem_score, meta, doc_text))

                    # Sort by final hybrid score
                    scored_candidates.sort(key=lambda x: x[0], reverse=True)

                    for final_score, sem_score, meta, doc_text in scored_candidates[:top_k]:
                        confidence = min(0.98, max(0.50, round(sem_score + 0.1, 2)))
                        doc_source = meta.get("source")
                        doc_title = meta.get("doc_title")
                        source_label = f"{doc_source} — {doc_title}" if doc_title and doc_source else (doc_title or doc_source or "ICAR Official Advisory Manual")
                        results.append({
                            "id": meta.get("id"),
                            "crop": meta.get("crop"),
                            "source": source_label,
                            "text": doc_text,
                            "confidence": confidence
                        })
                    return results
            except Exception as e:
                logger.warning(f"ChromaDB query exception, falling back to lexical retriever: {e}")

        # In-memory keyword & lexical fallback retriever
        query_words = set(query.lower().split())
        scored_docs = []

        for doc in self.documents:
            doc_lower = doc["text"].lower()
            score = 0
            for word in query_words:
                if len(word) > 2 and word in doc_lower:
                    score += 2
            if detected_crop and detected_crop.lower() in doc["crop"].lower():
                score += 10
            elif doc["crop"].lower() in query.lower():
                score += 5

            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        for score, doc in scored_docs[:top_k]:
            results.append({
                "id": doc["id"],
                "crop": doc["crop"],
                "source": doc["source"],
                "text": doc["text"],
                "confidence": round(min(0.95, 0.70 + score * 0.03), 3)
            })

        return results
