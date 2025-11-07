import logging
import re

logger = logging.getLogger(__name__)


# ——— Context utilities —————————————————————————————————

def last_sentences(text: str, n: int) -> str:
    """
    Grab the last n sentences (naïve split) for context truncation.
    """
    sentences = re.split(r'(?<=[\.!?])\s+', text.strip())
    return " ".join(sentences[-n:])
