import re
from typing import List

def validate_citations(response_text: str, retrieved_chunk_count: int) -> str:
    """
    Ensure that all [n] citations in the response are valid.
    If a citation [n] is not within the range [1, retrieved_chunk_count], it is removed.
    """
    def replace_citation(match):
        try:
            n = int(match.group(1))
            if 1 <= n <= retrieved_chunk_count:
                return f"[{n}]"
            return "" # Remove invalid citation
        except ValueError:
            return ""

    # Match [n] or [n:L...] where n is a digit
    return re.sub(r"\[(\d+)(?::[^\]]*)?\]", replace_citation, response_text)
