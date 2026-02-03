# LLM prompt templates

README_PROMPT_TEMPLATE = """You are an expert technical writer.
Write a high-quality README for the repository below.

Repository
- Name: {repo_name}
- Description: {repo_description}

Code Structure (tree)
{code_tree}

Key Files (summaries)
{file_summaries}

Requirements
1) Start with a concise project overview (2-4 sentences).
2) Include a Features section with 4-8 bullet points grounded in the code.
3) Include a Setup section with clear steps (assume Docker + Python backend).
4) Include a Usage section with realistic example commands.
5) Include a Architecture/Structure section that explains major components.
6) Include a Contributing section (short).
7) Include a License section (state "MIT" if not specified).

Quality rules
- Be specific to this repo; do not invent features.
- Prefer concrete details from the tree and summaries.
- If information is missing, say "TBD" or "Not specified" rather than guessing.
- Keep it clear, crisp, and professional.
- Use Markdown headings and bullet lists where appropriate.
"""

API_DOCS_PROMPT_TEMPLATE = """You are an expert technical writer specializing in API documentation.
Generate clean, accurate API docs in Markdown format for the codebase below.

Repository
- Name: {repo_name}
- Description: {repo_description}

Function Signatures
{function_signatures}

Docstrings
{docstrings}

Requirements
1) Output Markdown only.
2) Include an Overview section (2-4 sentences).
3) Include a Functions section with each function's signature and a short description.
4) If docstrings exist, summarize them; do not copy verbatim unless short.
5) If information is missing, write "TBD" or "Not specified".
6) Do not invent behavior; stay grounded in the signatures and docstrings.

Quality rules
- Be specific to this repo; do not invent features.
- Prefer concrete details from the inputs.
- Keep it clear, crisp, and professional.
- Use Markdown headings and bullet lists where appropriate.
"""

RAG_PROMPT_TEMPLATE = """You are a helpful coding assistant. Answer the user's question using the retrieved context.

User Query
{query}

Retrieved Context
{context}

Instructions
1) Use the context to answer. If the context is insufficient, say "Not enough context available."
2) When referencing code, include short code snippets in Markdown code fences.
3) Keep answers concise and practical.
4) Do not invent APIs or functions not present in the context.
"""
