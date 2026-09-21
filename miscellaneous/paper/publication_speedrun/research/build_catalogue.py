"""Build a local reading register from Crossref and a publisher-verified DOI census.

This creates planning artifacts only. It does not modify manuscript or experiment files.
"""
from pathlib import Path
import json, re, html, collections

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent
START, END = '2021-09-07', '2026-09-07'

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s or ''))).strip()

def online_date(x):
    dp = x.get('published-online', x.get('published', {})).get('date-parts', [[]])[0]
    return '-'.join(f'{v:04d}' if i == 0 else f'{v:02d}' for i, v in enumerate(dp))

raw = json.loads((ROOT / 'crossref_all.json').read_text())['message']['items']
volumes = json.loads((ROOT / 'publisher_volume_dois.json').read_text())
publisher = {f'10.1051/aacus/{suffix}': year for year, suffixes in volumes.items() for suffix in suffixes.split()}

patterns = {
    'Direction estimation / arrays': r'gcc|phat|tdoa|direction.of.arrival|time.delay estim|microphone array|beamform|acoustic source locali|sound source locali',
    'Room acoustics / reverberation': r'reverber|room acoustic|room impulse|image.source|diffuse reflection',
    'Numerical verification / benchmarks': r'benchmark|reproducib|numerical convergence|discretiz|discretis|finite difference|verification',
    'Uncertainty / calibration': r'uncertaint|calibrat|error propagation|sensitivity analy',
    'Hearing / spatial perception': r'binaural|psychoacoustic|hearing|hrtf|auditory|percept',
    'Software / efficient computation': r'computationally.efficient|open.source|software|real.time|computational cost',
}
notes_path = ROOT / 'reading_notes.json'
notes = json.loads(notes_path.read_text()) if notes_path.exists() else {}
receipt_path = ROOT / 'screening_receipt.json'
receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
exceptions = set(receipt.get('full_text_exceptions', []))
pdf_screened = set(receipt.get('pdf_screened_dois', []))
unresolved_publisher_dois = {'10.1051/aacus/2026090'}
items = []
for x in raw:
    date = online_date(x)
    if not START <= date <= END:
        continue
    doi = x['DOI']
    title, abstract = clean(x.get('title', [''])[0]), clean(x.get('abstract', ''))
    categories = [name for name, pattern in patterns.items() if re.search(pattern, title + ' ' + abstract, re.I)]
    record = {
        'doi': doi, 'title': title, 'online_date': date,
        'volume': x.get('volume', ''), 'article_number': x.get('page', ''),
        'publication_status': ('Published in volume' if doi in publisher else
                               'Unresolved publisher record / outside published-volume census' if doi in unresolved_publisher_dois else
                               'Forthcoming / outside published-volume census'),
        'authors': '; '.join(' '.join(filter(None, [a.get('given'), a.get('family')])) for a in x.get('author', [])),
        'abstract': abstract, 'tags': categories or ['Other acoustics'],
        'url': 'https://doi.org/' + doi,
        'publisher_url': x.get('resource', {}).get('primary', {}).get('URL', ''),
        'screening': 'Title and abstract screened' if abstract else 'Title / metadata screened; no Crossref abstract',
        'reading_note': notes.get(doi, {}).get('note', ''),
        'relevance': notes.get(doi, {}).get('relevance', 'Thematic screen'),
    }
    if doi in publisher and receipt.get('completed') and doi not in exceptions:
        record['screening'] += ('; all PDF pages text-extracted and keyword screened; DOI verified (HTML recovery)'
                                if doi in pdf_screened else '; full HTML retrieved and keyword screened')
    if doi in exceptions:
        record['screening'] += '; full HTML extraction exception'
    if notes.get(doi, {}).get('close_read'):
        record['screening'] += '; selected methods/results/discussion closely examined'
    items.append(record)
