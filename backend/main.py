"""
FastAPI Backend for AI Farmer Advisory Assistant.
Integrates BharatGen AgriParam, AI4Bharat IndicTrans2, and ChromaDB RAG.
"""

import os
import time
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from backend.rag.vector_store import AdvisoryKnowledgeBase
from backend.models.indic_translator import IndicTransEngine, INDIC_LANG_NAMES
from backend.models.agriparam_engine import AgriParamEngine

# Load environment configuration
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("farmer_advisor.api")

app = FastAPI(
    title="AI Farmer Advisory Assistant API",
    description="Multilingual Sovereign Agronomic Advisory powered by BharatGen AgriParam & AI4Bharat IndicTrans2 with ICAR Groundedness",
    version="1.0.0"
)

# Enable CORS for React Vite frontend
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Pipelines
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "demo")
HF_TOKEN = os.getenv("HF_TOKEN", "")

logger.info(f"Initializing Farmer Advisory Backend (Default Mode: {EXECUTION_MODE})...")

knowledge_base = AdvisoryKnowledgeBase(
    docs_dir=os.getenv("ADVISORY_DOCS_DIRECTORY", "data/advisories"),
    persist_dir=os.getenv("CHROMA_PERSIST_DIRECTORY", "data/chroma")
)

translator = IndicTransEngine(use_local_weights=(EXECUTION_MODE == "local_agriparam"))

agriparam_engine = AgriParamEngine(
    model_id=os.getenv("AGRIPARAM_MODEL_ID", "bharatgenai/AgriParam"),
    execution_mode=EXECUTION_MODE,
    hf_token=HF_TOKEN
)

# Pydantic Schemas
class AdvisoryRequest(BaseModel):
    query: str = Field(..., description="Farmer question in Indian language or English", min_length=2)
    language: str = Field("hi", description="Language code: hi, te, ta, kn, mr, pa, en")
    crop_filter: Optional[str] = Field(None, description="Optional crop filter, e.g. Cotton, Wheat, Tomato, Jute")
    mode: Optional[str] = Field(None, description="'demo' for instant response or 'local_agriparam' for local transformer")

class SourceCitation(BaseModel):
    id: Optional[str]
    crop: Optional[str]
    source: str
    text_snippet: str
    confidence: float

class AdvisoryResponse(BaseModel):
    query: str
    language: str
    language_display: str
    translated_query_en: str
    advisory: str
    advisory_english: str
    action_plan: List[str]
    groundedness_score: float
    sources: List[SourceCitation]
    model_engine: str
    latency_ms: float

@app.get("/api/health")
def health_check():
    """Health and status check of sovereign model components."""
    return {
        "status": "online",
        "service": "AI Farmer Advisory Assistant",
        "execution_mode": agriparam_engine.execution_mode,
        "indexed_documents_count": len(knowledge_base.documents),
        "models": {
            "domain_llm": os.getenv("AGRIPARAM_MODEL_ID", "bharatgenai/AgriParam"),
            "translation_nmt": "AI4Bharat IndicTrans2 (dist-200M)",
            "vector_store": "ChromaDB Persistent (data/chroma)",
            "embeddings": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        },
        "supported_languages": list(INDIC_LANG_NAMES.keys())
    }

@app.get("/api/languages")
def get_supported_languages():
    """Returns supported Indian languages with BCP47 tags for Speech Recognition/TTS."""
    return [
        {
            "code": code,
            "name": meta["name"],
            "native": meta["native"],
            "bcp47": meta["bcp47"]
        }
        for code, meta in INDIC_LANG_NAMES.items()
    ]

