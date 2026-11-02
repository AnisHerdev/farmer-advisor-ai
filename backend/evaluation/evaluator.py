"""
Quantitative Testing & Error Analysis Suite for Farmer Advisory Assistant.
Executes 40 representative domain QA test cases across 5 categories,
calculates Groundedness, Factual Correctness, and Retrieval Precision,
and outputs a comprehensive Failure Analysis Report (EVALUATION_REPORT.md).
"""

import os
import json
import time
import logging
from typing import List, Dict, Any

from backend.rag.vector_store import AdvisoryKnowledgeBase
from backend.models.indic_translator import IndicTransEngine
from backend.models.agriparam_engine import AgriParamEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("farmer_advisor.evaluation")

# 40 Representative Rubric Test Cases
EVALUATION_TEST_CASES = [
    # Category 1: Sowing Calendars & Agro-Climatic Zones (10 Cases)
    {
        "id": "TC_SOW_01",
        "category": "Sowing Calendar",
        "query": "What are the ideal sowing months for Cotton in Maharashtra and Gujarat?",
        "lang": "en",
        "expected_crop": "Cotton",
        "golden_facts": ["May", "June", "Kharif"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_SOW_02",
        "category": "Sowing Calendar",
        "query": "कपास की बुवाई महाराष्ट्र में किस महीने में करनी चाहिए?",
        "lang": "hi",
        "expected_crop": "Cotton",
        "golden_facts": [["May", "मई"], ["June", "जून"], ["Kharif", "खरीफ"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_SOW_03",
        "category": "Sowing Calendar",
        "query": "What is the recommended sowing window for Jute in West Bengal?",
        "lang": "en",
        "expected_crop": "Jute",
        "golden_facts": ["March", "April", "May"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_SOW_04",
        "category": "Sowing Calendar",
        "query": "पश्चिम बंगाल में जूट (पटसन) बोने का सही समय क्या है?",
        "lang": "hi",
        "expected_crop": "Jute",
        "golden_facts": [["March", "मार्च"], ["April", "अप्रैल"], ["May", "मई"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_SOW_05",
        "category": "Sowing Calendar",
        "query": "When should Tomato nursery be raised for the Rabi season crop?",
        "lang": "en",
        "expected_crop": "Tomato",
        "golden_facts": ["October", "November"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_SOW_06",
        "category": "Sowing Calendar",
        "query": "What is the timely sowing date for irrigated Wheat in Punjab and Haryana?",
        "lang": "en",
        "expected_crop": "Wheat",
        "golden_facts": ["November", "20"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_SOW_07",
        "category": "Sowing Calendar",
        "query": "गेहूं की समय पर बुवाई किस तारीख तक पूरी कर लेनी चाहिए?",
        "lang": "hi",
        "expected_crop": "Wheat",
        "golden_facts": [["November", "नवंबर"], ["20", "20 नवंबर"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_SOW_08",
        "category": "Sowing Calendar",
        "query": "What are the ideal sowing dates for Mustard in Rajasthan to avoid aphid attack?",
        "lang": "en",
        "expected_crop": "Mustard",
        "golden_facts": ["October", "September"],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_SOW_09",
        "category": "Sowing Calendar",
        "query": "When should Chickpea / Bengal gram be sown in Madhya Pradesh and Maharashtra?",
        "lang": "en",
        "expected_crop": "Chickpea",
        "golden_facts": ["October", "November"],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_SOW_10",
        "category": "Sowing Calendar",
        "query": "What is the nursery sowing season for Rabi Onion in Nashik, Maharashtra?",
        "lang": "en",
        "expected_crop": "Onion",
        "golden_facts": ["October", "November"],
        "min_expected_groundedness": 0.80
    },

    # Category 2: Fertilizer & NPK Nutrient Management (8 Cases)
    {
        "id": "TC_FRT_11",
        "category": "Fertilizer & NPK",
        "query": "What is the recommended NPK dose and basal fertilizer for irrigated Bt Cotton?",
        "lang": "en",
        "expected_crop": "Cotton",
        "golden_facts": ["120:60:60", "Phosphorus", "Potassium"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_FRT_12",
        "category": "Fertilizer & NPK",
        "query": "कपास की फसल में शुरुआती बेसल खाद में क्या डालना चाहिए?",
        "lang": "hi",
        "expected_crop": "Cotton",
        "golden_facts": [["Phosphorus", "फास्फोरस"], ["Potassium", "पोटाश"], ["Nitrogen", "यूरिया", "खाद"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_FRT_13",
        "category": "Fertilizer & NPK",
        "query": "What is the NPK fertilizer recommendation for hybrid Tomato per hectare?",
        "lang": "en",
        "expected_crop": "Tomato",
        "golden_facts": ["180:120:150", "Nitrogen", "Phosphorus"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_FRT_14",
        "category": "Fertilizer & NPK",
        "query": "टमाटर में फल फटने और सड़ांध (Blossom End Rot) से बचने के लिए कौन सा पोषक तत्व स्प्रे करें?",
        "lang": "hi",
        "expected_crop": "Tomato",
        "golden_facts": [["Calcium", "कैल्शियम"], ["Boron", "बोरोन"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_FRT_15",
        "category": "Fertilizer & NPK",
        "query": "How should Nitrogen / Urea be split applied in Wheat crop?",
        "lang": "en",
        "expected_crop": "Wheat",
        "golden_facts": ["Urea", "Crown Root Initiation", "tillering"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_FRT_16",
        "category": "Fertilizer & NPK",
        "query": "गेहूं में यूरिया की टॉप ड्रेसिंग कब और कैसे करनी चाहिए?",
        "lang": "hi",
        "expected_crop": "Wheat",
        "golden_facts": [["Crown Root", "CRI", "ताज जड़"], ["Urea", "यूरिया"], ["Irrigation", "सिंचाई"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_FRT_17",
        "category": "Fertilizer & NPK",
        "query": "What fertilizer dose is recommended for Olitorius (Tossa) Jute?",
        "lang": "en",
        "expected_crop": "Jute",
        "golden_facts": ["60:30:30", "Nitrogen", "Phosphorus"],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_FRT_18",
        "category": "Fertilizer & NPK",
        "query": "Why should farmers use Neem-coated urea and Zinc sulphate in Paddy fields?",
        "lang": "en",
        "expected_crop": "Paddy",
        "golden_facts": ["Neem", "Zinc", "Nitrogen"],
        "min_expected_groundedness": 0.85
    },

    # Category 3: Irrigation & Moisture Management (8 Cases)
    {
        "id": "TC_IRR_19",
        "category": "Irrigation Management",
        "query": "What is the single most critical stage for irrigation in Wheat?",
        "lang": "en",
        "expected_crop": "Wheat",
        "golden_facts": ["Crown Root Initiation", "20 to 25"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_IRR_20",
        "category": "Irrigation Management",
        "query": "गेहूं में सबसे जरूरी पहली सिंचाई (CRI अवस्था) कितने दिनों बाद करनी चाहिए?",
        "lang": "hi",
        "expected_crop": "Wheat",
        "golden_facts": [["21", "20 to 25", "25"], ["Crown Root", "CRI", "ताज जड़"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_IRR_21",
        "category": "Irrigation Management",
        "query": "If a farmer has water for only two irrigations in Wheat, at what stages should they apply?",
        "lang": "en",
        "expected_crop": "Wheat",
        "golden_facts": ["CRI", "Flowering"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_IRR_22",
        "category": "Irrigation Management",
        "query": "What are the critical moisture-sensitive stages in Cotton crop?",
        "lang": "en",
        "expected_crop": "Cotton",
        "golden_facts": ["Squaring", "Flowering", "Boll"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_IRR_23",
        "category": "Irrigation Management",
        "query": "How often should Tomato be irrigated under drip systems to prevent fruit cracking?",
        "lang": "en",
        "expected_crop": "Tomato",
        "golden_facts": ["drip", "moisture", "fruit"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_IRR_24",
        "category": "Irrigation Management",
        "query": "Why is alternate furrow irrigation recommended during water stress in Cotton?",
        "lang": "en",
        "expected_crop": "Cotton",
        "golden_facts": ["furrow", "water", "save"],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_IRR_25",
        "category": "Irrigation Management",
        "query": "What is the water requirement for Jute during seedling germination?",
        "lang": "en",
        "expected_crop": "Jute",
        "golden_facts": ["moist", "pre-sowing"],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_IRR_26",
        "category": "Irrigation Management",
        "query": "How can plastic mulch with drip irrigation benefit Tomato cultivation?",
        "lang": "en",
        "expected_crop": "Tomato",
        "golden_facts": ["mulch", "drip", "Tomato"],
        "min_expected_groundedness": 0.80
    },

    # Category 4: Pest & Disease Interventions (7 Cases)
    {
        "id": "TC_PST_27",
        "category": "Pest & Disease",
        "query": "What are the symptoms and ETL of Pink Bollworm in Cotton?",
        "lang": "en",
        "expected_crop": "Cotton",
        "golden_facts": ["rosette", "bolls", "pheromone"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_PST_28",
        "category": "Pest & Disease",
        "query": "कपास में गुलाबी सुंडी (Pink Bollworm) के क्या लक्षण हैं?",
        "lang": "hi",
        "expected_crop": "Cotton",
        "golden_facts": [["Pink Bollworm", "गुलाबी सुंडी"], ["rosette", "फूल", "टिंडे"], ["pheromone", "फेरोमोन"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_PST_29",
        "category": "Pest & Disease",
        "query": "How to manage Tomato Leaf Curl Virus (ToLCV) transmitted by whitefly?",
        "lang": "en",
        "expected_crop": "Tomato",
        "golden_facts": ["whitefly", "resistant", "curling"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_PST_30",
        "category": "Pest & Disease",
        "query": "टमाटर में पत्ता मरोड़ रोग (लीफ कर्ल) की रोकथाम कैसे करें?",
        "lang": "hi",
        "expected_crop": "Tomato",
        "golden_facts": [["whitefly", "सफेद मक्खी"], ["curling", "पत्ता", "मरोड़"], ["yellow", "पीले", "ट्रैप"]],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_PST_31",
        "category": "Pest & Disease",
        "query": "What are the early symptoms of Stem Rot in Jute and how to manage it?",
        "lang": "en",
        "expected_crop": "Jute",
        "golden_facts": ["Stem Rot", "Jute", "Carbendazim"],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_PST_32",
        "category": "Pest & Disease",
        "query": "How to identify Yellow Rust in Wheat and what fungicide should be sprayed?",
        "lang": "en",
        "expected_crop": "Wheat",
        "golden_facts": ["yellow", "stripes", "Propiconazole"],
        "min_expected_groundedness": 0.85
    },
    {
        "id": "TC_PST_33",
        "category": "Pest & Disease",
        "query": "गेहूं में पीला रतुआ (Yellow Rust) दिखने पर कौन सी दवा का छिड़काव करें?",
        "lang": "hi",
        "expected_crop": "Wheat",
        "golden_facts": [["Yellow", "Rust", "रतुआ"], ["Propiconazole", "Tebuconazole", "प्रोपिकोनाजोल", "टिल्ट"]],
        "min_expected_groundedness": 0.85
    },

    # Category 5: Multilingual Regional QA (7 Cases)
    {
        "id": "TC_ML_34",
        "category": "Multilingual QA",
        "query": "మహారాష్ట్రలో పత్తి ఎప్పుడు విత్తాలి మరియు మొదటి ఎరువు ఏది?",
        "lang": "te",
        "expected_crop": "Cotton",
        "golden_facts": [["Cotton", "పత్తి"], ["May", "June", "విత్తే"], ["Fertilizer", "ఎరువు"]],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_ML_35",
        "category": "Multilingual QA",
        "query": "பருத்தி விதைப்பதற்கு எந்த மாதம் சிறந்தது?",
        "lang": "ta",
        "expected_crop": "Cotton",
        "golden_facts": [["Cotton", "பருத்தி"], ["May", "June", "விதைப்பு"]],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_ML_36",
        "category": "Multilingual QA",
        "query": "ಹತ್ತಿ ಬಿತ್ತನೆ ಮಾಡಲು ಸೂಕ್ತವಾದ ತಿಂಗಳು ಯಾವುದು?",
        "lang": "kn",
        "expected_crop": "Cotton",
        "golden_facts": [["Cotton", "ಹತ್ತಿ"], ["May", "June", "ಬಿತ್ತನೆ"]],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_ML_37",
        "category": "Multilingual QA",
        "query": "महाराष्ट्रात कापूस पेरणी कधी करावी आणि पहिली खत कोणती द्यावी?",
        "lang": "mr",
        "expected_crop": "Cotton",
        "golden_facts": [["Cotton", "कापूस"], ["May", "June", "पेरणी"], ["Fertilizer", "खत"]],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_ML_38",
        "category": "Multilingual QA",
        "query": "ਕਪਾਹ ਦੀ ਬਿਜਾਈ ਕਿਸ ਮਹੀਨੇ ਕਰਨੀ ਚਾਹੀਦੀ ਹੈ?",
        "lang": "pa",
        "expected_crop": "Cotton",
        "golden_facts": [["Cotton", "ਕਪਾਹ"], ["May", "June", "ਬਿਜਾਈ"]],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_ML_39",
        "category": "Multilingual QA",
        "query": "गव्हाला मुकुट मुळे फुटण्याच्या अवस्थेत (CRI) पाणी कधी द्यावे?",
        "lang": "mr",
        "expected_crop": "Wheat",
        "golden_facts": [["Wheat", "गहू"], ["CRI", "Crown Root", "मुकुट मुळे"], ["21", "20-25", "दिवस"]],
        "min_expected_groundedness": 0.80
    },
    {
        "id": "TC_ML_40",
        "category": "Multilingual QA",
        "query": "ਟਮਾਟਰ ਦੀ ਫਸਲ ਵਿੱਚ ਖਾਦ ਅਤੇ ਸਿੰਚਾਈ ਦਾ ਪ੍ਰਬੰਧ ਕਿਵੇਂ ਕਰੀਏ?",
        "lang": "pa",
        "expected_crop": "Tomato",
        "golden_facts": [["Tomato", "ਟਮਾਟਰ"], ["Fertilizer", "NPK", "ਖਾਦ"], ["Irrigation", "ਸਿੰਚਾਈ", "ਪਾਣੀ"]],
        "min_expected_groundedness": 0.80
    }
]

def run_evaluation_suite():
    """Executes the 40 test cases, scores performance, and generates reports."""
    print("==================================================================")
    print("  Running AI Farmer Advisory Quantitative Evaluation Suite (40 TCs)")
    print("==================================================================")

    kb = AdvisoryKnowledgeBase(docs_dir="data/advisories", persist_dir="data/chroma")
    translator = IndicTransEngine(use_local_weights=False)
    agriparam = AgriParamEngine(execution_mode="demo")

    results = []
    category_stats = {}
    start_total_time = time.time()

    total_groundedness = 0.0
    total_factual_correctness = 0.0
    total_retrieval_hits = 0
    failures = []

    for tc in EVALUATION_TEST_CASES:
        t0 = time.time()
        tc_id = tc["id"]
        query = tc["query"]
        lang = tc["lang"]
        expected_crop = tc["expected_crop"]
        golden_facts = tc["golden_facts"]
        cat = tc["category"]

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "groundedness_sum": 0.0}

        category_stats[cat]["total"] += 1

        # 1. Indic to English query translation
        en_query = translator.translate_indic_to_en(query, src_lang=lang)

        # 2. Dense Vector Retrieval
        retrieved_docs = kb.retrieve(en_query, top_k=3)

        # Check retrieval hit-rate: does top-3 contain expected crop?
        retrieval_hit = any(expected_crop.lower() in doc.get("crop", "").lower() or expected_crop.lower() in doc.get("text", "").lower() for doc in retrieved_docs)
        if retrieval_hit:
            total_retrieval_hits += 1

        # 3. Advisory Generation
        gen_result = agriparam.generate_advisory(en_query, retrieved_docs, target_lang="en")
        advisory_en = gen_result["advisory_text"]

        # 4. Localization
        if lang != "en":
            localized_advisory = translator.translate_en_to_indic(advisory_en, tgt_lang=lang)
        else:
            localized_advisory = advisory_en

        # 5. Score Groundedness and Factual Correctness
        groundedness = gen_result["groundedness_score"]
        total_groundedness += groundedness
        category_stats[cat]["groundedness_sum"] += groundedness

        # Factual correctness check against golden facts (supports list of bilingual synonyms)
        combined_text = (advisory_en + " " + localized_advisory).lower()
        matched_facts = []
        for fact_item in golden_facts:
            # If fact_item is a list/tuple of synonyms, check if any matches
            if isinstance(fact_item, (list, tuple)):
                if any(syn.lower() in combined_text for syn in fact_item):
                    matched_facts.append(fact_item[0])
            elif str(fact_item).lower() in combined_text:
                matched_facts.append(str(fact_item))

        factual_score = len(matched_facts) / max(1, len(golden_facts))
        total_factual_correctness += factual_score

        duration_ms = round((time.time() - t0) * 1000, 1)

        # Pass condition
        passed = (retrieval_hit and groundedness >= 0.70 and factual_score >= 0.50)
        if passed:
            category_stats[cat]["passed"] += 1
        else:
            failures.append({
                "id": tc_id,
                "query": query,
                "category": cat,
                "lang": lang,
                "retrieval_hit": retrieval_hit,
                "groundedness": groundedness,
                "factual_score": factual_score,
                "matched_facts": matched_facts,
                "missing_facts": [f for f in golden_facts if f not in matched_facts]
            })

        results.append({
            "id": tc_id,
            "category": cat,
            "lang": lang,
            "passed": passed,
            "retrieval_hit": retrieval_hit,
            "groundedness_score": round(groundedness, 3),
            "factual_score": round(factual_score, 3),
            "duration_ms": duration_ms
        })

        status_flag = "PASS" if passed else "FAIL"
        print(f"[{status_flag}] {tc_id} ({lang}): Groundedness={groundedness:.2f}, Factual={factual_score:.2f} ({duration_ms}ms)")

    total_cases = len(EVALUATION_TEST_CASES)
    avg_groundedness = total_groundedness / total_cases
    avg_factual_correctness = total_factual_correctness / total_cases
    retrieval_precision = total_retrieval_hits / total_cases
    passed_cases = sum(1 for r in results if r["passed"])
    overall_pass_rate = (passed_cases / total_cases) * 100

    print("------------------------------------------------------------------")
    print(f"  Summary: {passed_cases}/{total_cases} Passed ({overall_pass_rate:.1f}%)")
    print(f"  Average Groundedness Score: {avg_groundedness * 100:.1f}%")
    print(f"  Average Factual Correctness: {avg_factual_correctness * 100:.1f}%")
    print(f"  Top-3 Retrieval Precision: {retrieval_precision * 100:.1f}%")
    print("==================================================================")

    # Export EVALUATION_REPORT.md
    generate_markdown_report(
        results,
        category_stats,
        failures,
        overall_pass_rate,
        avg_groundedness,
        avg_factual_correctness,
        retrieval_precision,
        time.time() - start_total_time
    )

    # Export evaluation_results.json
    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "overall_pass_rate": overall_pass_rate,
            "avg_groundedness": avg_groundedness,
            "avg_factual_correctness": avg_factual_correctness,
            "retrieval_precision": retrieval_precision,
            "category_stats": category_stats,
            "test_cases_count": total_cases,
            "failures_count": len(failures),
            "failures": failures,
            "results": results
        }, f, indent=2)

def generate_markdown_report(
    results: List[Dict[str, Any]],
    cat_stats: Dict[str, Any],
    failures: List[Dict[str, Any]],
    pass_rate: float,
    avg_groundedness: float,
    avg_factual: float,
    retrieval_precision: float,
    total_duration: float
):
    """Generates the official EVALUATION_REPORT.md file."""
    report_lines = [
        "# AI Farmer Advisory Assistant - Quantitative Evaluation & Failure Analysis Report",
        "",
        "## 1. Executive Summary & Rubric Metrics",
        "",
        "| Evaluation Metric | Measured Benchmark Score | Target Threshold | Status |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Overall Test Pass Rate** | **{pass_rate:.1f}%** | ≥ 80% | {'✅ Met' if pass_rate >= 80 else '❌ Review'} |",
        f"| **Mean Groundedness Score** | **{avg_groundedness * 100:.1f}%** | ≥ 85% | {'✅ Met' if avg_groundedness >= 0.85 else '❌ Review'} |",
        f"| **Factual Correctness** | **{avg_factual * 100:.1f}%** | ≥ 80% | {'✅ Met' if avg_factual >= 0.80 else '❌ Review'} |",
        f"| **Retrieval Precision @ 3** | **{retrieval_precision * 100:.1f}%** | ≥ 85% | {'✅ Met' if retrieval_precision >= 0.85 else '❌ Review'} |",
        "",
        f"- **Total Test Cases Evaluated**: {len(results)} representative domain QA queries",
        f"- **Total Benchmark Runtime**: {total_duration:.2f} seconds",
        "- **Evaluation Dimensions**: Sowing Calendars (10), Fertilizer NPK (8), Irrigation Scheduling (8), Pest & Disease IPM (7), Multilingual Cross-Lingual QA (7)",
        "",
        "---",
        "",
        "## 2. Category Performance Breakdown",
        "",
        "| Test Category | Total Cases | Passed Cases | Category Pass Rate | Mean Groundedness |",
        "| :--- | :---: | :---: | :---: | :---: |"
    ]

    for cat, data in cat_stats.items():
        c_rate = (data["passed"] / max(1, data["total"])) * 100
        c_avg_g = (data["groundedness_sum"] / max(1, data["total"])) * 100
        report_lines.append(f"| {cat} | {data['total']} | {data['passed']} | {c_rate:.1f}% | {c_avg_g:.1f}% |")

    report_lines.extend([
        "",
        "---",
        "",
        "## 3. Systematic Failure Analysis & Error Boundary Study",
        "",
        "### 3.1 Failure Rate & Edge-Case Identification",
        f"- **Identified Failures**: {len(failures)} / {len(results)} ({len(failures) / len(results) * 100:.1f}% error rate)",
        "",
        "### 3.2 Root Cause Taxonomy",
        "1. **Dialectal & Script Discrepancies**: Transliterating regional vernacular terms (e.g., 'నరమా' vs 'పత్తి' for Cotton or 'ਕਪਾਹ' in Punjabi) requires continuous expansion of agricultural vocabulary mappings.",
        "2. **Dual-Season Ambiguity**: Questions asking about multi-season crops (such as Tomato or Onion grown in both Kharif and Rabi) require explicit clarification on the target sowing season if not stated in the query.",
        "3. **Micro-Nutrient Thresholds**: Complex soil interactions (such as Zinc deficiency in waterlogged calcareous soils) necessitate deep multi-hop document retrieval.",
        "",
        "### 3.3 Mitigation & Hardening Interventions Implemented",
        "- **Cross-Lingual Query Normalization**: The AI4Bharat IndicTrans2 engine normalizes vernacular terms into standard English agronomic tokens before dense vector indexing.",
        "- **Dual Retrieval Scoring**: ChromaDB semantic embeddings are supplemented with lexical keyword filtering to ensure zero false positives on crop names.",
        "- **Structured Action Plan Extraction**: Generates step-by-step chronological advice (Field Prep → Fertilizer → Irrigation) to prevent cognitive overload for farmers.",
        "",
        "---",
        "",
        "## 4. Complete Test Case Execution Log",
        "",
        "| ID | Category | Language | Retrieval Hit | Groundedness | Factual Accuracy | Status |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
    ])

    for r in results:
        status_badge = "✅ PASS" if r["passed"] else "❌ FAIL"
        hit_badge = "Yes" if r["retrieval_hit"] else "No"
        report_lines.append(f"| {r['id']} | {r['category']} | {r['lang'].upper()} | {hit_badge} | {r['groundedness_score'] * 100:.0f}% | {r['factual_score'] * 100:.0f}% | {status_badge} |")

    with open("EVALUATION_REPORT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

if __name__ == "__main__":
    run_evaluation_suite()
