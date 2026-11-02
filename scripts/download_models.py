"""
Explicit Model Downloader for Farmer Advisory Assistant.
Downloads BharatGen AgriParam, AI4Bharat IndicTrans2, and Multilingual MiniLM
to a visible local directory (./models_cache) on Drive D: with progress reporting.
"""

import os
import sys
import argparse
from huggingface_hub import snapshot_download

# Default local cache directory on Drive D in the project workspace
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CACHE_DIR = os.path.join(PROJECT_ROOT, "models_cache")

MODELS_REGISTRY = {
    "embeddings": {
        "repo_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "description": "Multilingual Dense Embedding Model (~120 MB)",
        "approx_size": "120 MB",
        "subfolder": "embeddings_minilm"
    },
    "indictrans_indic_en": {
        "repo_id": "ai4bharat/indictrans2-indic-en-dist-200M",
        "description": "AI4Bharat IndicTrans2 Indic-to-English NMT (~400 MB)",
        "approx_size": "400 MB",
        "subfolder": "indictrans2_indic_en"
    },
    "indictrans_en_indic": {
        "repo_id": "ai4bharat/indictrans2-en-indic-dist-200M",
        "description": "AI4Bharat IndicTrans2 English-to-Indic NMT (~400 MB)",
        "approx_size": "400 MB",
        "subfolder": "indictrans2_en_indic"
    },
    "agriparam": {
        "repo_id": "bharatgenai/AgriParam",
        "description": "BharatGen AgriParam 2.9B Domain LLM for Indian Agriculture (~5.8 GB)",
        "approx_size": "5.8 GB",
        "subfolder": "bharatgen_agriparam"
    }
}

def download_model(key: str, dest_dir: str, hf_token: str = None):
    meta = MODELS_REGISTRY.get(key)
    if not meta:
        print(f"[!] Unknown model key: {key}. Available: {list(MODELS_REGISTRY.keys())}")
        return

    repo_id = meta["repo_id"]
    target_path = os.path.join(dest_dir, meta["subfolder"])
    os.makedirs(target_path, exist_ok=True)

    print("\n" + "="*70)
    print(f"  Downloading: {meta['description']}")
    print(f"  Hugging Face Repo: https://huggingface.co/{repo_id}")
    print(f"  Approximate Size: {meta['approx_size']}")
    print(f"  Target Local Directory: {target_path}")
    print("="*70)

    try:
        downloaded_path = snapshot_download(
            repo_id=repo_id,
            local_dir=target_path,
            local_dir_use_symlinks=False,
            token=hf_token
        )
        print(f"\n[+] Successfully downloaded {repo_id} to:\n    {downloaded_path}")
    except Exception as e:
        print(f"\n[-] Error downloading {repo_id}: {e}")
        print("    If the repository requires authentication, provide your token with --token or HF_TOKEN.")

def main():
    parser = argparse.ArgumentParser(description="Download sovereign AI models locally to project directory.")
    parser.add_argument(
        "--model",
        type=str,
        default="lightweight",
        choices=["all", "lightweight", "agriparam", "indictrans", "embeddings"],
        help="Select which model(s) to download. 'lightweight' downloads embeddings & IndicTrans2 (~900MB). 'all' includes AgriParam (~5.8GB)."
    )
    parser.add_argument(
        "--dest",
        type=str,
        default=DEFAULT_CACHE_DIR,
        help=f"Target directory for saved weights (default: {DEFAULT_CACHE_DIR})"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("HF_TOKEN"),
        help="Hugging Face personal access token (optional for public models)."
    )
    args = parser.parse_args()

    print(f"Farmer Advisor Model Storage Location: {args.dest}")

    if args.model == "all":
        for k in MODELS_REGISTRY:
            download_model(k, args.dest, args.token)
    elif args.model == "lightweight":
        print("\n[*] Downloading lightweight sovereign models (Embeddings + IndicTrans2 ~920 MB total)...")
        download_model("embeddings", args.dest, args.token)
        download_model("indictrans_indic_en", args.dest, args.token)
        download_model("indictrans_en_indic", args.dest, args.token)
        print("\n[*] Lightweight models downloaded. To download the 5.8GB AgriParam LLM, run: python scripts/download_models.py --model agriparam")
    elif args.model == "indictrans":
        download_model("indictrans_indic_en", args.dest, args.token)
        download_model("indictrans_en_indic", args.dest, args.token)
    elif args.model == "agriparam":
        download_model("agriparam", args.dest, args.token)
    elif args.model == "embeddings":
        download_model("embeddings", args.dest, args.token)

if __name__ == "__main__":
    main()
