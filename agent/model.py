import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)


# =========================================================
# MODEL CONFIG
# =========================================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


# =========================================================
# CACHED MODEL
# =========================================================

_tokenizer = None
_model = None


# =========================================================
# LOAD MODEL ONCE
# =========================================================

def get_qwen_model():

    global _tokenizer
    global _model

    # -----------------------------------------------------
    # Already loaded
    # -----------------------------------------------------

    if _tokenizer is not None and _model is not None:

        print("[MODEL] Using cached Qwen model.")

        return _tokenizer, _model

    # -----------------------------------------------------
    # First load
    # -----------------------------------------------------

    print("[MODEL] Loading Qwen model for the first time...")

    _tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME
    )

    _model.eval()

    print("[MODEL] Qwen model loaded successfully.")

    return _tokenizer, _model