@app.get("/api/quick-prompts")
def get_quick_prompts(lang: str = Query("hi")):
    """Returns 4 curated agricultural prompts in the selected language for instant farmer action."""
    prompts_by_lang = {
        "en": [
            {"crop": "Cotton", "title": "Cotton Sowing Window", "query": "What month to what month should I sow Cotton in Maharashtra?"},
            {"crop": "Wheat", "title": "Wheat Irrigation Stage", "query": "When is the critical first irrigation (CRI stage) for Wheat?"},
            {"crop": "Tomato", "title": "Tomato NPK Schedule", "query": "What is the recommended fertilizer dose and spray for Tomato?"},
            {"crop": "Jute", "title": "Jute Sowing & Soil", "query": "What is the ideal sowing month and soil for Jute in West Bengal?"}
        ],
        "hi": [
            {"crop": "कपास", "title": "कपास बुवाई का समय", "query": "महाराष्ट्र में कपास की बुवाई किस महीने से किस महीने तक करनी चाहिए?"},
            {"crop": "गेहूं", "title": "गेहूं में पहली सिंचाई (CRI)", "query": "गेहूं में ताज जड़ (CRI अवस्था) पर पहली सिंचाई कब करनी चाहिए?"},
            {"crop": "टमाटर", "title": "टमाटर खाद (NPK) अनुसूची", "query": "टमाटर की फसल में कौन सा खाद और बेसल डोज डालना चाहिए?"},
            {"crop": "पटसन / जूट", "title": "जूट की बुवाई और मिट्टी", "query": "पश्चिम बंगाल में जूट बोने का सही महीना और मिट्टी कौन सी है?"}
        ],
        "te": [
            {"crop": "పత్తి", "title": "పత్తి విత్తే సమయం", "query": "మహారాష్ట్ర మరియు తెలంగాణలో పత్తి విత్తడానికి సరైన నెల ఏది?"},
            {"crop": "గోధుమ", "title": "గోధుమ మొదటి నీటిపారుదల", "query": "గోధుమ పంటలో కిరీటం వేరు దశ (CRI) లో మొదటి నీరు ఎప్పుడు ఇవ్వాలి?"},
            {"crop": "టమోటా", "title": "టమోటా ఎరువుల మోతాదు", "query": "టమోటా పంటకు సిఫార్సు చేసిన ఎరువుల మోతాదు మరియు పోషకాలు ఏమిటి?"},
            {"crop": "జనపనార", "title": "జనపనార విత్తే కాలం", "query": "పశ్చిమ బెంగాల్‌లో జనపనార విత్తే సరైన నెల ఏది?"}
        ],
        "ta": [
            {"crop": "பருத்தி", "title": "பருத்தி விதைப்பு காலம்", "query": "பருத்தி விதைப்பதற்கு ஏற்ற மாதம் எது?"},
            {"crop": "கோதுமை", "title": "கோதுமை முதல் பாசனம்", "query": "கோதுமை பயிரில் முதல் பாசனம் எப்போது செய்ய வேண்டும்?"},
            {"crop": "தக்காளி", "title": "தக்காளி உர மேலாண்மை", "query": "தக்காளி பயிருக்கு தேவையான உர அளவு மற்றும் பாதுகாப்பு என்ன?"},
            {"crop": "சணல்", "title": "சணல் விதைப்பு வழிகாட்டுதல்", "query": "சணல் சாகுபடிக்கு உகந்த மாதம் மற்றும் மண் எது?"}
        ],
        "kn": [
            {"crop": "ಹತ್ತಿ", "title": "ಹತ್ತಿ ಬಿತ್ತನೆ ಸಮಯ", "query": "ಹತ್ತಿ ಬೆಳೆಯನ್ನು ಯಾವ ತಿಂಗಳಲ್ಲಿ ಬಿತ್ತನೆ ಮಾಡಬೇಕು?"},
            {"crop": "ಗೋಧಿ", "title": "ಗೋಧಿ ಮೊದಲ ನೀರಾವರಿ", "query": "ಗೋಧಿ ಬೆಳೆಗೆ ಮೊದಲ ನೀರಾವರಿ (CRI ಹಂತ) ಯಾವಾಗ ನೀಡಬೇಕು?"},
            {"crop": "ಟೊಮೆಟೊ", "title": "ಟೊಮೆಟೊ ಗೊಬ್ಬರ ವೇಳಾಪಟ್ಟಿ", "query": "ಟೊಮೆಟೊ ಬೆಳೆಗೆ ಶಿಫಾರಸು ಮಾಡಿದ ರಸಗೊಬ್ಬರ ಪ್ರಮಾಣ ಎಷ್ಟು?"},
            {"crop": "ಸೆಣಬು", "title": "ಸೆಣಬು ಬಿತ್ತನೆ ಮಾರ್ಗದರ್ಶಿ", "query": "ಸೆಣಬು ಬಿತ್ತನೆ ಮಾಡಲು ಸೂಕ್ತವಾದ ತಿಂಗಳು ಯಾವುದು?"}
        ],
        "mr": [
            {"crop": "कापूस", "title": "कापूस पेरणीची योग्य वेळ", "query": "महाराष्ट्रात कापूस पेरणी कोणत्या महिन्यात करावी?"},
            {"crop": "गहू", "title": "गव्हाचे पहिले पाणी (CRI)", "query": "गव्हाला मुकुट मुळे फुटण्याच्या अवस्थेत (CRI) पाणी कधी द्यावे?"},
            {"crop": "टोमॅटो", "title": "टोमॅटो खत व्यवस्थापन", "query": "टोमॅटो पिकासाठी खताचे प्रमाण आणि बेसल डोस काय आहे?"},
            {"crop": "ताग", "title": "ताग पेरणी आणि माती", "query": "ताग लागवडीसाठी योग्य महिना आणि माती कोणती आहे?"}
        ],
        "pa": [
            {"crop": "ਕਪਾਹ", "title": "ਨਰਮੇ ਦੀ ਬਿਜਾਈ ਦਾ ਸਮਾਂ", "query": "ਕਪਾਹ ਦੀ ਬਿਜਾਈ ਕਿਸ ਮਹੀਨੇ ਵਿੱਚ ਕਰਨੀ ਚਾਹੀਦੀ ਹੈ?"},
            {"crop": "ਕਣਕ", "title": "ਕਣਕ ਦਾ ਪਹਿਲਾ ਪਾਣੀ (CRI)", "query": "ਕਣਕ ਨੂੰ ਪਹਿਲਾ ਪਾਣੀ ਕਦੋਂ ਲਾਉਣਾ ਚਾਹੀਦਾ ਹੈ?"},
            {"crop": "ਟਮਾਟਰ", "title": "ਟਮਾਟਰ ਖਾਦ ਪ੍ਰਬੰਧਨ", "query": "ਟਮਾਟਰ ਦੀ ਫਸਲ ਲਈ ਖਾਦ ਦੀ ਕਿੰਨੀ ਮਾਤਰਾ ਚਾਹੀਦੀ ਹੈ?"},
            {"crop": "ਪਟਸਨ", "title": "ਪਟਸਨ ਦੀ ਬਿਜਾਈ", "query": "ਪਟਸਨ ਬੀਜਣ ਲਈ ਸਹੀ ਮਹੀਨਾ ਅਤੇ ਮਿੱਟੀ ਕਿਹੜੀ ਹੈ?"}
        ]
    }
    return prompts_by_lang.get(lang, prompts_by_lang["en"])

