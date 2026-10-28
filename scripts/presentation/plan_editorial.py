"""Restore the approved nine-page graphical plan into its production workspace."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'projects/finals_editorial_ppt169_20261028'
P.mkdir(parents=True,exist_ok=True)
(P/'notes').mkdir(exist_ok=True)
for source,target in [('presentation-design-spec.md','design_spec.md'),('presentation-spec-lock.md','spec_lock.md'),('speaker-notes.md','notes/total.md')]:
    shutil.copy2(ROOT/'deliverables/source'/source,P/target)
print('Restored nine-page plan, notes, light canvas and static-motion contract.')
