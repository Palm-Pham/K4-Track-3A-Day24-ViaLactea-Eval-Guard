from __future__ import annotations

"""Phase C: Production Guardrails — Presidio PII + NeMo Guardrails + P95 Latency."""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ADVERSARIAL_SET_PATH, GUARDRAILS_CONFIG_DIR, PRESIDIO_LANGUAGE


# ─── Task 9a: Presidio PII Detection ─────────────────────────────────────────

def setup_presidio():
    """Khởi tạo Presidio engine với custom Vietnamese PII recognizers. (Đã implement sẵn)

    Custom recognizers thêm vào:
        VN_CCCD  — số CCCD 12 chữ số hoặc CMND 9 chữ số
        VN_PHONE — số điện thoại Việt Nam (0[3-9]xxxxxxxx)

    Các recognizers mặc định đã có sẵn: EMAIL, PHONE_NUMBER (international), ...
    """
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
    from presidio_anonymizer import AnonymizerEngine

    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[
            Pattern("CCCD 12 digits", r"\b\d{12}\b", 0.9),
            Pattern("CMND 9 digits",  r"\b\d{9}\b",  0.7),
        ],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern("VN mobile", r"\b0[3-9]\d{8}\b", 0.9)],
    )

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)

    analyzer  = AnalyzerEngine(registry=registry)
    anonymizer = AnonymizerEngine()
    return analyzer, anonymizer


def pii_scan(text: str, analyzer=None, anonymizer=None) -> dict:
    """Task 9a: Quét PII trong văn bản bằng Presidio.

    Returns:
        {
          "has_pii":    bool,
          "entities":   [{"type": str, "text": str, "score": float, "start": int, "end": int}],
          "anonymized": str,   # text với PII được thay bằng <TYPE>
        }
    """
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()

    results = analyzer.analyze(text=text, language=PRESIDIO_LANGUAGE)
    # Task 9a covers identifiers, phone and email; English PERSON/license NER
    # mislabels Vietnamese policy text. NeMo handles contextual personal-data requests.
    results = [result for result in results if result.entity_type in
               {"VN_CCCD", "VN_PHONE", "PHONE_NUMBER", "EMAIL_ADDRESS"}]
    if not results:
        return {"has_pii": False, "entities": [], "anonymized": text}

    entities = [
        {"type": result.entity_type, "text": text[result.start:result.end],
         "score": round(float(result.score), 3), "start": result.start, "end": result.end}
        for result in results
    ]
    entities.sort(key=lambda entity: (entity["start"], entity["end"], entity["type"]))
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results).text
    return {"has_pii": True, "entities": entities, "anonymized": anonymized}


# ─── Task 9b + 11: NeMo Guardrails ───────────────────────────────────────────

def setup_nemo_rails():
    """Khởi tạo NeMo Guardrails từ guardrails/config.yml. (Đã implement sẵn)

    Config directory: guardrails/
        config.yml  — model + rails config
        rails.co    — câu từ chối Colang 1.0; built-in self-check flows được bật trong YAML
    """
    from nemoguardrails import RailsConfig, LLMRails
    config = RailsConfig.from_path(GUARDRAILS_CONFIG_DIR)
    main = next(model for model in config.models if model.type == "main")
    if main.engine == "openai":
        # NeMo 0.10 infers chat only from gpt-3.5/gpt-4 names; newer names need an explicit client.
        from langchain_openai import ChatOpenAI
        class GuardChatOpenAI(ChatOpenAI):
            def _get_request_payload(self, *args, **kwargs):
                payload = super()._get_request_payload(*args, **kwargs)
                if self.model_name == "gpt-6-luna" and "max_tokens" in payload:
                    payload["max_completion_tokens"] = payload.pop("max_tokens")
                return payload
        return LLMRails(config, llm=GuardChatOpenAI(model=main.model, **main.parameters))
    rails  = LLMRails(config)
    return rails


def _normalize_for_echo_comparison(text: str) -> str:
    """Collapse whitespace so an echoed answer cannot evade the fallback check."""
    return " ".join(text.split())


async def check_input_rail(text: str, rails=None) -> dict:
    """Task 9b: Kiểm tra input qua NeMo input rails (topic guard + jailbreak guard).

    Returns:
        {
          "allowed":        bool,
          "blocked_reason": str | None,
          "response":       str,          # NeMo's raw response
        }
    """
    if rails is None:
        rails = setup_nemo_rails()

    result = await rails.generate_async(
        messages=[{"role": "user", "content": text}],
        options={"rails": ["input"], "log": {"activated_rails": True}},
    )
    response = result.response[0]["content"]
    activated_rails = result.log.activated_rails
    blocked = any(
        bool(rail.get("stop")) if isinstance(rail, dict) else bool(getattr(rail, "stop", False))
        for rail in (activated_rails or [])
    )
    return {
        "allowed": not blocked,
        "blocked_reason": "nemo_input_rail" if blocked else None,
        "response": response,
    }


