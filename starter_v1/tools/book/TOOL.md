---
name: book
track: core
kind: live_api
provider: BigBookAPI
requires_env: [BOOK_API_KEY]
inputs: [query, max_results]
outputs: [items]
side_effect: false
---
# book

Searches for books via BigBookAPI by title, author, or keyword. Returns book
metadata: title, authors, rating, image, and book ID.