@app.post("/api/advisory", response_model=AdvisoryResponse)
def get_farmer_advisory(req: AdvisoryRequest):
    """
    Main agronomic advisory endpoint.
    Retrieves ICAR documents, runs AgriParam generation, and localizes via IndicTrans2.
    """
    start_time = time.time()
    user_lang = req.language.lower()
    if user_lang not in INDIC_LANG_NAMES:
        user_lang = "en"

    # 1. Indic to English Query Translation (AI4Bharat IndicTrans2)
    translated_query = translator.translate_indic_to_en(req.query, src_lang=user_lang)
    logger.info(f"Query [{user_lang}]: '{req.query}' -> English: '{translated_query}'")

    # 2. ChromaDB RAG Vector Retrieval
    retrieved_docs = knowledge_base.retrieve(
        query=translated_query,
        top_k=3,
        crop_filter=req.crop_filter
    )

    # 3. Domain LLM Generation (BharatGen AgriParam)
    if req.mode:
        agriparam_engine.execution_mode = req.mode

    generation_result = agriparam_engine.generate_advisory(
        query=translated_query,
        retrieved_contexts=retrieved_docs,
        target_lang="en"
    )

    raw_advisory_en = generation_result["advisory_text"]
    action_plan_en = generation_result["action_plan"]

    # 4. English to Indic Response Translation (AI4Bharat IndicTrans2)
    if user_lang != "en":
        localized_advisory = translator.translate_en_to_indic(raw_advisory_en, tgt_lang=user_lang)
        localized_action_plan = [translator.translate_en_to_indic(step, tgt_lang=user_lang) for step in action_plan_en]
    else:
        localized_advisory = raw_advisory_en
        localized_action_plan = action_plan_en

    # 5. Format sources
    source_citations = [
        SourceCitation(
            id=doc.get("id"),
            crop=doc.get("crop"),
            source=doc.get("source", "ICAR Package of Practices"),
            text_snippet=doc.get("text", "")[:280] + "...",
            confidence=doc.get("confidence", 0.85)
        )
        for doc in retrieved_docs
    ]

    latency_ms = round((time.time() - start_time) * 1000, 2)
    lang_info = INDIC_LANG_NAMES.get(user_lang, {"name": "English", "native": "English"})

    return AdvisoryResponse(
        query=req.query,
        language=user_lang,
        language_display=f"{lang_info['native']} ({lang_info['name']})",
        translated_query_en=translated_query,
        advisory=localized_advisory,
        advisory_english=raw_advisory_en,
        action_plan=localized_action_plan,
        groundedness_score=generation_result["groundedness_score"],
        sources=source_citations,
        model_engine=generation_result["model_engine"],
        latency_ms=latency_ms
    )
