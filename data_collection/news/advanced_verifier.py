import os
import re
from typing import List, Tuple

class AdvancedContentVerifier:
    """
    Lightweight, optional advanced content verifier.
    - Currently implements a configurable hate-speech detector.
    - No external dependencies; enabled via env: ENABLE_HATE_SPEECH_DETECTOR=true
    - Terms can be provided via HATE_SPEECH_TERMS (comma-separated) or HATE_SPEECH_TERMS_FILE (one per line).
    """

    def __init__(self) -> None:
        self._terms: List[str] = self._load_terms()
        # Precompile regexes with word boundaries, case-insensitive
        self._patterns = [re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE) for t in self._terms]

    def _load_terms(self) -> List[str]:
        terms: List[str] = []
        env_terms = os.getenv("HATE_SPEECH_TERMS", "").strip()
        if env_terms:
            terms.extend([t.strip().lower() for t in env_terms.split(",") if t.strip()])
        terms_file = os.getenv("HATE_SPEECH_TERMS_FILE", "").strip()
        if terms_file and os.path.exists(terms_file):
            try:
                with open(terms_file, "r", encoding="utf-8") as f:
                    for line in f:
                        t = line.strip().lower()
                        if t:
                            terms.append(t)
            except Exception:
                # Fail closed on external file; keep existing terms
                pass
        # Deduplicate
        return sorted(list({t for t in terms if t}))

    def detect_hate_speech(self, text: str) -> Tuple[bool, float, List[str]]:
        """
        Return (flag, score, matches).
        - flag: True if any term is matched
        - score: simple normalized score by number of distinct terms matched (0..1)
        - matches: distinct matched terms (lowercased)
        """
        if not text or not self._patterns:
            return (False, 0.0, [])

        found: List[str] = []
        for term, pat in zip(self._terms, self._patterns):
            if pat.search(text):
                found.append(term)
        distinct = sorted(list(set(found)))
        if not distinct:
            return (False, 0.0, [])
        # Score: cap by 10 terms for sanity
        score = min(1.0, len(distinct) / 10.0)
        return (True, score, distinct)
