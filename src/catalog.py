"""Allowlisted, edition-validated catalog extraction with stable chunk identities."""
import hashlib
import re
from bs4 import BeautifulSoup
import httpx
from src.config import URLS, YEAR


def split_text(text: str, size: int = 1000, overlap: int = 120) -> list[str]:
    if size <= overlap or overlap < 0:
        raise ValueError('Invalid chunk size/overlap')
    return [text[i:i + size] for i in range(0, len(text), size - overlap) if text[i:i + size].strip()]


def parse_html(html: str, url: str, year: str = YEAR) -> list[dict]:
    if url not in URLS or year != YEAR:
        raise ValueError('Source or catalog edition is not allowlisted')
    soup = BeautifulSoup(html, 'html.parser')
    # Do not silently mislabel a new catalog edition with the requested year.
    page_text = soup.get_text(' ', strip=True)
    if not re.search(r'2026\s*[-–—]\s*(?:2027|27)', page_text):
        raise ValueError('The fetched page does not establish the 2026–27 edition')
    root = soup.select_one('#content') or soup.select_one('main')
    if root is None:
        raise ValueError('Catalog content container missing')
    for node in root.select('script,style,nav,footer,.archive-message'):
        node.decompose()
    records = []
    blocks = root.select('.courseblock')
    if blocks:
        for block in blocks:
            title = block.select_one('.courseblocktitle')
            heading = (title or block).get_text(' ', strip=True).replace('\xa0', ' ')
            match = re.search(r'\b(CS|MATH)\s+(\d{3})\b', heading)
            if match:
                records.append((match[0], heading, block.get_text(' ', strip=True).replace('\xa0', ' ')))
    else:
        # Keep tables as text, headings and rows in document order.
        for section in root.select('[id$="textcontainer"]') or [root]:
            text = section.get_text('\n', strip=True)
            records.append((None, 'Computer Science BS requirements', text))
    chunks = []
    for code, heading, text in records:
        for order, content in enumerate(split_text(text)):
            # Repeat course identity on continuations to retain retrieval context.
            content = f'{heading}\n{content}' if order else content
            digest = hashlib.sha256(f'{year}|{url}|{code}|{order}|{content}'.encode()).hexdigest()
            chunks.append(dict(id=digest, course_code=code, heading=heading, content=content,
                               chunk_order=len(chunks), catalog_year=year, source_url=url))
    if not chunks:
        raise ValueError('No catalog records extracted')
    return chunks


def fetch_source(url: str) -> str:
    if url not in URLS:
        raise ValueError('Source is not allowlisted')
    with httpx.Client(timeout=25, follow_redirects=False, headers={'User-Agent': 'GYST-Catalog-Advisor/0.1 (educational catalog indexing)'}) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text
