from __future__ import annotations

import hmac
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import json_text, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
WORKSPACE_ROOT = ROOT.parent
TRANSCRIPTS_DIR = ROOT / "transcripts"
PROVIDER_NAMES = ["openrouter", "openai", "anthropic", "gemini"]
PROVIDER_ENV_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
VERSION_LABELS = ["v0", "v1", "v2", "v3"]
VERSION_ROOTS = {
    version: WORKSPACE_ROOT / f"starter_{version}"
    for version in VERSION_LABELS
}
MAX_INPUT_CHARS = 4000
MAX_TURNS_PER_SESSION = 20
MAX_TOOL_ROUNDS = 4
MAX_PUBLIC_STRING_CHARS = 12000
MAX_PUBLIC_LIST_ITEMS = 50
MAX_PUBLIC_DICT_ITEMS = 100
MAX_PUBLIC_DEPTH = 8
MAX_RUN_FILE_BYTES = 10 * 1024 * 1024
PROMPT_LEAK_REPLACEMENT = (
    "Mình không thể cung cấp hoặc tái tạo instruction nội bộ, system prompt hay secret. "
    "Mình vẫn có thể mô tả khả năng của agent và thực hiện một yêu cầu research hợp lệ."
)

load_lab_env(ROOT)


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def configured_provider_names() -> list[str]:
    return [
        name
        for name in PROVIDER_NAMES
        if (os.getenv(PROVIDER_ENV_KEYS[name]) or "").strip()
    ]


def is_sensitive_field(name: str) -> bool:
    normalized = name.strip().lower().replace("-", "_")
    exact_names = {
        "access_code",
        "access_token",
        "api_key",
        "authorization",
        "cookie",
        "credential",
        "credentials",
        "id_token",
        "password",
        "private_key",
        "refresh_token",
        "secret",
        "token",
    }
    sensitive_suffixes = (
        "_access_code",
        "_access_token",
        "_api_key",
        "_authorization",
        "_cookie",
        "_credential",
        "_credentials",
        "_password",
        "_private_key",
        "_refresh_token",
        "_secret",
        "_token",
    )
    return normalized in exact_names or normalized.endswith(sensitive_suffixes)


def sensitive_env_values() -> list[str]:
    values: list[str] = []
    for name, value in os.environ.items():
        if (is_sensitive_field(name) or name in PROVIDER_ENV_KEYS.values()) and len(value) >= 8:
            values.append(value)
    return sorted(set(values), key=len, reverse=True)


def redact_text(value: str) -> str:
    redacted = value.replace(str(WORKSPACE_ROOT.resolve()), "<WORKSPACE_ROOT>")
    for secret in sensitive_env_values():
        redacted = redacted.replace(secret, "[REDACTED]")

    patterns = (
        (r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{8,}", r"\1[REDACTED]"),
        (r"https://api\.telegram\.org/bot[^/\s]+/", "https://api.telegram.org/bot[REDACTED]/"),
        (r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b", "[REDACTED_TELEGRAM_TOKEN]"),
        (r"\bAIza[A-Za-z0-9_-]{20,}\b", "[REDACTED_API_KEY]"),
        (r"\b(?:tvly|fc)-[A-Za-z0-9_-]{12,}\b", "[REDACTED_API_KEY]"),
    )
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted


def redact_sensitive(value: Any, *, key: str = "", depth: int = 0) -> Any:
    if is_sensitive_field(key):
        return "[REDACTED]"
    if depth >= MAX_PUBLIC_DEPTH:
        return "[TRUNCATED_MAX_DEPTH]"
    if isinstance(value, str):
        redacted = redact_text(value)
        if len(redacted) > MAX_PUBLIC_STRING_CHARS:
            return redacted[:MAX_PUBLIC_STRING_CHARS] + "\n...<truncated>"
        return redacted
    if isinstance(value, dict):
        items = list(value.items())
        redacted_dict = {
            item_key: redact_sensitive(item_value, key=str(item_key), depth=depth + 1)
            for item_key, item_value in items[:MAX_PUBLIC_DICT_ITEMS]
        }
        if len(items) > MAX_PUBLIC_DICT_ITEMS:
            redacted_dict["_truncated_fields"] = len(items) - MAX_PUBLIC_DICT_ITEMS
        return redacted_dict
    if isinstance(value, list):
        redacted_list = [redact_sensitive(item, depth=depth + 1) for item in value[:MAX_PUBLIC_LIST_ITEMS]]
        if len(value) > MAX_PUBLIC_LIST_ITEMS:
            redacted_list.append(f"...<{len(value) - MAX_PUBLIC_LIST_ITEMS} items truncated>")
        return redacted_list
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item, depth=depth + 1) for item in value[:MAX_PUBLIC_LIST_ITEMS])
    return value


