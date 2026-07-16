# SPDX-License-Identifier: MIT
"""Local instruction-tuned model provider (default: Mistral 7B via transformers).

This provider is entirely optional. It only imports the heavy ML stack
(``torch`` / ``transformers``) when the model is actually loaded, so importing
this module never pulls in those dependencies. Install with the ``local-ai``
extra to use it.
"""

from __future__ import annotations

import logging
from typing import Any

from moneyflow.ai.base import AIProvider, AIUnavailableError
from moneyflow.ai.prompt_builder import build_flat_prompt
from moneyflow.config.settings import get_settings

logger = logging.getLogger(__name__)


class LocalMistralProvider(AIProvider):
    """Run a local instruct model with transformers.

    Loading downloads and initialises a multi-gigabyte model, so construction is
    cheap and the model is only loaded on :meth:`load`.
    """

    name = "Local model"

    def __init__(self, model_name: str | None = None) -> None:
        super().__init__()
        self.model_name = model_name or get_settings().ai_model
        self.device = "cpu"
        self._tokenizer: Any = None
        self._model: Any = None

    def is_available(self) -> bool:
        """True if the optional ML dependencies can be imported."""
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError:
            return False
        return True

    def load(self) -> None:
        if self._ready:
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise AIUnavailableError(
                "Local model support is not installed. Install the 'local-ai' extra."
            ) from exc

        try:
            from transformers import BitsAndBytesConfig

            bnb_available = True
        except ImportError:
            bnb_available = False

        if torch.cuda.is_available():
            self.device = "cuda"
            use_quantization = bnb_available
        elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            self.device = "cpu"  # 7B float16 buffers are unreliable on MPS; use CPU.
            use_quantization = False
        else:
            self.device = "cpu"
            use_quantization = False

        logger.info("Loading local model '%s' on %s", self.model_name, self.device)

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, trust_remote_code=True, use_fast=False
        )
        self._tokenizer.pad_token = self._tokenizer.eos_token

        if use_quantization:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                device_map=None,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

        self._model.eval()
        self._ready = True

    def generate_insights(
        self,
        financial_data: dict[str, Any],
        user_query: str | None = None,
        concise: bool = False,
        max_tokens: int | None = None,
        **_: Any,
    ) -> str:
        if not self._ready:
            self.load()

        import torch

        settings = get_settings()
        max_new = max_tokens or settings.ai_max_tokens
        if self.device != "cuda":
            max_new = min(max_new, 400)  # keep CPU/MPS inference responsive

        prompt = build_flat_prompt(financial_data, user_query, concise)
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048 if self.device == "cuda" else 1024,
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new,
                temperature=settings.ai_temperature,
                top_p=0.9,
                do_sample=True,
                repetition_penalty=1.1,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "[/INST]" in text:
            return text.split("[/INST]")[-1].strip()
        return text[len(prompt) :].strip()
