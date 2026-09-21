"""Screen publisher PDFs downloaded through the journal's visible archive links."""
from pathlib import Path
import hashlib
import json
import shutil
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
PDFS = ROOT / 'publisher_pdfs'
TEXTS = ROOT / 'publisher_pdf_text'
PDFS.mkdir(exist_ok=True)
TEXTS.mkdir(exist_ok=True)
mapping = {
    '2026004': 'aacus250087', '2026042': 'aacus260048',
    '2025018': 'aacus240123', '2025020': 'aacus240106',
    '2025010': 'aacus240125', '2025030': 'aacus240143',
    '2024070': 'aacus240089', '2024023': 'aacus230083',
    '2024019': 'aacus230106', '2023018': 'aacus220077',
    '2023022': 'aacus220092', '2023045': 'aacus230050',
    '2023058': 'aacus220108', '2023034': 'aacus230023',
    '2022041': 'aacus220017', '2022046': 'aacus220051',
    '2021038': 'aacus210048', '2021049': 'aacus210076',
}
items = []
for suffix, stem in mapping.items():
    doi = '10.1051/aacus/' + suffix
    destination = PDFS / (stem + '.pdf')
    if not destination.exists():
        source = Path('/home/ani/Downloads') / destination.name
        # Only these exact, newly downloaded task files are organized here.
        shutil.move(str(source), str(destination))
    reader = PdfReader(destination)
    pages = [p.extract_text() or '' for p in reader.pages]
    if any(len(p.strip()) < 30 for p in pages):
        raise ValueError(f'Empty text page in {doi}')
    text = '\n\n'.join(f'--- PDF page {i+1} ---\n{p}' for i, p in enumerate(pages))
    if doi not in ''.join(text.split()):
        raise ValueError(f'DOI not found in downloaded PDF: {doi}')
    text_path = TEXTS / (suffix + '.txt')
    text_path.write_text(text)
    items.append({
        'doi': doi, 'pdf': str(destination), 'text': str(text_path),
        'pages': len(pages), 'chars': len(text),
        'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'screening': 'All PDF pages text-extracted and keyword screened; DOI verified',
        'terms': [s for s in ['GCC', 'PHAT', 'TDOA', 'microphone array', 'benchmark',
                             'fractional', 'bias', 'simulation', 'reverberation', 'uncertainty']
                  if s.lower() in text.lower()],
    })
(ROOT / 'pdf_screening_receipt.json').write_text(json.dumps(items, indent=2))
print(json.dumps([{'doi':x['doi'], 'pages':x['pages'], 'chars':x['chars'], 'terms':x['terms']}
                  for x in items], indent=2))