items.sort(key=lambda x: (x['publication_status'] != 'Published in volume', x['online_date'], x['doi']))
(ROOT / 'literature_register.json').write_text(json.dumps(items, ensure_ascii=False, indent=2))
published = [x for x in items if x['publication_status'] == 'Published in volume']
forthcoming = [x for x in items if x['publication_status'] != 'Published in volume']
summary = {
    'window': [START, END], 'publisher_volume_entries_2021_to_2026': len(publisher),
    'published_in_window': len(published), 'additional_index_records': len(forthcoming),
    'confirmed_forthcoming': sum(x['doi'] not in unresolved_publisher_dois for x in forthcoming),
    'unresolved_publisher_records': sorted(unresolved_publisher_dois),
    'published_with_abstract': sum(bool(x['abstract']) for x in published),
    'by_online_year': dict(sorted(collections.Counter(x['online_date'][:4] for x in published).items())),
    'tags_overlap': dict(collections.Counter(t for x in published for t in x['tags'])),
    'full_text_screened': len(published)-len(exceptions) if receipt.get('completed') else 0,
    'html_screened': len(published)-len(exceptions)-len(pdf_screened) if receipt.get('completed') else 0,
    'pdf_screened': len(pdf_screened),
    'close_read_items': sum(bool(notes.get(x['doi'], {}).get('close_read')) for x in items),
    'records_with_project_notes': sum(bool(x['reading_note']) for x in items),
}
(ROOT / 'corpus_summary.json').write_text(json.dumps(summary, indent=2))

intro = f'''# Acta Acustica reading register

Review window: **7 September 2021–7 September 2026**, inclusive, using online publication dates.

The publisher lists **{len(publisher)} items** across the six intersecting annual volumes; **{len(published)} fall in the window**. Crossref adds **{len(forthcoming)} records outside that census**, retained separately: 12 are publisher-confirmed forthcoming articles; DOI 10.1051/aacus/2026090 returns a publisher “Content not found” page and remains unresolved. Crossref year-only publication filters initially mixed these groups; the publisher census controls the published set.

Each record below contains the publisher-deposited abstract where available and its DOI. Topic tags are rule-based screening aids. They are not judgments of study quality or proof of novelty. Full-text retrieval and keyword screening is distinguished from close examination of selected sections. The separate publication plan supplies the substantive synthesis.

Final screening: {summary['full_text_screened']} published full texts ({summary['html_screened']} HTML, {summary['pdf_screened']} PDF); selected sections closely examined for {summary['close_read_items']} items; project notes on {summary['records_with_project_notes']} records. See COVERAGE_AND_METHOD.md for scope and limitations.

Source index: https://acta-acustica.edpsciences.org/component/issues/?task=all&Itemid=121

Crossref: https://api.crossref.org/journals/2681-4617/works

'''
parts = [intro]
for status, records in [('Published items', published), ('Forthcoming and unresolved records — separate from the published count', forthcoming)]:
    parts.append('## ' + status + '\n')
    for x in records:
        parts.append(f"### {x['online_date']} — {x['title']}\n\n{x['authors']}\n\n[{x['doi']}]({x['url']}) · Volume {x['volume']}, article {x['article_number']}\n\n**Screening:** {x['screening']}.\n\n**Topics:** {'; '.join(x['tags'])}.\n\n{x['abstract'] or 'No abstract deposited in Crossref.'}\n")
        if x['reading_note']:
            parts.append('**Use in this project:** ' + x['reading_note'] + '\n')
(OUT / 'LITERATURE_REGISTER.md').write_text('\n'.join(parts))

