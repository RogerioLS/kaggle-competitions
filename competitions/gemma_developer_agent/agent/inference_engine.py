"""Inference Engine & Gemma 4 Prompt Formatting Abstraction.

Provides structured prompt template rendering according to Gemma 4 turn tokens
(<start_of_turn>user, <start_of_turn>model, <end_of_turn>), JSON tool-call schema
injection, and inference backends for Hugging Face Transformers, vLLM, and offline
deterministic mock execution.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Gemma native turn tokens
START_OF_TURN = "<start_of_turn>"
END_OF_TURN = "<end_of_turn>"
USER_ROLE = "user"
MODEL_ROLE = "model"


@dataclass
class ChatMessage:
    """Represents a conversational turn in the Gemma chat template."""

    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in (USER_ROLE, MODEL_ROLE):
            raise ValueError(
                f"Invalid role '{self.role}'. Expected '{USER_ROLE}' or '{MODEL_ROLE}'."
            )


class GemmaPromptFormatter:
    """Formats multi-turn conversations and tool schemas using Gemma's turn tokens."""

    @staticmethod
    def render_tool_declarations(tools: Dict[str, Dict[str, Any]]) -> str:
        """Renders tool schemas and JSON invocation contracts for system prompts.

        Args:
            tools: Mapping of tool_name to dict with description and parameter schemas.

        Returns:
            Formatted string describing available tools and required JSON output format.
        """
        lines = [
            "### Available Tools",
            "You have access to the following execution tools in the repository sandbox:",
            "",
        ]
        for name, spec in sorted(tools.items()):
            desc = spec.get("description", "No description provided.")
            params = spec.get("parameters", {})
            param_str = json.dumps(params, indent=2) if params else "{}"
            lines.append(f"- **`{name}`**: {desc}")
            lines.append(f"  Parameters: `{param_str}`")

        lines.extend(
            [
                "",
                "### Action Output Format",
                "CRITICAL RULE: DO NOT CHAT. DO NOT EXPLAIN OUTSIDE JSON. DO NOT GREET.",
                "To invoke a tool, your output MUST contain exclusively a single JSON block:",
                "```json",
                "{",
                '  "thought": "Step-by-step reasoning explaining why this action is necessary",',
                '  "sub_agent": "explorer|locator|drafter|validator",',
                '  "tool": "<tool_name>",',
                '  "arguments": { "<arg_key>": "<arg_value>" }',
                "}",
                "```",
                "When the bug is fully resolved and verified, call `submit_patch` to finish.",
            ]
        )
        return "\n".join(lines)

    @classmethod
    def format_conversation(
        cls,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        tool_declarations: Optional[str] = None,
        add_generation_prompt: bool = True,
    ) -> str:
        """Renders conversational history into a Gemma 4 raw token sequence.

        Args:
            messages: List of ChatMessage objects in chronological order.
            system_prompt: Optional system-level instructions.
            tool_declarations: Optional tool descriptions string.
            add_generation_prompt: If True, appends `<start_of_turn>model\\n` to prompt.

        Returns:
            Rendered prompt string ready for causal LM tokenization.
        """
        prompt_parts: List[str] = []

        system_block_parts: List[str] = []
        if system_prompt and system_prompt.strip():
            system_block_parts.append(system_prompt.strip())
        if tool_declarations and tool_declarations.strip():
            system_block_parts.append(tool_declarations.strip())

        system_header = "\n\n".join(system_block_parts)

        first_user_turn = True
        for msg in messages:
            if msg.role == USER_ROLE:
                prompt_parts.append(f"{START_OF_TURN}{USER_ROLE}")
                if first_user_turn and system_header:
                    prompt_parts.append(f"{system_header}\n\n{msg.content.strip()}")
                    first_user_turn = False
                else:
                    prompt_parts.append(msg.content.strip())
                prompt_parts.append(f"{END_OF_TURN}")
            elif msg.role == MODEL_ROLE:
                prompt_parts.append(f"{START_OF_TURN}{MODEL_ROLE}")
                prompt_parts.append(msg.content.strip())
                prompt_parts.append(f"{END_OF_TURN}")

        # If no user messages exist yet, include system header as first user turn
        if first_user_turn and system_header:
            prompt_parts.append(f"{START_OF_TURN}{USER_ROLE}")
            prompt_parts.append(system_header)
            prompt_parts.append(f"{END_OF_TURN}")

        if add_generation_prompt:
            prompt_parts.append(f"{START_OF_TURN}{MODEL_ROLE}\n")

        return "\n".join(prompt_parts)


class InferenceEngine(ABC):
    """Abstract base interface for LLM inference backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.2,
        top_p: float = 0.95,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Generates completion text from prompt.

        Args:
            prompt: Rendered prompt sequence.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            top_p: Nucleus sampling probability mass.
            stop_sequences: Sequences that stop generation when encountered.

        Returns:
            Generated text string.
        """


