#!/usr/bin/env python3
"""Baut die Vantic-Webseite.

Liest jeden Ordner in skills/, erzeugt daraus je ein Zip zum Download und eine
Datei skills.json. Die Webseite (site/) baut ihre Karten aus dieser Datei.
Ergebnis liegt im Ordner dist/.

Aufruf: python3 scripts/build.py
"""
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
SITE_DIR = ROOT / "site"
DIST = ROOT / "dist"
SKILLS_OUT = DIST / "skills"  # Skills-Seite, skills.json und Downloads liegen unter /skills
IGNORE = {"site.json", ".DS_Store", "Thumbs.db"}


def warn(msg):
    # Erscheint im Protokoll von GitHub Actions als gelbe Warnung
    print(f"::warning::{msg}")


def parse_frontmatter(text):
    """Liest name und description aus dem Kopf einer SKILL.md (einzeilige Werte)."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
    if not m:
        return {}
    data = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def shorten(text, limit=150):
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def collect_files(folder):
    files = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.name not in IGNORE and not path.name.startswith("."):
            files.append(path.relative_to(folder).as_posix())
    return files


def build_skill(folder):
    skill_md = folder / "SKILL.md"
    if not skill_md.exists():
        return None

    fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    name = fm.get("name", "")
    if not name:
        warn(f"{folder.name}: In der SKILL.md fehlt 'name'. Skill wird übersprungen.")
        return None
    if name != folder.name:
        warn(f"{folder.name}: 'name' ({name}) muss dem Ordnernamen entsprechen. Skill wird übersprungen.")
        return None
    if not fm.get("description"):
        warn(f"{folder.name}: In der SKILL.md fehlt 'description'. Skill wird übersprungen.")
        return None

    meta = {}
    site_json = folder / "site.json"
    if site_json.exists():
        try:
            meta = json.loads(site_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            warn(f"{folder.name}: site.json ist kein gültiges JSON ({err}). Es werden Standardwerte genutzt.")
    else:
        warn(f"{folder.name}: site.json fehlt. Es werden Standardwerte genutzt.")

    files = collect_files(folder)

    # Zip: Der Ordner heisst im Zip wie der Skill, damit Claude ihn direkt erkennt.
    downloads = SKILLS_OUT / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    zip_path = downloads / f"{folder.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            zf.write(folder / rel, f"{folder.name}/{rel}")

    description = fm["description"]
    return {
        "id": folder.name,
        "titel": meta.get("titel") or folder.name.replace("-", " ").title(),
        "kategorie": meta.get("kategorie") or "Weitere Skills",
        "reihenfolge": meta.get("reihenfolge", 1000),
        "ebene": meta.get("ebene", ""),
        "kurzbeschreibung": meta.get("kurzbeschreibung") or shorten(description),
        "einleitung": meta.get("einleitung") or description,
        "punkte": meta.get("punkte", []),
        "du_gibst": meta.get("du_gibst", ""),
        "du_erhaeltst": meta.get("du_erhaeltst", ""),
        "beispielauftrag": meta.get("beispielauftrag", ""),
        "dateien": files,
        "zip": f"downloads/{folder.name}.zip",
        "groesse_kb": max(1, round(zip_path.stat().st_size / 1024)),
    }


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SITE_DIR, DIST)
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

    skills = []
    if SKILLS_DIR.exists():
        for folder in sorted(SKILLS_DIR.iterdir()):
            if folder.is_dir() and not folder.name.startswith("."):
                skill = build_skill(folder)
                if skill:
                    skills.append(skill)

    # Kategorien in der Reihenfolge ihres ersten Skills
    skills.sort(key=lambda s: (s["reihenfolge"], s["titel"]))
    categories = []
    for s in skills:
        if s["kategorie"] not in categories:
            categories.append(s["kategorie"])

    SKILLS_OUT.mkdir(parents=True, exist_ok=True)
    (SKILLS_OUT / "skills.json").write_text(
        json.dumps({"config": config, "kategorien": categories, "skills": skills}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Fertig: {len(skills)} Skill(s), {len(categories)} Kategorie(n) in {DIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
