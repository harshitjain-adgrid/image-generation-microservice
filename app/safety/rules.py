"""
Generator-level safety rules.

Appended to the image generation prompt as a second layer of defence
against brand hallucination. Independent of the refiner's system prompt.

GPT Image 2 is a reasoning model — it follows explicit constraints well.
"""

GPT_SAFETY_SUFFIX = (
    "\n\nSTRICT RULES: Do not render any real-world brand names, logos, or trademarks "
    "anywhere in the image unless they are explicitly named in this prompt. "
    "All products must appear completely unbranded with blank/plain labels. "
    "Any brand names that ARE explicitly mentioned in this prompt MUST be rendered accurately."
)