class MockInferenceEngine(InferenceEngine):
    """Deterministic mock inference engine for offline unit testing and dry runs."""

    def __init__(
        self,
        canned_responses: Optional[List[str]] = None,
        dynamic_handler: Optional[Callable[[str], str]] = None,
    ) -> None:
        """Initializes mock inference engine.

        Args:
            canned_responses: Sequential list of responses to return per turn.
            dynamic_handler: Optional custom callback responding dynamically to prompts.
        """
        self.canned_responses = list(canned_responses) if canned_responses else []
        self.dynamic_handler = dynamic_handler
        self.generation_count = 0
        self.prompts_received: List[str] = []

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.2,
        top_p: float = 0.95,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Returns canned or dynamically handled response."""
        self.prompts_received.append(prompt)
        self.generation_count += 1

        if self.dynamic_handler:
            return self.dynamic_handler(prompt)

        if self.canned_responses:
            resp = self.canned_responses.pop(0)
            return resp

        # Default fallback response: submit patch
        return (
            "```json\n"
            "{\n"
            '  "thought": "Task completed successfully. Submitting patch.",\n'
            '  "sub_agent": "validator",\n'
            '  "tool": "submit_patch",\n'
            '  "arguments": {}\n'
            "}\n"
            "```"
        )


class TransformersInferenceEngine(InferenceEngine):
    """Hugging Face Transformers inference backend for Gemma 4 models."""

    def __init__(
        self,
        model_id_or_path: str,
        device: str = "auto",
        torch_dtype: str = "auto",
        quantization_bits: Optional[int] = None,
        max_memory: Optional[Dict[Any, str]] = None,
    ) -> None:
        """Initializes transformers model and tokenizer.

        Args:
            model_id_or_path: HuggingFace model ID or local directory path.
            device: Target device string ("auto", "cuda", "cpu").
            torch_dtype: Precision string ("auto", "bfloat16", "float16", "float32").
            quantization_bits: Optional quantization bits (4, 8, or None).
            max_memory: Optional per-device memory limits for accelerate/transformers.
        """
        self.model_id_or_path = model_id_or_path
        self.device = device
        self.torch_dtype = torch_dtype
        self.quantization_bits = quantization_bits
        self.max_memory = max_memory
        self._model: Any = None
        self._tokenizer: Any = None
        self._is_initialized = False

    def _ensure_loaded(self) -> None:
        """Lazy loads model and tokenizer upon first invocation."""
        if self._is_initialized:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "transformers and torch are required for TransformersInferenceEngine. "
                "Install with `pip install transformers torch`."
            ) from exc

        logger.info("Loading tokenizer from %s...", self.model_id_or_path)
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_id_or_path,
            trust_remote_code=True,
        )

        load_kwargs: Dict[str, Any] = {
            "trust_remote_code": True,
            "device_map": self.device,
        }

        if self.max_memory is not None:
            load_kwargs["max_memory"] = self.max_memory

        if self.torch_dtype == "bfloat16":
            load_kwargs["torch_dtype"] = torch.bfloat16
        elif self.torch_dtype == "float16":
            load_kwargs["torch_dtype"] = torch.float16
        elif self.torch_dtype == "auto":
            load_kwargs["torch_dtype"] = "auto"

        if self.quantization_bits == 4:
            try:
                from transformers import BitsAndBytesConfig

                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
            except ImportError:
                logger.warning("bitsandbytes not installed; loading without 4-bit quantization.")

        logger.info("Loading model weights from %s...", self.model_id_or_path)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id_or_path,
            **load_kwargs,
        )
        self._is_initialized = True

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.2,
        top_p: float = 0.95,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Executes autoregressive text generation using loaded Hugging Face model."""
        self._ensure_loaded()
        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        gen_kwargs: Dict[str, Any] = {
            "max_new_tokens": max_tokens,
            "temperature": max(temperature, 1e-4),
            "top_p": top_p,
            "do_sample": temperature > 0.0,
            "pad_token_id": self._tokenizer.pad_token_id or self._tokenizer.eos_token_id,
        }

        with torch.no_grad():
            output_tokens = self._model.generate(**inputs, **gen_kwargs)

        input_len = inputs["input_ids"].shape[1]
        new_tokens = output_tokens[0][input_len:]
        decoded = self._tokenizer.decode(new_tokens, skip_special_tokens=False)

        # Enforce stop sequences
        stop_tokens = stop_sequences or [END_OF_TURN, "<eos>"]
        for stop_seq in stop_tokens:
            if stop_seq in decoded:
                decoded = decoded.split(stop_seq)[0]

        return decoded.strip()
