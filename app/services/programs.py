"""Split canonical career mappings and attach exact-name program source links."""
import csv
from functools import lru_cache
from app.config import REFERENCE_DIR

@lru_cache(maxsize=1)
def _program_sources():
    # This registry supplies metadata only; it never generates pathway mappings.
    with (REFERENCE_DIR/'program_catalog.csv').open(encoding='utf-8-sig', newline='') as f:
        return {(r['kind'], r['name'].casefold()): r for r in csv.DictReader(f)}


def program_options(text, kind=None):
    sources = _program_sources() if kind else {}
    result=[]
    for name in dict.fromkeys(p.strip() for p in (text or '').split('|') if p.strip()):
        source=sources.get((kind,name.casefold()),{})
        result.append(dict(name=name,source_url=source.get('source_url',''),source_status=source.get('source_status','')))
    return result
