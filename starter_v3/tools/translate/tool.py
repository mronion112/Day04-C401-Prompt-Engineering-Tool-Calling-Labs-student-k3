from __future__ import annotations

from typing import Any

from tools._shared import err

SUPPORTED_LANGS = {
    "vi", "en", "fr", "de", "ja", "ko", "zh", "es", "pt", "ru",
    "ar", "hi", "it", "nl", "pl", "th", "tr", "id", "ms", "tl",
}


def _validate_lang(lang: str) -> str:
    lang = (lang or "en").strip().lower()
    if lang not in SUPPORTED_LANGS:
        raise ValueError(f"Unsupported language: {lang}. Supported: {', '.join(sorted(SUPPORTED_LANGS))}")
    return lang


def _detect_lang(text: str) -> str:
    for ch in text:
        o = ord(ch)
        if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
            return "zh"
        if 0x3040 <= o <= 0x309F or 0x30A0 <= o <= 0x30FF:
            return "ja"
        if 0xAC00 <= o <= 0xD7AF:
            return "ko"
        if 0x0E00 <= o <= 0x0E7F:
            return "th"
        if 0x0900 <= o <= 0x097F:
            return "hi"
        if 0x0600 <= o <= 0x06FF:
            return "ar"
    return "en"


def translate_text(text: str = "", target_lang: str = "vi", source_lang: str = "auto") -> dict[str, Any]:
    try:
        target_lang = _validate_lang(target_lang)
        text = (text or "").strip()
        if not text:
            return {"tool": "translate_text", "error": "No text provided."}

        from deep_translator import GoogleTranslator

        if source_lang == "auto":
            source_lang = _detect_lang(text)

        result = GoogleTranslator(source=source_lang, target=target_lang).translate(text)

        return {
            "tool": "translate_text",
            "original_text": text[:2000],
            "translated_text": result,
            "source_lang": source_lang,
            "target_lang": target_lang,
        }
    except ImportError:
        return {
            "tool": "translate_text",
            "error": "deep-translator not installed. Run: pip install deep-translator",
        }
    except ValueError as exc:
        return {"tool": "translate_text", "error": "unsupported_language", "message": str(exc)}
    except Exception as exc:
        return err("translate_text", exc)