def contains_sensitive_input(value: str) -> bool:
    if any(secret in value for secret in sensitive_env_values()):
        return True
    secret_patterns = (
        r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b",
        r"\bAIza[A-Za-z0-9_-]{20,}\b",
        r"\b(?:tvly|fc)-[A-Za-z0-9_-]{12,}\b",
        r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}",
    )
    return any(re.search(pattern, value) for pattern in secret_patterns)


def normalized_text(value: str) -> str:
    return " ".join(value.lower().split())


def contains_system_prompt_leak(value: str, system_prompt: str) -> bool:
    response = normalized_text(value)
    prompt = normalized_text(system_prompt)
    if len(response) < 60 or len(prompt) < 60:
        return False
    if prompt in response:
        return True

    prompt_lines = [
        normalized_text(line)
        for line in system_prompt.splitlines()
        if len(normalized_text(line)) >= 80
    ]
    if any(line in response for line in prompt_lines):
        return True

    window = 100
    step = 40
    prompt_windows = [prompt[index:index + window] for index in range(0, max(1, len(prompt) - window + 1), step)]
    return any(len(fragment) == window and fragment in response for fragment in prompt_windows)


def is_sensitive_extraction_request(value: str) -> bool:
    text = normalized_text(value)
    protected_material = (
        "system prompt",
        "developer message",
        "hidden instruction",
        "internal instruction",
        "prompt hệ thống",
        "chỉ dẫn hệ thống",
        "chỉ dẫn ẩn",
        "instruction nội bộ",
    )
    if any(phrase in text for phrase in protected_material):
        return True

    extraction_verbs = (
        "show",
        "reveal",
        "print",
        "dump",
        "list",
        "read",
        "display",
        "cho xem",
        "hiển thị",
        "in ra",
        "tiết lộ",
        "đọc file",
        "liệt kê",
    )
    secret_targets = (
        ".env",
        "environment variable",
        "api key",
        "access token",
        "credential",
        "secret",
        "biến môi trường",
        "khóa api",
    )
    return any(verb in text for verb in extraction_verbs) and any(target in text for target in secret_targets)


def secure_loop_result(result: dict[str, Any], system_prompt: str) -> dict[str, Any]:
    secured = redact_sensitive(result)
    leak_blocked = False

    assistant_text = str(secured.get("assistant_text") or "")
    if contains_system_prompt_leak(assistant_text, system_prompt):
        secured["assistant_text"] = PROMPT_LEAK_REPLACEMENT
        leak_blocked = True

    for round_data in secured.get("rounds") or []:
        round_text = str(round_data.get("assistant_text") or "")
        if contains_system_prompt_leak(round_text, system_prompt):
            round_data["assistant_text"] = "[BLOCKED_SYSTEM_PROMPT_LEAK]"
            leak_blocked = True

    if leak_blocked:
        secured["security_event"] = "system_prompt_leak_blocked"
    return secured