async def check_output_rail(question: str, answer: str, rails=None) -> dict:
    """Task 11: Kiểm tra LLM output qua NeMo output rails trước khi trả về user.

    NeMo output rails hoạt động trong context của cả cuộc hội thoại (input + output).
    Kiểm tra PII và nội dung nhạy cảm. Self-check này không thay RAGAS faithfulness
    hoặc kiểm tra factual accuracy với retrieved contexts.

    Returns:
        {
          "safe":           bool,
          "flagged_reason": str | None,
          "final_answer":   str,          # answer đã qua guard (có thể bị redact)
        }
    """
    if rails is None:
        rails = setup_nemo_rails()

    result = await rails.generate_async(
        messages=[
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        options={"rails": ["output"], "log": {"activated_rails": True}},
    )
    response = result.response[0]["content"]
    activated_rails = result.log.activated_rails
    flagged = any(
        bool(rail.get("stop")) if isinstance(rail, dict) else bool(getattr(rail, "stop", False))
        for rail in (activated_rails or [])
    )
    if not flagged:
        return {"safe": True, "flagged_reason": None, "final_answer": answer}

    # NeMo normally returns the configured refusal when an output rail stops.
    # Fail closed if it returns an empty response or echoes the unsafe answer.
    final_answer = response.strip() if isinstance(response, str) else ""
    if (not final_answer
            or _normalize_for_echo_comparison(final_answer)
            == _normalize_for_echo_comparison(answer)):
        final_answer = (
            "Xin lỗi, tôi không thể cung cấp nội dung này vì có thể chứa thông tin "
            "nhạy cảm."
        )
    return {
        "safe": False,
        "flagged_reason": "nemo_output_rail",
        "final_answer": final_answer,
    }


# ─── Task 10: Adversarial Test Suite ─────────────────────────────────────────

def run_adversarial_suite(adversarial_set: list[dict], rails=None,
                           analyzer=None, anonymizer=None) -> list[dict]:
    """Task 10: Chạy 20 adversarial inputs qua full guard stack, so sánh với expected.

    Guard stack order:
        1. pii_scan()         → block nếu has_pii (cho category pii_injection)
        2. check_input_rail() → block nếu jailbreak / off-topic / prompt injection

    Returns:
        list of {
          "id": int, "category": str, "input": str,
          "expected": "blocked"|"allowed",
          "actual":   "blocked"|"allowed",
          "blocked_by": str | None,       # "presidio" | "nemo_input" | None
          "passed": bool,
        }
    """
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def _run_all():
        results = []
        for item in adversarial_set:
            blocked_by = None

            pii_result = pii_scan(item["input"], analyzer, anonymizer)
            if pii_result["has_pii"]:
                blocked_by = "presidio"

            if blocked_by is None:
                rail_result = await check_input_rail(item["input"], rails)
                if not rail_result["allowed"]:
                    blocked_by = "nemo_input"

            actual = "blocked" if blocked_by else "allowed"
            results.append({
                "id": item["id"],
                "category": item["category"],
                "input": item["input"],
                "expected": item["expected"],
                "actual": actual,
                "blocked_by": blocked_by,
                "passed": actual == item["expected"],
            })
        return results

    results = asyncio.run(_run_all())
    passed = sum(1 for result in results if result["passed"])
    print(f"Adversarial suite: {passed}/{len(results)} passed")
    return results


# ─── Task 12: P95 Latency Measurement ────────────────────────────────────────

def measure_p95_latency(test_inputs: list[str], n_runs: int = 20,
                         rails=None, analyzer=None, anonymizer=None) -> dict:
    """Task 12: measure INPUT layers sequentially, not end-to-end guard/RAG latency.

    Reuse engines. Inside ONE event loop, execute two real warm-up calls per layer,
    excluded from samples. Then collect exactly n_runs timed samples (cycle clean
    inputs), always measuring BOTH PII and NeMo input even if PII blocks.
    Use perf_counter; keep raw milliseconds. summarize_latency() supplies linear
    percentiles at (n - 1) * q. Submission requires n_runs >= 20.
    Short-circuit request timing, RAG and output timing are outside this scope.
    """
    from src.experiment_support import summarize_latency

    if not test_inputs or any(not isinstance(text, str) or not text.strip() for text in test_inputs):
        raise ValueError("test_inputs must contain at least one non-empty string")
    if type(n_runs) is not int or n_runs < 20:
        raise ValueError("n_runs must be an integer >= 20")
    if analyzer is None or anonymizer is None:
        default_analyzer, default_anonymizer = setup_presidio()
        if analyzer is None:
            analyzer = default_analyzer
        if anonymizer is None:
            anonymizer = default_anonymizer
    if rails is None:
        rails = setup_nemo_rails()

    async def _measure():
        # Warm both input layers twice. These calls initialize the real engines
        # but are intentionally excluded from the timed samples.
        for index in range(2):
            text = test_inputs[index % len(test_inputs)]
            pii_scan(text, analyzer, anonymizer)
            await check_input_rail(text, rails)

        samples = []
        for index in range(n_runs):
            text = test_inputs[index % len(test_inputs)]

            started = time.perf_counter()
            pii_scan(text, analyzer, anonymizer)
            presidio_ms = (time.perf_counter() - started) * 1000

            started = time.perf_counter()
            # Always measure NeMo, including for a PII-positive input, so each
            # sample describes both sequential layers rather than short-circuit latency.
            await check_input_rail(text, rails)
            nemo_input_ms = (time.perf_counter() - started) * 1000

            if presidio_ms <= 0 or nemo_input_ms <= 0:
                raise RuntimeError("Latency samples must have positive layer durations")
            samples.append({
                "presidio_ms": presidio_ms,
                "nemo_input_ms": nemo_input_ms,
                "input_guard_ms": presidio_ms + nemo_input_ms,
            })
        return samples

    return summarize_latency(asyncio.run(_measure()), warmup_runs=2)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "c", *sys.argv[1:]]))