data = json.dumps(items, ensure_ascii=False).replace('</', '<\\/')
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Acta Acustica reading register</title>
<style>:root{color-scheme:light;--ink:#183237;--muted:#51696c;--line:#cddad9;--accent:#176d68}*{box-sizing:border-box}body{margin:0;background:#f5f7f4;color:var(--ink);font:16px/1.65 system-ui,sans-serif}header,main{max-width:1180px;margin:auto;padding:32px}header{padding-bottom:18px}h1{font-size:36px;letter-spacing:-1px;margin:10px 0}h2{font-size:20px;line-height:1.4;margin:8px 0}p{margin:8px 0}.intro{max-width:930px;color:var(--muted)}.controls{display:grid;grid-template-columns:2fr 1fr 1.1fr;gap:12px;margin:22px 0 12px}input,select{min-width:0;border:1px solid var(--line);border-radius:6px;background:white;padding:12px;font:inherit}article{background:white;border:1px solid var(--line);padding:23px;margin:0 0 16px;border-radius:8px}.meta{font-size:14px;color:var(--muted)}a{color:var(--accent)}details{margin-top:12px}summary{cursor:pointer;color:var(--accent)}.note{border-left:3px solid var(--accent);padding-left:14px}.tag{display:inline-block;font-size:12px;margin:3px 6px 0 0;padding:2px 8px;background:#eaf2ee;border-radius:4px}.count{font-weight:600;margin:12px 0}label span{display:block;font-size:13px;margin-bottom:4px}label input,label select{width:100%}@media(max-width:740px){header,main{padding:18px}.controls{grid-template-columns:1fr}h1{font-size:28px}}</style>
<header><p class="meta">7 September 2021–7 September 2026</p><h1>Acta Acustica reading register</h1><p class="intro">398 published items, checked against all six annual volumes. Thirteen additional records are retained separately: twelve confirmed forthcoming and one unresolved publisher record. Search titles, authors, abstracts, and project notes. Topic tags assist screening; they do not establish novelty or study quality.</p><p class="intro">All 398 published full texts were screened: 380 HTML and 18 PDF. Selected sections of 16 items were examined more closely. Every entry states its review level. The publication plan contains the scientific audit and recommended work.</p><p><a href="PUBLICATION_SPEEDRUN_PLAN.md">Publication plan</a> · <a href="LITERATURE_REGISTER.md">Complete text register</a> · <a href="COVERAGE_AND_METHOD.md">Coverage and method</a> · <a href="https://acta-acustica.edpsciences.org/component/issues/?task=all&Itemid=121">Publisher archive</a></p><div class="controls"><label><span>Search</span><input id="search" placeholder="GCC-PHAT, bias, calibration…"></label><label><span id="year-label">Online year</span><select id="year" aria-labelledby="year-label"><option value="">All years</option></select></label><label><span id="status-label">Publication status</span><select id="status" aria-labelledby="status-label"><option value="Published in volume">Published items</option><option value="all">All records</option><option value="forthcoming">Forthcoming / unresolved</option><option value="notes">Project reading notes</option></select></label></div><p id="count" class="count" aria-live="polite"></p></header><main id="results"></main>
<script>const papers=DATA;const $=s=>document.querySelector(s);const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));for(const y of [...new Set(papers.map(p=>p.online_date.slice(0,4)))].sort().reverse())$('#year').insertAdjacentHTML('beforeend',`<option>${y}</option>`);function render(){const q=$('#search').value.toLowerCase().trim(),year=$('#year').value,mode=$('#status').value;const rows=papers.filter(p=>(!year||p.online_date.startsWith(year))&&(!q||[p.title,p.authors,p.abstract,p.reading_note,p.doi,...p.tags].join(' ').toLowerCase().includes(q))&&(mode==='all'||(mode==='notes'?p.reading_note:mode==='forthcoming'?p.publication_status!=='Published in volume':p.publication_status===mode)));$('#count').textContent=`${rows.length} ${rows.length===1?'entry':'entries'}`;$('#results').innerHTML=rows.map(p=>`<article><p class="meta">${esc(p.online_date)} · ${esc(p.publication_status)} · Volume ${esc(p.volume)}, article ${esc(p.article_number)}</p><h2><a href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">${esc(p.title)}</a></h2><p class="meta">${esc(p.authors)}</p><p>${p.tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</p>${p.reading_note?`<p class="note">${esc(p.reading_note)}</p>`:''}<details><summary>Abstract and review coverage</summary><p>${esc(p.abstract||'No abstract deposited in Crossref.')}</p><p class="meta">${esc(p.screening)}.</p><p class="meta">${esc(p.doi)}</p></details></article>`).join('')||'<p>No entries match these filters.</p>';}for(const e of document.querySelectorAll('input,select'))e.addEventListener('input',render);render();</script></html>'''.replace('DATA', data)
(OUT / 'READING_REGISTER.html').write_text(page)
print(json.dumps(summary, indent=2))