def version_root(version: str) -> Path:
    try:
        root = VERSION_ROOTS[version].resolve()
    except KeyError as exc:
        raise ValueError(f"Unsupported artifact version: {version}") from exc
    if not root.is_dir():
        raise FileNotFoundError(f"Missing artifact directory: starter_{version}")
    return root


def load_version_tool_functions(version: str, root: Path) -> dict[str, Any]:
    if version == "v0":
        from tools import TOOL_FUNCTIONS

        return dict(TOOL_FUNCTIONS)

    module_name = f"_day04_{version}_tools"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return dict(cached.TOOL_FUNCTIONS)

    init_path = root / "tools" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        module_name,
        init_path,
        submodule_search_locations=[str(init_path.parent)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load tool registry for {version}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return dict(module.TOOL_FUNCTIONS)


def tool_has_side_effect(name: str, root: Path) -> bool:
    tool_doc = root / "tools" / name / "TOOL.md"
    try:
        raw = tool_doc.read_text(encoding="utf-8")
    except OSError:
        return name == "send"
    frontmatter = raw.split("---", 2)[1] if raw.startswith("---") and raw.count("---") >= 2 else ""
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip().lower()
    side_effect = metadata.get("side_effect", "false")
    return (
        metadata.get("kind") == "action"
        or side_effect not in {"", "false", "none"}
        or metadata.get("requires_confirmation") == "true"
    )


def filter_public_tools(
    declarations: list[dict[str, Any]],
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    if env_flag("DAY04_ALLOW_SIDE_EFFECT_TOOLS") or env_flag("DAY04_ALLOW_ACTION_TOOLS"):
        return declarations, []
    blocked = [
        item.get("name", "")
        for item in declarations
        if tool_has_side_effect(str(item.get("name", "")), root)
    ]
    enabled = [item for item in declarations if item.get("name") not in blocked]
    return enabled, blocked


class RestrictedProvider:
    def __init__(self, provider: Any, allowed_tool_names: set[str], system_prompt: str) -> None:
        self._provider = provider
        self.allowed_tool_names = allowed_tool_names
        self.system_prompt = system_prompt
        self.default_model = getattr(provider, "default_model", None)
        self.blocked_tool_calls: list[str] = []
        self.blocked_prompt_leaks = 0

    def complete(self, *args: Any, **kwargs: Any) -> Any:
        response = self._provider.complete(*args, **kwargs)
        allowed_calls = []
        blocked_calls = []
        for call in response.tool_calls:
            serialized_args = json.dumps(call.args, ensure_ascii=False, default=str)
            args_are_sensitive = (
                contains_sensitive_input(serialized_args)
                or contains_system_prompt_leak(serialized_args, self.system_prompt)
            )
            if call.name in self.allowed_tool_names and not args_are_sensitive:
                allowed_calls.append(call)
            else:
                blocked_calls.append(call.name)
        if blocked_calls:
            self.blocked_tool_calls.extend(blocked_calls)
            response.tool_calls = allowed_calls
            if not allowed_calls:
                response.text = "Tool call đã bị chặn bởi demo-safe mode."
        if contains_system_prompt_leak(str(response.text or ""), self.system_prompt):
            response.text = PROMPT_LEAK_REPLACEMENT
            self.blocked_prompt_leaks += 1
        return response


def enforce_optional_access_code() -> None:
    expected = os.getenv("DAY04_DEMO_ACCESS_CODE", "")
    if not expected:
        return
    st.title("🔒 Research Agent")
    provided = st.text_input("Demo access code", type="password")
    if not provided or not hmac.compare_digest(provided, expected):
        st.info("Nhập access code để mở demo.")
        st.stop()


def new_session_id(version: str, provider_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return "_".join([safe_slug(version), safe_slug(provider_name), timestamp])


def load_runtime(version: str, provider_name: str, model_override: str) -> dict[str, Any]:
    root = version_root(version)
    prompt_path = root / "artifacts" / "system_prompt.md"
    tools_path = root / "artifacts" / "tools.yaml"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    all_declarations = load_tool_declarations(tools_path)
    declarations, blocked_tools = filter_public_tools(all_declarations, root)
    registry = load_version_tool_functions(version, root)
    declared_names = {str(item["name"]) for item in all_declarations}
    missing_implementations = sorted(declared_names - set(registry))
    if missing_implementations:
        raise RuntimeError(
            f"Missing tool implementations for {version}: {', '.join(missing_implementations)}"
        )
    enabled_names = {str(item["name"]) for item in declarations}
    base_provider = make_provider(provider_name)
    selected_model = model_override.strip() or getattr(base_provider, "default_model", None)
    provider = RestrictedProvider(
        base_provider,
        {item["name"] for item in declarations},
        system_prompt,
    )
    artifact = build_artifact_version(version, prompt_path, tools_path)
    return {
        "root": root,
        "prompt_path": prompt_path,
        "tools_path": tools_path,
        "system_prompt": system_prompt,
        "declarations": declarations,
        "all_declarations": all_declarations,
        "blocked_tools": blocked_tools,
        "tools": to_openai_tools(declarations),
        "tool_functions": {
            name: implementation
            for name, implementation in registry.items()
            if name in enabled_names
        },
        "provider": provider,
        "model": selected_model,
        "artifact": artifact,
    }


def runtime_signature(
    version: str,
    provider_name: str,
    model: str | None,
    artifact_version: str,
    history_window: int,
    max_tool_rounds: int,
    enabled_tool_names: list[str],
) -> str:
    return "|".join(
        [
            version,
            provider_name,
            model or "",
            artifact_version,
            str(history_window),
            str(max_tool_rounds),
            ",".join(enabled_tool_names),
        ]
    )


def create_transcript(
    *,
    version: str,
    provider_name: str,
    model: str | None,
    history_window: int,
    max_tool_rounds: int,
    artifact: Any,
    enabled_tools: list[str],
    blocked_tools: list[str],
) -> tuple[Path, dict[str, Any]]:
    transcript_id = new_session_id(version, provider_name)
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact),
        "provider": provider_name,
        "model": model,
        "system_prompt": f"starter_{version}/artifacts/system_prompt.md",
        "tools": f"starter_{version}/artifacts/tools.yaml",
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "enabled_tools": enabled_tools,
        "blocked_tools": blocked_tools,
        "demo_safe_mode": not (
            env_flag("DAY04_ALLOW_SIDE_EFFECT_TOOLS")
            or env_flag("DAY04_ALLOW_ACTION_TOOLS")
        ),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "source": "streamlit_ui",
        "turns": [],
    }
    return transcript_path, transcript


def reset_ui_session() -> None:
    for key in (
        "display_messages",
        "history",
        "transcript",
        "transcript_path",
        "runtime_signature",
    ):
        st.session_state.pop(key, None)


def ensure_ui_state() -> None:
    st.session_state.setdefault("display_messages", [])
    st.session_state.setdefault("history", [])


def result_status(result: Any) -> str:
    if not isinstance(result, dict):
        return "ok"
    if result.get("error"):
        return "error"
    if result.get("awaiting_user") or result.get("status") == "needs_confirmation":
        return "waiting"
    return str(result.get("status") or "ok")


def status_icon(status: str) -> str:
    return {
        "ok": "✅",
        "sent": "✅",
        "answered": "✅",
        "error": "❌",
        "waiting": "⏸️",
    }.get(status, "ℹ️")


def render_tool_trace(turn: dict[str, Any]) -> None:
    rounds = turn.get("rounds") or []
    if not rounds:
        if turn.get("error"):
            st.error(redact_text(str(turn["error"])))
        return

    tool_call_count = sum(len(round_data.get("tool_calls") or []) for round_data in rounds)
    has_error = any(
        result_status(event.get("result", {})) == "error"
        for round_data in rounds
        for event in (round_data.get("tool_results") or [])
    )
    trace_label = f"🧭 Tool trace · {tool_call_count} calls · {len(rounds)} rounds"
    with st.expander(trace_label, expanded=has_error):
        for round_data in rounds:
            round_number = round_data.get("round", "?")
            calls = round_data.get("tool_calls") or []
            events = round_data.get("tool_results") or []
            with st.container(border=True):
                st.markdown(f"##### Round {round_number}")
                if not calls:
                    st.caption("✅ Model trả lời trực tiếp, không gọi thêm tool.")
                    continue

                for index, call in enumerate(calls):
                    event = events[index] if index < len(events) else {}
                    result = event.get("result", {})
                    status = result_status(result)
                    st.markdown(
                        f"{status_icon(status)} **{call.get('name', 'unknown')}** "
                        f"· `{status}`"
                    )
                    args_col, result_col = st.columns(2, gap="large")
                    with args_col:
                        st.caption("ARGUMENTS")
                        st.json(redact_sensitive(call.get("args") or {}))
                    with result_col:
                        st.caption("RESULT / ERROR")
                        st.json(redact_sensitive(result))
                    if index < len(calls) - 1:
                        st.divider()


def render_chat_history() -> None:
    for message in st.session_state.display_messages:
        with st.chat_message(message["role"]):
            st.markdown(message.get("content") or "")
            if message["role"] == "assistant" and message.get("turn"):
                render_tool_trace(message["turn"])


def load_run_files(version: str | None = None) -> list[Path]:
    roots = [version_root(version)] if version else list(VERSION_ROOTS.values())
    run_files = [
        path
        for root in roots
        for path in (root / "runs").glob("*.json")
    ]
    return sorted(
        run_files,
        key=lambda path: ("_base_" in path.name, path.stat().st_mtime),
        reverse=True,
    )


def load_run(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    allowed_run_dirs = {
        (root / "runs").resolve()
        for root in VERSION_ROOTS.values()
    }
    if path.is_symlink() or resolved.parent not in allowed_run_dirs:
        raise ValueError("Invalid run path")
    if not resolved.is_file() or resolved.stat().st_size > MAX_RUN_FILE_BYTES:
        raise ValueError("Invalid run file")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Run payload must be an object")
    return redact_sensitive(payload)


def render_run_evidence(version: str) -> None:
    st.subheader("📊 Run evidence")
    st.caption(f"Metric và failure evidence của artifact {version}; ưu tiên base run mới nhất.")
    run_files = load_run_files(version)
    if not run_files:
        st.info("Chưa có run JSON. Hãy chạy baseline v0 trước, sau đó refresh trang.")
        return

    run_options = {
        f"{path.parent.parent.name}/{path.name}": path
        for path in run_files
    }
    selected_label = st.selectbox(
        "Chọn run",
        list(run_options),
        key=f"run_selector_{version}",
    )
    selected = run_options[selected_label]
    try:
        run = load_run(selected)
    except (OSError, ValueError, json.JSONDecodeError):
        st.error("Không đọc được run JSON đã chọn.")
        return

    summary = run.get("summary") or {}
    metric_cols = st.columns(4)
    metric_cols[0].metric("Version", run.get("version", "—"))
    metric_cols[1].metric("Case accuracy", summary.get("case_accuracy", "—"))
    metric_cols[2].metric("Routing accuracy", summary.get("tool_routing_accuracy", "—"))
    metric_cols[3].metric("Argument accuracy", summary.get("argument_accuracy", "—"))

    with st.expander("Artifact fingerprint & full summary"):
        st.code(run.get("artifact_version", "unknown artifact"), language=None)
        st.json(summary)

    rows = []
    for item in run.get("results") or []:
        if not isinstance(item, dict):
            continue
        result = item.get("result") or {}
        if not isinstance(result, dict):
            result = {}
        rows.append(
            {
                "case": item.get("id"),
                "passed": result.get("passed"),
                "failure_type": result.get("failure_type"),
                "observed_mismatch": result.get("observed_mismatch"),
                "tool_calls": json.dumps(result.get("actual_tool_calls") or [], ensure_ascii=False),
            }
        )
    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)

    if env_flag("DAY04_ENABLE_EVIDENCE_DOWNLOADS"):
        st.download_button(
            "Tải run JSON đã redacted",
            data=json_text(run),
            file_name=selected.name,
            mime="application/json",
        )
    else:
        st.caption("Raw evidence download đang tắt trong demo-safe mode.")


def render_tool_catalog(declarations: list[dict[str, Any]]) -> None:
    st.subheader("🧰 Enabled tools")
    st.caption("Danh sách runtime được đọc trực tiếp từ tools.yaml của artifact đang chọn.")
    columns = st.columns(2, gap="large")
    for index, declaration in enumerate(declarations):
        name = declaration.get("name", "unknown")
        parameters = declaration.get("parameters") or {}
        required = parameters.get("required") or []
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"#### 🔧 `{name}`")
                st.write(declaration.get("description") or "Chưa có mô tả.")
                st.caption(
                    f"{len((parameters.get('properties') or {}))} arguments"
                    f" · {len(required)} required"
                )
                with st.expander("Input schema"):
                    st.json(parameters)


