import re
from pathlib import Path

I18N_PATH = Path(__file__).resolve().parent.parent / "utils" / "i18n.py"


def _extract_keys(block: str) -> set:
    return set(re.findall(r'^\s*"([a-zA-Z0-9_.]+)":', block, re.M))


def _load_vi_en_blocks():
    content = I18N_PATH.read_text(encoding="utf-8")
    vi_block = content.split('TRANSLATIONS["vi"].update({')[1].split('TRANSLATIONS["en"].update({')[0]
    en_block = content.split('TRANSLATIONS["en"].update({')[1]
    return vi_block, en_block


def test_vi_en_key_parity():
    """Every i18n key must exist in both languages, or t() silently falls
    back and the UI shows the wrong language for that string."""
    vi_block, en_block = _load_vi_en_blocks()
    vi_keys, en_keys = _extract_keys(vi_block), _extract_keys(en_block)

    missing_in_en = vi_keys - en_keys
    missing_in_vi = en_keys - vi_keys
    assert not missing_in_en, f"Keys present in VI but missing in EN: {sorted(missing_in_en)}"
    assert not missing_in_vi, f"Keys present in EN but missing in VI: {sorted(missing_in_vi)}"
    assert len(vi_keys) > 100, "Suspiciously few keys found - the split markers may be stale"


def test_no_duplicate_keys_within_a_language():
    """A duplicate key silently shadows the earlier definition - catch it here
    instead of discovering the wrong string shows up in the UI."""
    for lang, block in zip(("vi", "en"), _load_vi_en_blocks()):
        keys = re.findall(r'^\s*"([a-zA-Z0-9_.]+)":', block, re.M)
        dupes = {k for k in keys if keys.count(k) > 1}
        assert not dupes, f"Duplicate keys in {lang} block: {sorted(dupes)}"
