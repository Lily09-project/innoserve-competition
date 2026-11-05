"""Restore the approved twelve-page graphical plan into its production workspace."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / 'projects/finals_editorial_ppt169_20261028'
(P / 'notes').mkdir(parents=True, exist_ok=True)
for source, target in [('presentation-design-spec.md', 'design_spec.md'),
                       ('presentation-spec-lock.md', 'spec_lock.md'),
                       ('speaker-notes.md', 'notes/total.md')]:
    shutil.copy2(ROOT / 'deliverables/source' / source, P / target)

notes = (P / 'notes/total.md').read_text(encoding='utf-8')
sections = re.split(r'^# (\d{2}_slide)[ \t]*$', notes, flags=re.M)
if sections[1::2] != [f'{i:02d}_slide' for i in range(1, 13)]:
    raise ValueError('speaker_notes_roster_mismatch')
for stem, body in zip(sections[1::2], sections[2::2]):
    (P / 'notes' / f'{stem}.md').write_text(body.strip().removesuffix('---').rstrip()+'\n', encoding='utf-8')
print('Restored twelve-page plan, notes, light canvas and static-motion contract.')
