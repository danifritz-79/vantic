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
REZEPTE_DIR = ROOT / "rezepte"
SITE_DIR = ROOT / "site"
DIST = ROOT / "dist"
SKILLS_OUT = DIST / "skills"  # Skills-Seite, skills.json und Downloads liegen unter /skills
REZEPTE_OUT = DIST / "rezepte"  # Rezepte-Seite und rezepte.json liegen unter /rezepte
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


TITEL_RE = re.compile(r"^#{1,2}\s+(.*\S)\s*$")
ANGABEN_RE = re.compile(r"^\*{0,2}(Für [^*]*[^*\s])\*{0,2}$", re.I)
TAGS_RE = re.compile(r"^(#[\wäöüÄÖÜéèà-]+)(\s+#[\wäöüÄÖÜéèà-]+)*$")
ABSCHNITT_RE = re.compile(r"^(?:\*\*(Zutaten|Zubereitung|Notiz|Notizen|Hinweis)\*\*|#{1,3}\s*(Zutaten|Zubereitung|Notiz|Notizen|Hinweis))\s*$", re.I)
KOMPONENTE_RE = re.compile(r"^\*\*(.+)\*\*$")
SCHRITT_RE = re.compile(r"^\d+\.\s+(.*)$")


def esc(text):
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def gruppen_zu_html(zeilen, geordnet):
    """Baut HTML aus Zeilen, die mit **Komponente**-Zwischentiteln gegliedert sind.
    geordnet=True: nummerierte Schritte (Zubereitung). geordnet=False: Zutatenliste."""
    html = []
    offen = False
    for raw in zeilen:
        zeile = raw.strip()
        if not zeile:
            continue
        m = KOMPONENTE_RE.match(zeile)
        if m and not SCHRITT_RE.match(zeile):
            if offen:
                html.append("</ol>" if geordnet else "</ul>")
                offen = False
            html.append(f"<h4>{esc(m.group(1))}</h4>")
            continue
        inhalt = zeile
        s = SCHRITT_RE.match(zeile)
        if s:
            inhalt = s.group(1)
        if not offen:
            html.append("<ol>" if geordnet else "<ul>")
            offen = True
        html.append(f"<li>{esc(inhalt)}</li>")
    if offen:
        html.append("</ol>" if geordnet else "</ul>")
    return "".join(html)


def parse_rezept(text):
    """Liest ein Rezept im Format des rezept-creator Skills (Titel, **Für X Personen**,
    optionale #hashtags, **Zutaten**/**Zubereitung**/**Notiz**, je mit **Komponente**-Titeln)."""
    titel = None
    angaben = ""
    tags = []
    abschnitt = None
    zutaten_zeilen, zubereitung_zeilen, notiz_zeilen = [], [], []
    for raw in text.replace("\r\n", "\n").split("\n"):
        zeile = raw.strip()
        if titel is None:
            m = TITEL_RE.match(zeile)
            if m:
                titel = m.group(1)
            continue
        if not zeile:
            continue
        m = TAGS_RE.match(zeile)
        if m:
            tags = [t.lstrip("#").lower() for t in zeile.split()]
            continue
        m = ABSCHNITT_RE.match(zeile)
        if m:
            name = (m.group(1) or m.group(2)).lower()
            abschnitt = "zutaten" if name == "zutaten" else ("zubereitung" if name == "zubereitung" else "notiz")
            continue
        m = ANGABEN_RE.match(zeile)
        if m and not angaben:
            angaben = m.group(1)
            continue
        if abschnitt is None:
            continue
        if abschnitt == "zutaten":
            zutaten_zeilen.append(zeile)
        elif abschnitt == "zubereitung":
            zubereitung_zeilen.append(zeile)
        else:
            notiz_zeilen.append(zeile)
    if not titel:
        return None
    return {
        "titel": titel,
        "angaben": angaben,
        "tags": tags,
        "zutaten_html": gruppen_zu_html(zutaten_zeilen, geordnet=False),
        "zubereitung_html": gruppen_zu_html(zubereitung_zeilen, geordnet=True),
        "notiz": " ".join(notiz_zeilen).strip(),
    }


def build_rezepte():
    rezepte = []
    if not REZEPTE_DIR.exists():
        return rezepte
    for datei in sorted(REZEPTE_DIR.glob("*.md")):
        rezept = parse_rezept(datei.read_text(encoding="utf-8"))
        if not rezept:
            warn(f"{datei.name}: Kein Titel gefunden (erste Zeile mit # oder ##). Datei wird übersprungen.")
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", rezept["titel"].lower()).strip("-") or datei.stem
        rezept["id"] = slug
        rezept["quelle"] = datei.name
        rezepte.append(rezept)
    return rezepte


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
    rezepte = build_rezepte()
    REZEPTE_OUT.mkdir(parents=True, exist_ok=True)
    (REZEPTE_OUT / "rezepte.json").write_text(
        json.dumps({"rezepte": rezepte}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Fertig: {len(skills)} Skill(s), {len(categories)} Kategorie(n), {len(rezepte)} Rezept(e) in {DIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
