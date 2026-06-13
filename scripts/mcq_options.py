"""
Shared multiple-choice option handling for the Paper 1 runners (EXP1 logprobs, EXP2 instruct,
EXP3/4/5 variants). Centralized so the three runners cannot diverge on option handling.

Why this exists: the focused-1,030 set is 4-option with options as a dict ({"A": "text", ...})
and `answer` equal to an option's value text. The full/test sets are 5-option with options as a
LIST of label-prefixed strings (["A. Chloramphenicol", ..., "E. Trimethoprim"]) and a bare-text
`answer` ("Ceftriaxone"). A 4-option runner silently drops option E and mis-scores the rest.

These helpers are option-count- and schema-agnostic:
  * normalize_options  -> ordered {letter: text} from a dict OR a label-prefixed list
  * option_letters     -> the letters actually present for THIS question (A-D, A-E, ...)
  * render_options     -> canonical "A. text\nB. text..." listing EVERY present option
  * answer_letter      -> the correct letter, robust to value-text / prefixed / letter / idx
  * letters_phrase     -> "A, B, C, or D"  /  "A, B, C, D, or E"   (for the instruct prompt)
  * extract_first / extract_cot -> answer extraction over the present letters only

Backward compatibility: on the focused 4-option dict schema these reproduce the original
behavior exactly (sorted "A. v" rendering, exact-value answer match, [A-D] extraction,
"A, B, C, or D" phrasing), so existing focused results are unchanged.
"""
import re

_LABEL = re.compile(r'\s*([A-Za-z])\s*[.)]\s*(.*)', re.DOTALL)


def normalize_options(raw):
    """Return an ordered {LETTER: text} dict from a dict or a list of options.

    dict -> keys uppercased, text kept verbatim.
    list -> parse a leading 'X. ' / 'X) ' label if present (and strip it from the text);
            otherwise assign A, B, C, ... by position.
    """
    if isinstance(raw, dict):
        return {str(k).strip().upper(): v for k, v in raw.items()}
    out = {}
    for i, entry in enumerate(raw):
        s = "" if entry is None else str(entry)
        m = _LABEL.match(s)
        if m:
            out[m.group(1).upper()] = m.group(2).strip()
        else:
            out[chr(ord('A') + i)] = s.strip()
    return out


def option_letters(options):
    """Sorted list of the letters present in this (already-normalized) question."""
    return sorted(options.keys())


def render_options(options):
    """Canonical 'A. text\\nB. text...' listing EVERY present option, in letter order."""
    return "\n".join(f"{l}. {options[l]}" for l in option_letters(options))


def _norm_text(x):
    """Lowercase, strip, drop a leading 'X. ' label — for tolerant answer/option matching."""
    s = "" if x is None else str(x).strip()
    m = _LABEL.match(s)
    if m:
        s = m.group(2)
    return s.strip().lower()


def answer_letter(item, options):
    """Resolve the correct option letter for `item` against normalized `options`.

    Resolution order (first hit wins):
      1. exact value-text match (preserves original focused behavior byte-for-byte)
      2. answer is itself a single letter
      3. answer is a label-prefixed string ('D. Ceftriaxone' / 'D) ...')
      4. tolerant text match (case-insensitive, label-stripped) — handles the full set's
         bare-text answer vs the list's 'D. Ceftriaxone' rendering
      5. integer answer_idx, if present
      6. fall back to the first present letter
    """
    letters = option_letters(options)
    ans = item.get('answer')
    if ans is not None:
        for l in letters:                       # (1) exact value match
            if options[l] == ans:
                return l
    a = '' if ans is None else str(ans).strip()
    if len(a) == 1 and a.upper() in options:    # (2) bare letter
        return a.upper()
    m = _LABEL.match(a)                          # (3) label-prefixed answer
    if m and m.group(1).upper() in options:
        return m.group(1).upper()
    na = _norm_text(a)                           # (4) tolerant text match
    if na:
        for l in letters:
            if _norm_text(options[l]) == na:
                return l
    idx = item.get('answer_idx')                 # (5) explicit index
    if isinstance(idx, int) and 0 <= idx < len(letters):
        return letters[idx]
    return letters[0]                            # (6) fallback


def letters_phrase(letters):
    """'A' / 'A or B' / 'A, B, C, or D' / 'A, B, C, D, or E' — for prompt instructions."""
    letters = list(letters)
    if len(letters) == 1:
        return letters[0]
    if len(letters) == 2:
        return f"{letters[0]} or {letters[1]}"
    return ", ".join(letters[:-1]) + ", or " + letters[-1]


def _charclass(letters):
    return "[" + "".join(sorted({l.upper() for l in letters})) + "]"


def extract_first(text, letters):
    """First valid letter (multi-strategy), restricted to the letters present this question."""
    valid = {l.upper() for l in letters}
    s = (text or "").strip()
    if s and s[0].upper() in valid:
        return s[0].upper()
    cls = _charclass(letters)
    for pat in (rf'ANSWER[:\s]+({cls})', rf'Answer[:\s]+({cls})', rf'answer[:\s]+({cls})'):
        m = re.search(pat, s, re.IGNORECASE)
        if m and m.group(1).upper() in valid:
            return m.group(1).upper()
    for ch in s[:50]:
        if ch.upper() in valid:
            return ch.upper()
    for ch in s:
        if ch.upper() in valid:
            return ch.upper()
    return option_letters_fallback(letters)


def extract_cot(text, letters):
    """CoT: prefer the letter after the final 'answer', else the last valid present letter."""
    valid = {l.upper() for l in letters}
    cls = _charclass(letters)
    matches = list(re.finditer(rf'answer[:\s]*\(?({cls})\)?', text or "", re.IGNORECASE))
    if matches:
        return matches[-1].group(1).upper()
    seen = [c.upper() for c in (text or "") if c.upper() in valid]
    return seen[-1] if seen else option_letters_fallback(letters)


def option_letters_fallback(letters):
    ls = sorted({l.upper() for l in letters})
    return ls[0] if ls else 'A'
