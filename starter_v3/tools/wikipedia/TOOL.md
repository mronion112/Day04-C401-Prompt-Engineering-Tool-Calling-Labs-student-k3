---
name: wikipedia
track: core
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [query, lang]
outputs: [items, url, page_id]
side_effect: false
---
# wikipedia

Searches Wikipedia and returns the summary of a topic. Use for quick background
knowledge, definitions, and factual reference. Not for current news or social
media — use `lookup` or `social_search` for those.