def render_empty_chat_state() -> None:
    with st.container(border=True):
        st.markdown("**Bắt đầu một phiên research**")
        st.caption(
            "Thử một trong các tình huống dưới đây để kiểm tra direct answer, "
            "clarification boundary hoặc local policy tool."
        )
        examples = (
            ("💬 Direct answer", "Bạn là gì và có thể làm gì?"),
            ("❓ Clarification", "Tóm tắt 5 tweet mới nhất giúp mình"),
            ("📚 Local policy", "Theo policy công ty, API key nên được bảo vệ thế nào?"),
        )
        columns = st.columns(3, gap="large")
        for column, (label, prompt) in zip(columns, examples):
            with column:
                st.markdown(f"**{label}**")
                st.write(prompt)


def main() -> None:
    st.set_page_config(page_title="Research Agent Lab", page_icon="🔎", layout="wide")
    enforce_optional_access_code()
    ensure_ui_state()

    st.title("🔎 Research Agent Lab")
    st.caption(
        "Research with auditable tool calls · Inspect every round · Compare evidence from v0 to v3"
    )

    with st.sidebar:
        st.header("⚙️ Demo controls")
        st.caption("ARTIFACT")
        version = st.selectbox("Artifact label", VERSION_LABELS, index=0)
        available_providers = configured_provider_names()
        if not available_providers:
            st.error("Chưa có model provider API key trong `.env`.")
            st.stop()
        st.caption("MODEL PROVIDER")
        provider_name = st.selectbox("Provider", available_providers, index=0)
        if env_flag("DAY04_ALLOW_MODEL_OVERRIDE"):
            model_override = st.text_input("Model override", placeholder="Để trống để dùng model mặc định")
        else:
            model_override = ""
            st.caption("Model override đã khóa trong demo-safe mode.")
        with st.expander("Advanced runtime settings"):
            history_window = st.number_input("History window", min_value=0, max_value=10, value=5)
            max_tool_rounds = st.number_input(
                "Max tool rounds",
                min_value=1,
                max_value=MAX_TOOL_ROUNDS,
                value=MAX_TOOL_ROUNDS,
            )
        if st.button("＋ New chat session", width="stretch", type="primary"):
            reset_ui_session()
            st.rerun()

        st.divider()
        if env_flag("DAY04_ALLOW_SIDE_EFFECT_TOOLS") or env_flag("DAY04_ALLOW_ACTION_TOOLS"):
            st.warning("Side-effect tools đang được bật cho UI.")
        else:
            st.success("Demo-safe mode active")
            st.caption("Side-effect tools và raw evidence download đang tắt.")
        st.caption(
            "Chọn đúng label v0–v3 tại thời điểm chạy; prompt/tools hash sẽ được lưu cùng transcript."
        )

    try:
        runtime = load_runtime(version, provider_name, model_override)
    except Exception:
        st.error("Không load được runtime. Kiểm tra prompt, tools YAML và provider configuration.")
        st.stop()

    artifact = runtime["artifact"]
    signature = runtime_signature(
        version,
        provider_name,
        runtime["model"],
        artifact.artifact_version,
        int(history_window),
        int(max_tool_rounds),
        [item["name"] for item in runtime["declarations"]],
    )

    if st.session_state.get("runtime_signature") not in {None, signature}:
        reset_ui_session()
        ensure_ui_state()
        st.info("Runtime hoặc artifact đã đổi; UI đã bắt đầu session mới để không trộn evidence giữa các version.")

    if "transcript" not in st.session_state:
        transcript_path, transcript = create_transcript(
            version=version,
            provider_name=provider_name,
            model=runtime["model"],
            history_window=int(history_window),
            max_tool_rounds=int(max_tool_rounds),
            artifact=artifact,
            enabled_tools=[item["name"] for item in runtime["declarations"]],
            blocked_tools=runtime["blocked_tools"],
        )
        st.session_state.transcript_path = transcript_path
        st.session_state.transcript = transcript
        st.session_state.runtime_signature = signature

    with st.sidebar:
        st.divider()
        st.caption("ACTIVE RUNTIME")
        st.code(runtime["model"] or "provider default", language=None)
        st.caption(
            f"{len(runtime['declarations'])} tools enabled"
            f" · {len(runtime['blocked_tools'])} side-effect tools blocked"
        )

    info_cols = st.columns(4, gap="large")
    info_cols[0].metric("Version", version)
    info_cols[1].metric("Provider", provider_name)
    info_cols[2].metric("Enabled tools", len(runtime["declarations"]))
    info_cols[3].metric(
        "Session turns",
        f"{len(st.session_state.transcript['turns'])}/{MAX_TURNS_PER_SESSION}",
    )
    with st.expander("🔐 Artifact fingerprint & runtime policy"):
        st.code(artifact.artifact_version, language=None)
        st.caption(f"Model: `{runtime['model'] or 'provider default'}`")
        if runtime["blocked_tools"]:
            st.caption(f"Blocked side-effect tools: {', '.join(runtime['blocked_tools'])}")
        st.caption(
            f"Session: {st.session_state.transcript['transcript_id']}"
            f" · {len(st.session_state.transcript['turns'])}/{MAX_TURNS_PER_SESSION} turns"
        )

    chat_tab, runs_tab, tools_tab = st.tabs(["💬 Chat", "📊 Run evidence", "🧰 Tools"])

    with chat_tab:
        if not st.session_state.display_messages:
            render_empty_chat_state()
        render_chat_history()
        turn_limit_reached = len(st.session_state.transcript["turns"]) >= MAX_TURNS_PER_SESSION
        if turn_limit_reached:
            st.warning("Session đã đạt giới hạn request. Hãy chọn New chat session nếu cần tiếp tục demo.")
        user_text = st.chat_input(
            "Nhập yêu cầu research...",
            max_chars=MAX_INPUT_CHARS,
            disabled=turn_limit_reached,
        )
        if user_text and len(user_text) > MAX_INPUT_CHARS:
            st.error(f"Input vượt giới hạn {MAX_INPUT_CHARS} ký tự và chưa được gửi tới model.")
        elif user_text and user_text.strip():
            safe_user_text = redact_text(user_text)
            st.session_state.display_messages.append({"role": "user", "content": safe_user_text})
            with st.chat_message("user"):
                st.markdown(safe_user_text)

            turn_index = len(st.session_state.transcript["turns"]) + 1
            turn_record: dict[str, Any] = {
                "turn_index": turn_index,
                "started_at": now_iso(),
                "user": safe_user_text,
                "status": "started",
                "assistant_text": None,
                "rounds": [],
                "tool_events": [],
            }
            if contains_sensitive_input(user_text):
                assistant_text = "Request đã bị chặn vì có vẻ chứa credential hoặc secret."
                turn_record.update(
                    {
                        "status": "blocked_sensitive_input",
                        "assistant_text": assistant_text,
                        "security_event": "sensitive_input_blocked",
                    }
                )
            elif is_sensitive_extraction_request(user_text):
                assistant_text = PROMPT_LEAK_REPLACEMENT
                turn_record.update(
                    {
                        "status": "blocked_sensitive_extraction",
                        "assistant_text": assistant_text,
                        "security_event": "sensitive_extraction_blocked",
                    }
                )
            else:
                messages = [
                    {"role": "system", "content": runtime["system_prompt"]},
                    *trim_history(st.session_state.history, int(history_window)),
                    {"role": "user", "content": user_text},
                ]

                try:
                    with st.spinner("Agent đang xử lý..."):
                        raw_result = run_model_tool_loop(
                            provider=runtime["provider"],
                            messages=messages,
                            tools=runtime["tools"],
                            model=model_override.strip() or None,
                            max_tool_rounds=int(max_tool_rounds),
                            tool_functions=runtime["tool_functions"],
                        )
                    if runtime["provider"].blocked_tool_calls:
                        raw_result["security_events"] = {
                            "blocked_tool_calls": runtime["provider"].blocked_tool_calls,
                        }
                    if runtime["provider"].blocked_prompt_leaks:
                        raw_result.setdefault("security_events", {})[
                            "blocked_prompt_leaks"
                        ] = runtime["provider"].blocked_prompt_leaks
                    result = secure_loop_result(raw_result, runtime["system_prompt"])
                    turn_record.update(result)
                    assistant_text = result.get("assistant_text") or ""
                    st.session_state.history.extend(
                        [
                            {"role": "user", "content": user_text},
                            {"role": "assistant", "content": assistant_text},
                        ]
                    )
                except Exception as exc:
                    assistant_text = "Không thể hoàn thành request vì provider gặp lỗi."
                    turn_record.update(
                        {
                            "status": "provider_error",
                            "assistant_text": assistant_text,
                            "error": f"{type(exc).__name__}: {redact_text(str(exc))}",
                        }
                    )

            turn_record["ended_at"] = now_iso()
            safe_turn_record = redact_sensitive(turn_record)
            st.session_state.transcript["turns"].append(safe_turn_record)
            write_transcript(
                st.session_state.transcript_path,
                redact_sensitive(st.session_state.transcript),
            )
            st.session_state.display_messages.append(
                {"role": "assistant", "content": assistant_text, "turn": safe_turn_record}
            )

            with st.chat_message("assistant"):
                st.markdown(assistant_text)
                render_tool_trace(safe_turn_record)

        transcript = st.session_state.transcript
        with st.expander("📁 Session evidence"):
            st.caption(f"Transcript: `transcripts/{st.session_state.transcript_path.name}`")
            evidence_cols = st.columns([1, 2])
            with evidence_cols[0]:
                st.download_button(
                    "Download redacted transcript",
                    data=json_text(redact_sensitive(transcript)),
                    file_name=st.session_state.transcript_path.name,
                    mime="application/json",
                    disabled=not transcript.get("turns"),
                    width="stretch",
                )
            with evidence_cols[1]:
                st.caption(
                    "Transcript lưu request/response, tool rounds, artifact hash và runtime policy. "
                    "Secret và đường dẫn máy được redacted trước khi ghi."
                )

    with runs_tab:
        render_run_evidence(version)

    with tools_tab:
        render_tool_catalog(runtime["declarations"])


if __name__ == "__main__":
    main()
