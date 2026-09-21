"""Build a local source/data review package with a complete checksum manifest."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,zipfile
from .common import OUT,ROOT


def copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)


def assemble(destination):
    target=Path(destination);target.mkdir(parents=True,exist_ok=True)
    for source in sorted((ROOT/'validation/direction_a').glob('*.py')):copy(source,target/source.relative_to(ROOT))
    init=ROOT/'validation/__init__.py'
    if init.exists():copy(init,target/init.relative_to(ROOT))
    selected_dirs=['configs','results','figures','literature']
    for directory in selected_dirs:
        for source in sorted((OUT/directory).rglob('*')):
            if not source.is_file() or 'publisher_pages' in source.parts:continue
            # Bibliographic metadata and own reading notes are sufficient; no publisher full texts.
            if source.suffix.lower() in ('.html',):continue
            copy(source,target/source.relative_to(ROOT))
    for source in sorted(OUT.glob('*.md')):copy(source,target/source.relative_to(ROOT))
    for name in ['progress.json','metadata.json','baseline/manifest.json','environment/runtime.json','environment/requirements-lock.txt','environment/tectonic_source.json']:
        source=OUT/name
        if source.exists():copy(source,target/source.relative_to(ROOT))
    for source in sorted((OUT/'environment').glob('*.log')):copy(source,target/source.relative_to(ROOT))
    for source in sorted((OUT/'manuscript').iterdir()):
        if source.suffix in ('.tex','.bib','.pdf'):copy(source,target/source.relative_to(ROOT))
    for source in sorted((OUT/'reproduction').glob('*.json')):copy(source,target/source.relative_to(ROOT))
    # Retain the superseded scientific run and original builder without large response caches/previews.
    history=OUT/'superseded/v1_duration_0p9'
    for directory in ['results/main','results/sensitivity','results/analysis','configs','source']:
        for source in sorted((history/directory).rglob('*')):
            if source.is_file() and '__pycache__' not in source.parts:copy(source,target/source.relative_to(ROOT))
    diagnostic=ROOT/'paper/publication_speedrun/research/direct_path_rounding_diagnostic.json'
    copy(diagnostic,target/diagnostic.relative_to(ROOT))
    checklist=ROOT/'paper/publication_speedrun/DIRECTION_A_PREPRINT_TODO.md'
    copy(checklist,target/checklist.relative_to(ROOT))
    (target/'README.md').write_text('# Direction A: local author-review package\n\nStart with `paper/direction_a_preprint/AUTHOR_REVIEW.md` and the preprint/supplement PDFs under `paper/direction_a_preprint/manuscript/`.\n\nReproduction instructions: `paper/direction_a_preprint/REPRODUCING.md`. Final results are v2. The initial v1 run is retained separately with its failed joint-refinement evidence.\n\nAuthor: Aneesh Arnav Chikkala. No affiliation; self-funded. Server-neutral. Conflicts, scientific review, licensing and public release remain author decisions.\n\nSee `SHA256SUMS.json` for all packaged file checksums. Scientific dependencies, Tectonic binaries, response caches, historical recordings and publisher full texts are not redistributed.\n')
    (target/'LICENSE_STATUS.md').write_text('# License status\n\nNo distribution license has been selected for the manuscript, generated data or project code. This is a local review package, pending the author\'s public-release and licensing decisions.\n\nThird-party scientific dependencies and document tools are not redistributed. Install them from their official sources under their upstream licenses. Bibliographic records identify cited works; their publisher full texts are not included. No historical recordings are included.\n')
    # Make review links usable after extraction on another machine. Historical
    # workspace-only evidence is identified explicitly rather than linked falsely.
    link_pattern=re.compile(r'\[([^\]]+)\]\('+re.escape(str(ROOT))+r'/([^\)]+)\)')
    for document in sorted(target.rglob('*.md')):
        def portable(match):
            label,relative=match.groups();included=target/relative
            if included.exists():
                return '['+label+']('+os.path.relpath(included,document.parent)+')'
            if relative.endswith('release/Direction_A_Source_and_Data.zip'):
                return label+' (this extracted package)'
            return label+' (original-workspace artifact; not included in this package)'
        document.write_text(link_pattern.sub(portable,document.read_text()))
    manifest={str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
    (target/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'directory':str(target),'files':len(manifest),'bytes':sum(p.stat().st_size for p in target.rglob('*') if p.is_file())}),flush=True)
    return target


def archive(target):
    target=Path(target);destination=target.with_suffix('.zip')
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(target.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(target.parent))
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        manifest=json.loads((target/'SHA256SUMS.json').read_text())
        for name,digest in manifest.items():assert hashlib.sha256(z.read(target.name+'/'+name)).hexdigest()==digest
    print(json.dumps({'zip':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'verified_members':len(manifest)}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination');parser.add_argument('--zip',action='store_true');args=parser.parse_args()
    target=assemble(args.destination)
    if args.zip:archive(target)
