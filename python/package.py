"""Assemble portable bundle, excluding hosting identity and Git history."""
import pathlib,zipfile
r=pathlib.Path(__file__).resolve().parents[1];target=r/'dist/downloads/project.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(r.rglob('*')):
  if p.is_file() and p!=target and not any(part.startswith('.') for part in p.relative_to(r).parts[:-1]) and '__pycache__' not in p.parts and p.suffix!='.tar':z.write(p,p.relative_to(r))
print(f'{target}: {target.stat().st_size:,} bytes')
