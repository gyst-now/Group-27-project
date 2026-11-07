import pytest
from src.catalog import parse_html, split_text
from src.config import URLS
HTML = '<main><h1>2026-2027 Catalog</h1><div class="courseblock"><p class="courseblocktitle">CS 225 Data Structures 4 hours.</p><p>Prerequisite: CS 128 and CS 173.</p></div></main>'
def test_course_and_provenance():
    chunks = parse_html(HTML, URLS[0])
    assert chunks[0]['course_code']=='CS 225'
    assert 'CS 173' in chunks[0]['content']
    assert chunks==parse_html(HTML,URLS[0])
    assert chunks[0]['source_url']==URLS[0]
def test_reject_wrong_edition_and_host():
    with pytest.raises(ValueError): parse_html(HTML.replace('2026-2027','2025-2026'),URLS[0])
    with pytest.raises(ValueError): parse_html(HTML,'https://evil.example/')
def test_long_course_keeps_identity():
    chunks=parse_html(HTML.replace('Prerequisite:', 'x'*3000+'Prerequisite:'),URLS[0])
    assert len(chunks)>1
    assert all('CS 225' in c['content'] for c in chunks)
def test_split_bounds():
    with pytest.raises(ValueError): split_text('hello',100,120)
