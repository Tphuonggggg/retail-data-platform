"""Offline links, Python syntax and basic secret-pattern checks; no runtime connections."""
from pathlib import Path
import ast
import json
import re
import subprocess
import unicodedata
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

def anchors(text: str) -> set[str]:
    result = set(); counts = {}; fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith((chr(96)*3, "~~~")):
            fenced = not fenced; continue
        if fenced: continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
        if not match: continue
        title = re.sub(r"<[^>]*>", "", match[1])
        title = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", title)
        slug = "".join(c for c in title.lower() if c.isspace() or c in "_-" or unicodedata.category(c)[0] in "LN")
        slug = re.sub(r"\s", "-", slug); n = counts.get(slug, 0); counts[slug] = n+1
        result.add(slug if n == 0 else slug+"-"+str(n))
    return result

def main() -> int:
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    paths = sorted({ROOT/n for n in names if n and (ROOT/n).is_file()})
    # Power BI background/QA images are legitimate binary artifacts, not source text.
    image_signatures = {'.png': b'\x89PNG\r\n\x1a\n', '.jpg': b'\xff\xd8', '.jpeg': b'\xff\xd8'}
    binary_images = {p for p in paths if p.suffix.lower() in image_signatures}
    for p in binary_images:
        if not p.read_bytes().startswith(image_signatures[p.suffix.lower()]):
            raise ValueError('Invalid image signature: '+str(p.relative_to(ROOT)))
    texts = {p: p.read_text(encoding="utf-8-sig") for p in paths if p not in binary_images}
    headings = {p.resolve(): anchors(t) for p,t in texts.items() if p.suffix == ".md"}
    issues = []; links = 0; python = 0
    patterns = [r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", r"\bghp_[A-Za-z0-9]{30,}\b", r"(?i)(?:postgres(?:ql)?|mssql)://[^:\s/]+:[^@\s]+@"]
    for p,t in texts.items():
        if any(re.search(pattern,t) for pattern in patterns): issues.append([str(p.relative_to(ROOT)), "secret pattern"])
        if p.name == ".env" or p.suffix in {".key", ".pfx", ".bak", ".mdf", ".dump"}: issues.append([str(p.relative_to(ROOT)), "forbidden file"])
        if p.suffix == ".py": ast.parse(t, filename=str(p)); python += 1
        if p.suffix != ".md": continue
        for m in re.finditer(r"!?\[[^\]\n]*\]\(([^\s)]+)\)",t):
            target = unquote(m[1])
            if re.match(r"^[a-z]+:|^//",target,re.I): continue
            path,_,frag = target.partition("#"); dest = (p.parent/path).resolve() if path else p.resolve(); links += 1
            if not dest.exists() or (frag and dest.suffix == ".md" and frag not in headings.get(dest,set())):
                issues.append([str(p.relative_to(ROOT)),target])
    print(json.dumps({"files":len(paths),"links":links,"python_syntax":python,"issues":issues}))
    return int(bool(issues))

if __name__ == "__main__": raise SystemExit(main())
