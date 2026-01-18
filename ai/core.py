import os
import threading
from typing import Dict, Any
from llama_cpp import Llama

# Default local model path (keep models/ out of git via .gitignore)
DEFAULT_MODEL_PATH = "./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
DEFAULT_N_CTX = 4096
DEFAULT_N_GPU_LAYERS = 35

_llm_instance = None
_llm_lock = threading.Lock()

class MechanicLLMInitError(Exception):
    pass

class ModelConfig:
    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        n_ctx: int = DEFAULT_N_CTX,
        n_gpu_layers: int = DEFAULT_N_GPU_LAYERS,
    ):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers

class MechanicLLM:
    def __init__(self, config: ModelConfig):
        if not os.path.exists(config.model_path):
            raise MechanicLLMInitError(f"Model path does not exist: {config.model_path}")
        print(f"🧠 Loading model from {config.model_path} ...")
        self.llm = Llama(
            model_path=config.model_path,
            n_ctx=config.n_ctx,
            n_gpu_layers=config.n_gpu_layers,
            verbose=False,
        )
        print("✅ Model loaded successfully.")

    def generate_diagnosis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        vehicle = data.get("vehicle") or "Unknown"
        codes = data.get("codes") or []
        symptoms = data.get("symptoms") or "None"
        prior = data.get("prior_repairs") or "None"

        prompt = (
            f"Vehicle: {vehicle}\n"
            f"Codes: {', '.join(codes) if codes else 'None'}\n"
            f"Symptoms: {symptoms}\n"
            f"Prior Repairs: {prior}\n\n"
            "You are an expert automotive diagnostician. Provide a concise, step-by-step diagnostic plan "
            "with likely root causes (with brief rationale), concrete tests, and safety notes. "
            "Format clearly with bullets and short lines."
        )

        out = self.llm.create_completion(
            prompt=prompt,
            temperature=0.35,
            max_tokens=600,
            stop=["###"],
        )
        text = out["choices"][0]["text"].strip()

        return {
            "summary": "AI-generated diagnostic plan.",
            "suggestions": [
                {"title": "Primary Diagnostic", "details": text}
            ],
            "ai_plan": text,
        }

def get_mechanic_llm() -> MechanicLLM:
    """Lazy, thread-safe singleton init to avoid reloader/multi-init issues."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    with _llm_lock:
        if _llm_instance is not None:
            return _llm_instance
        config = ModelConfig()
        _llm_instance = MechanicLLM(config)
        return _llm_instance
