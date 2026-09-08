"""Evidence-backed task completion and progress records."""
import argparse
import datetime
import json
from pathlib import Path
from .common import OUT, ROOT


def complete(task, artifacts, check):
    for artifact in artifacts:
        if not (ROOT / artifact).exists():
            raise FileNotFoundError(artifact)
    path = OUT/'progress.json'
    progress = json.loads(path.read_text()) if path.exists() else {'completed': {}, 'active_stage': 'G1'}
    progress['completed'][task] = {
        'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'artifacts': artifacts, 'verification': check,
    }
    path.write_text(json.dumps(progress, indent=2)+'\n')
    lines=['# Direction A execution log', '', 'Only evidence-backed completed tasks appear here.', '']
    for name, item in sorted(progress['completed'].items()):
        lines += [f'**{name} — {item["completed_utc"]}**', '', item['verification'], '']
        lines += [f'- [{Path(p).name}]({ROOT/p})' for p in item['artifacts']]
        lines += ['']
    (OUT/'EXECUTION_LOG.md').write_text('\n'.join(lines))
    todo=ROOT/'paper/publication_speedrun/DIRECTION_A_PREPRINT_TODO.md'
    text=todo.read_text().replace(f'- [ ] **{task} —', f'- [x] **{task} —')
    text=text.replace('The checklist is prepared; research execution is pending. All research tasks remain unchecked.',
                      'Research execution is underway. Completion evidence is recorded in the [execution log](/home/ani/Desktop/sound_local/paper/direction_a_preprint/EXECUTION_LOG.md).')
    todo.write_text(text)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('task');p.add_argument('--artifact',action='append',required=True);p.add_argument('--check',required=True)
    a=p.parse_args();complete(a.task,a.artifact,a.check)
