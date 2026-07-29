---
name: translate
track: core
kind: live_api
provider: Google Translate (deep-translator)
requires_env: []
inputs: [text, target_lang, source_lang]
outputs: [translated_text, source_lang, target_lang]
side_effect: false
---
# translate

Translates text between languages using Google Translate (free, no API key).
`target_lang` is the target language code (e.g. 'vi', 'en', 'fr', 'ja').
`source_lang` is 'auto' by default. Use when the user asks to translate
text from one language to another.
