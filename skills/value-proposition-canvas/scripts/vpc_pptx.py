#!/usr/bin/env python3
"""Erzeugt PowerPoint-Folien zum Value Proposition Canvas.

Aufruf:
    python3 vpc_pptx.py --leer Ausgabe.pptx                leeres Template zum Ausdrucken
    python3 vpc_pptx.py daten.json --kunde Ausgabe.pptx    Zwischenresultat: Kundenprofil in drei Säulen
    python3 vpc_pptx.py daten.json Ausgabe.pptx            alle Resultate: Titel, Kundenprofil, Value Map,
                                                           Canvas, Übereinstimmung (sobald erfasst)

Benötigt python-pptx (pip install python-pptx).

Value Proposition Canvas nach Osterwalder, Pigneur, Bernarda und Smith, Value Proposition Design (2014), Strategyzer.
"""
import json
import math
import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt
except ImportError:
    sys.exit("python-pptx fehlt. Installieren mit: pip install python-pptx")

ANTHRAZIT = RGBColor(0x33, 0x38, 0x3D)
GRUEN = RGBColor(0x0F, 0x3D, 0x2E)
GOLD = RGBColor(0xE2, 0xB0, 0x4A)
GOLD_TIEF = RGBColor(0xA8, 0x7A, 0x0A)
GRUND = RGBColor(0xF2, 0xF3, 0xEC)
TINTE = RGBColor(0x14, 0x23, 0x1C)
GEDAEMPFT = RGBColor(0x3F, 0x4B, 0x44)
LINIE = RGBColor(0xD2, 0xD9, 0xCF)
WEISS = RGBColor(0xFF, 0xFF, 0xFF)
ROT = RGBColor(0xB4, 0x3C, 0x2E)
SCHRIFT = "Arial"
SYMBOL = "Segoe UI Symbol"
QUELLE = "Value Proposition Canvas nach Osterwalder, Pigneur, Bernarda und Smith, Value Proposition Design (Strategyzer)"
LOGO = Path(__file__).resolve().parent.parent / "assets" / "vantic-logo-liegend.png"

# Gewichtungsstufen pro Kategorie, von hoch nach tief
STUFEN = {
    "aufgaben": ["wichtig", "mittel", "unbedeutend"],
    "probleme": ["gravierend", "mittel", "gering"],
    "gewinne": ["unverzichtbar", "erwünscht", "nice to have"],
}
KUNDE = [
    ("aufgaben", "Kundenaufgaben", "Was Kunden in ihrer Arbeit und ihrem Alltag erledigen möchten", GRUEN),
    ("probleme", "Probleme", "Schlechte Ergebnisse, Risiken und Hindernisse rund um die Aufgaben", ANTHRAZIT),
    ("gewinne", "Gewinne", "Resultate, die Kunden erzielen wollen, und Vorteile, die sie suchen", GOLD),
]
WERT = [
    ("produkte", "Produkte und Dienstleistungen", "Worum sich das Wertangebot dreht", GRUEN),
    ("problemloeser", "Problemlöser", "Wie das Angebot Probleme der Kunden löst", ANTHRAZIT),
    ("gewinnerzeuger", "Gewinnerzeuger", "Wie das Angebot Gewinne für die Kunden erzeugt", GOLD),
]


def mische(farbe, anteil):
    return RGBColor(*[round(255 - (255 - c) * anteil) for c in farbe])


def text_von(eintrag):
    return eintrag if isinstance(eintrag, str) else eintrag.get("text", "")


def sortiert(daten, key):
    """Einträge nach Gewichtung sortieren, Reihenfolge innerhalb einer Stufe bleibt."""
    eintraege = daten.get(key, [])
    stufen = STUFEN.get(key)
    if not stufen:
        return eintraege
    def rang(e):
        g = e.get("gewicht") if isinstance(e, dict) else None
        return stufen.index(g) if g in stufen else len(stufen)
    return sorted(eintraege, key=rang)


# ---------- Bausteine ----------

def neue_folie(prs):
    f = prs.slides.add_slide(prs.slide_layouts[6])
    flaeche(f, 0, 0, prs.slide_width, prs.slide_height, GRUND)
    return f


def flaeche(folie, x, y, b, h, farbe, form=MSO_SHAPE.RECTANGLE, linie=None, staerke=1.0):
    s = folie.shapes.add_shape(form, x, y, b, h)
    if farbe is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = farbe
    if linie is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = linie
        s.line.width = Pt(staerke)
    s.shadow.inherit = False
    return s


def textfeld(folie, x, y, b, h, absaetze, anker=MSO_ANCHOR.TOP):
    """absaetze: dict(text, groesse, farbe, fett, kursiv, abstand, ausrichtung, laeufe)."""
    tb = folie.shapes.add_textbox(x, y, b, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anker
    for seite in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, seite, Emu(0))
    for i, a in enumerate(absaetze):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = a.get("ausrichtung", PP_ALIGN.LEFT)
        p.space_before = Pt(a.get("abstand", 0))
        for lauf in a.get("laeufe", [a]):
            r = p.add_run()
            r.text = lauf["text"]
            f = r.font
            f.name = lauf.get("schrift", SCHRIFT)
            f.size = Pt(lauf.get("groesse", a.get("groesse", 12)))
            f.bold = lauf.get("fett", a.get("fett", False))
            f.italic = lauf.get("kursiv", a.get("kursiv", False))
            f.color.rgb = lauf.get("farbe", a.get("farbe", TINTE))
    return tb


def linie(folie, x1, y1, x2, y2, farbe=TINTE, staerke=1.5):
    c = folie.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = farbe
    c.line.width = Pt(staerke)
    return c


def kopf(folie, titel, untertitel, prs):
    textfeld(folie, Inches(0.5), Inches(0.3), Inches(10.2), Inches(0.9), [
        {"text": titel, "groesse": 22, "fett": True},
        {"text": untertitel, "groesse": 11, "farbe": GEDAEMPFT, "abstand": 3},
    ])
    if LOGO.exists():
        folie.shapes.add_picture(str(LOGO), Inches(10.95), Inches(0.36), height=Inches(0.5))


def fuss(folie, prs, zusatz="", datum=""):
    zusatz = "    ".join(t for t in (datum, zusatz) if t)
    textfeld(folie, Inches(0.5), prs.slide_height - Inches(0.4), Inches(12.3), Inches(0.3), [
        {"text": (zusatz + "    " if zusatz else "") + QUELLE + "  ·  vantic.ch", "groesse": 8.5,
         "farbe": GEDAEMPFT},
    ])


def groesse_fuer(texte, breite_zoll, hoehe_zoll, start=12, minimum=7.5):
    g = start
    while g > minimum:
        zeichen = max(8, int(breite_zoll * 72 / (g * 0.5)))
        zeilen = sum(max(1, -(-len(t) // zeichen)) for t in texte)
        if zeilen * g * 1.25 + len(texte) * 2 <= hoehe_zoll * 72:
            return g
        g -= 0.5
    return minimum


def untertitel(daten):
    teile = [daten.get("kundensegment") and f"Kundensegment: {daten['kundensegment']}",
             daten.get("wertangebot") and f"Wertangebot: {daten['wertangebot']}"]
    return "  ·  ".join(t for t in teile if t)


# ---------- Folie: drei Säulen ----------

def saeulen_folie(prs, daten, spalten, titel, hinweis, mit_gewicht):
    folie = neue_folie(prs)
    kopf(folie, titel, untertitel(daten), prs)
    links, oben, luecke = Inches(0.5), Inches(1.45), Inches(0.15)
    b = int((Inches(12.33) - 2 * luecke) / 3)
    h_gesamt = Inches(5.45)
    for s, (key, name, erklaerung, farbe) in enumerate(spalten):
        x = links + s * (b + luecke)
        flaeche(folie, x, oben, b, Inches(0.95), farbe)
        schrift = TINTE if farbe == GOLD else WEISS
        textfeld(folie, x + Inches(0.2), oben + Inches(0.12), b - Inches(0.4), Inches(0.8), [
            {"text": name, "groesse": 16, "fett": True, "farbe": schrift},
            {"text": erklaerung, "groesse": 9.5, "farbe": schrift, "abstand": 2},
        ])
        eintraege = sortiert(daten, key) if mit_gewicht else daten.get(key, [])
        y = oben + Inches(1.05)
        verfuegbar = h_gesamt - Inches(1.05)
        stufen = STUFEN.get(key) if mit_gewicht else None
        bar_b = Inches(0.32) if stufen else 0
        if stufen:
            # Skala von hoch nach tief
            schritte = 12
            for k in range(schritte):
                flaeche(folie, x, y + int(verfuegbar * k / schritte), bar_b, int(verfuegbar / schritte) + 1,
                        mische(farbe, 1 - 0.85 * k / (schritte - 1)))
            laenge = int(verfuegbar / 2)
            for txt, mitte, ausr, f in ((stufen[0], y + verfuegbar // 4, PP_ALIGN.RIGHT,
                                         TINTE if farbe == GOLD else WEISS),
                                        (stufen[-1], y + 3 * verfuegbar // 4, PP_ALIGN.LEFT, TINTE)):
                tb = textfeld(folie, x + bar_b // 2 - laenge // 2, mitte - bar_b // 2, laenge, bar_b, [
                    {"text": txt, "groesse": 8, "fett": True, "farbe": f, "ausrichtung": ausr}],
                    anker=MSO_ANCHOR.MIDDLE)
                tb.text_frame.margin_left = tb.text_frame.margin_right = Inches(0.08)
                tb.rotation = 270
        karte_x = x + bar_b + (Inches(0.1) if stufen else 0)
        karte_b = b - bar_b - (Inches(0.1) if stufen else 0)
        if not eintraege:
            textfeld(folie, karte_x, y, karte_b, Inches(0.5), [
                {"text": "noch keine Einträge", "groesse": 10, "kursiv": True, "farbe": GEDAEMPFT}])
            continue
        n = len(eintraege)
        luecke_k = Inches(0.06)
        hk = min(Inches(0.62), int((verfuegbar - luecke_k * (n - 1)) / n))
        g = groesse_fuer([text_von(e) for e in eintraege], (karte_b - Inches(1.3)) / 914400,
                         (hk * n) / 914400, start=11, minimum=7)
        for i, e in enumerate(eintraege):
            yk = y + i * (hk + luecke_k)
            gewicht = e.get("gewicht") if isinstance(e, dict) else None
            stufe = stufen.index(gewicht) if stufen and gewicht in stufen else None
            hg = WEISS if stufe is None else mische(farbe, [0.22, 0.11, 0.0][stufe])
            flaeche(folie, karte_x, yk, karte_b, hk, hg, linie=LINIE)
            absatz = [{"text": text_von(e), "groesse": g}]
            textfeld(folie, karte_x + Inches(0.12), yk, karte_b - Inches(1.35 if stufen else 0.24), hk,
                     absatz, anker=MSO_ANCHOR.MIDDLE)
            if stufen:
                textfeld(folie, karte_x + karte_b - Inches(1.2), yk, Inches(1.1), hk, [
                    {"text": gewicht or "offen", "groesse": 8.5, "fett": stufe == 0,
                     "farbe": GEDAEMPFT, "ausrichtung": PP_ALIGN.RIGHT}], anker=MSO_ANCHOR.MIDDLE)
    fuss(folie, prs, hinweis, daten.get("datum", ""))


# ---------- Folie: Canvas ----------

def canvas_folie(prs, daten, leer):
    folie = neue_folie(prs)
    kopf(folie, "Value Proposition Canvas", untertitel(daten) if not leer else
         "Kundensegment: ...............................................   Wertangebot: ...............................................",
         prs)
    I = Inches
    # Value Map: Quadrat links
    qx, qy, qs = I(0.6), I(1.45), I(5.45)
    flaeche(folie, qx, qy, qs, qs, WEISS, linie=TINTE, staerke=2)
    innen_x, mitte_y = qx + int(qs * 0.56), qy + qs // 2
    linie(folie, qx, qy, innen_x, mitte_y)
    linie(folie, qx, qy + qs, innen_x, mitte_y)
    linie(folie, innen_x, mitte_y, qx + qs, mitte_y)
    # Kundenprofil: Kreis rechts
    r = I(2.72)
    kx, ky = I(13.333 - 0.6) - r, qy + qs // 2
    flaeche(folie, kx - r, ky - r, 2 * r, 2 * r, WEISS, form=MSO_SHAPE.OVAL, linie=TINTE, staerke=2)
    kopf_r = I(0.42)
    linie(folie, kx - r, ky, kx - kopf_r, ky)
    for wink in (55, -55):
        cx, cy = math.cos(math.radians(wink)), -math.sin(math.radians(wink))
        linie(folie, kx + int(kopf_r * cx), ky + int(kopf_r * cy), kx + int(r * cx), ky + int(r * cy))
    flaeche(folie, kx - kopf_r, ky - kopf_r, 2 * kopf_r, 2 * kopf_r, WEISS, form=MSO_SHAPE.OVAL,
            linie=TINTE, staerke=1.5)
    textfeld(folie, kx - kopf_r, ky - kopf_r, 2 * kopf_r, 2 * kopf_r, [
        {"text": "Kunde", "groesse": 8, "fett": True, "ausrichtung": PP_ALIGN.CENTER}], anker=MSO_ANCHOR.MIDDLE)
    # Übereinstimmung in der Mitte
    fd = I(1.12)
    fx = (qx + qs + kx - r) // 2
    linie(folie, qx + qs, mitte_y, kx - r, ky, farbe=GOLD_TIEF, staerke=1.5)
    flaeche(folie, fx - fd // 2, ky - fd // 2, fd, fd, GOLD, form=MSO_SHAPE.OVAL)
    textfeld(folie, fx - fd // 2, ky - fd // 2, fd, fd, [
        {"text": "Überein-", "groesse": 9.5, "fett": True, "ausrichtung": PP_ALIGN.CENTER},
        {"text": "stimmung", "groesse": 9.5, "fett": True, "ausrichtung": PP_ALIGN.CENTER}],
        anker=MSO_ANCHOR.MIDDLE)
    # Bereichstitel
    textfeld(folie, qx, qy - I(0.32), qs, I(0.3), [
        {"text": "VALUE MAP", "groesse": 10, "fett": True, "farbe": GEDAEMPFT}])
    textfeld(folie, kx - r, qy - I(0.32), 2 * r, I(0.3), [
        {"text": "KUNDENPROFIL", "groesse": 10, "fett": True, "farbe": GEDAEMPFT, "ausrichtung": PP_ALIGN.RIGHT}])

    # Felder: (Schlüssel, Titel, Leitsatz, x, y, b, h, Farbe, Ausrichtung)
    felder = [
        ("produkte", "Produkte und Dienstleistungen", "Worum dreht sich das Wertangebot?",
         qx + I(0.12), qy + I(1.7), I(1.75), I(2.05), GRUEN, PP_ALIGN.LEFT),
        ("gewinnerzeuger", "Gewinnerzeuger", "Wie erzeugt das Angebot Gewinne?",
         qx + I(3.0), qy + I(0.15), I(2.35), I(2.45), GOLD_TIEF, PP_ALIGN.LEFT),
        ("problemloeser", "Problemlöser", "Wie löst das Angebot Probleme?",
         qx + I(3.0), mitte_y + I(0.15), I(2.35), I(2.45), ANTHRAZIT, PP_ALIGN.LEFT),
        ("gewinne", "Gewinne", "Welche Resultate und Vorteile suchen Kunden?",
         kx - I(1.95), ky - I(2.1), I(2.3), I(1.6), GOLD_TIEF, PP_ALIGN.CENTER),
        ("probleme", "Probleme", "Was ärgert, behindert oder gefährdet Kunden?",
         kx - I(1.95), ky + I(0.55), I(2.3), I(1.65), ANTHRAZIT, PP_ALIGN.CENTER),
        ("aufgaben", "Kundenaufgaben", "Was wollen Kunden erledigen?",
         kx + I(0.78), ky - I(1.0), I(1.72), I(2.0), GRUEN, PP_ALIGN.CENTER),
    ]
    for key, titel, leitsatz, x, y, b, h, farbe, ausr in felder:
        absaetze = [{"text": titel, "groesse": 11.5, "fett": True, "farbe": farbe, "ausrichtung": ausr}]
        if leer:
            absaetze.append({"text": leitsatz, "groesse": 9, "kursiv": True, "farbe": GEDAEMPFT,
                             "ausrichtung": ausr, "abstand": 2})
        else:
            eintraege = sortiert(daten, key)
            maximal = 6 if key in ("produkte", "gewinnerzeuger", "problemloeser") else 4
            texte = [text_von(e) for e in eintraege[:maximal]]
            g = groesse_fuer(texte, b / 914400, (h - I(0.3)) / 914400, start=10, minimum=8)
            absaetze += [{"text": ("" if ausr == PP_ALIGN.CENTER else "•  ") + t, "groesse": g,
                          "ausrichtung": ausr, "abstand": 2} for t in texte]
            if len(eintraege) > maximal:
                absaetze.append({"text": f"und {len(eintraege) - maximal} weitere", "groesse": 7.5,
                                 "kursiv": True, "farbe": GEDAEMPFT, "ausrichtung": ausr, "abstand": 2})
        textfeld(folie, x, y, b, h, absaetze)
    fuss(folie, prs, "Im Kreis die wichtigsten Einträge, alle auf den Säulen-Folien."
         if not leer else "Zuerst das Kundenprofil rechts ausfüllen, dann die Value Map links.", daten.get("datum", ""))


# ---------- Folie: Übereinstimmung ----------

def fit_folie(prs, daten):
    folie = neue_folie(prs)
    kopf(folie, "Übereinstimmung", untertitel(daten), prs)
    links, oben, luecke = Inches(0.5), Inches(1.45), Inches(0.15)
    b = int((Inches(12.33) - 2 * luecke) / 3)
    gesamt = abgedeckt = 0
    hoch_offen = []
    for s, (key, name, _, farbe) in enumerate(KUNDE):
        eintraege = sortiert(daten, key)
        x = links + s * (b + luecke)
        n_ok = sum(1 for e in eintraege if isinstance(e, dict) and e.get("abgedeckt") is True)
        gesamt += len(eintraege)
        abgedeckt += n_ok
        flaeche(folie, x, oben, b, Inches(0.62), farbe)
        schrift = TINTE if farbe == GOLD else WEISS
        textfeld(folie, x + Inches(0.2), oben, b - Inches(0.4), Inches(0.62), [
            {"laeufe": [{"text": name, "groesse": 15, "fett": True, "farbe": schrift},
                        {"text": f"   {n_ok} von {len(eintraege)} berücksichtigt", "groesse": 10,
                         "farbe": schrift}]}], anker=MSO_ANCHOR.MIDDLE)
        y = oben + Inches(0.72)
        verfuegbar = Inches(3.95)
        n = max(1, len(eintraege))
        hk = min(Inches(0.62), int((verfuegbar - Inches(0.05) * (n - 1)) / n))
        stufen = STUFEN[key]
        for i, e in enumerate(eintraege):
            yk = y + i * (hk + Inches(0.05))
            ok = isinstance(e, dict) and e.get("abgedeckt") is True
            offen = not isinstance(e, dict) or e.get("abgedeckt") is None
            gewicht = e.get("gewicht") if isinstance(e, dict) else None
            if not ok and not offen and gewicht == stufen[0]:
                hoch_offen.append(text_von(e))
            flaeche(folie, x, yk, b, hk, WEISS, linie=LINIE)
            zeichen, zfarbe = ("?", GEDAEMPFT) if offen else (("✓", GRUEN) if ok else ("✗", ROT))
            textfeld(folie, x + Inches(0.08), yk, Inches(0.4), hk, [
                {"text": zeichen, "schrift": SYMBOL, "groesse": 17, "fett": True, "farbe": zfarbe,
                 "ausrichtung": PP_ALIGN.CENTER, "laeufe": [{"text": zeichen, "schrift": SYMBOL, "groesse": 17,
                                                             "fett": True, "farbe": zfarbe}]}],
                anker=MSO_ANCHOR.MIDDLE)
            durch = e.get("durch", "") if isinstance(e, dict) else ""
            g = 9.5 if hk >= Inches(0.5) else 8.5
            absaetze = [{"laeufe": [{"text": text_von(e), "groesse": g, "fett": gewicht == stufen[0]},
                                    {"text": f"  ({gewicht})" if gewicht else "", "groesse": g - 1.5,
                                     "farbe": GEDAEMPFT}]}]
            if durch and hk >= Inches(0.45):
                absaetze.append({"text": ("durch: " if ok else "") + durch, "groesse": g - 1.5,
                                 "farbe": GRUEN if ok else GEDAEMPFT, "kursiv": True})
            textfeld(folie, x + Inches(0.52), yk, b - Inches(0.62), hk, absaetze, anker=MSO_ANCHOR.MIDDLE)

    # Zusammenfassung
    y = oben + Inches(4.78)
    flaeche(folie, links, y, Inches(12.33), Inches(0.78), WEISS, linie=LINIE)
    quote = f"{abgedeckt} von {gesamt} Kundenbedürfnissen berücksichtigt" if gesamt else "Noch keine Einträge"
    teile = [{"text": quote, "groesse": 12.5, "fett": True}]
    if hoch_offen:
        teile.append({"text": "   Offen mit höchster Gewichtung: " + "; ".join(hoch_offen[:4]), "groesse": 10.5,
                      "farbe": ROT})
    ohne = daten.get("ohne_bezug", [])
    absaetze = [{"laeufe": teile}]
    if ohne:
        absaetze.append({"text": "Elemente der Value Map ohne Bezug zum Kundenprofil: " + "; ".join(ohne),
                         "groesse": 10, "farbe": GEDAEMPFT, "abstand": 3})
    textfeld(folie, links + Inches(0.2), y, Inches(11.9), Inches(0.78), absaetze, anker=MSO_ANCHOR.MIDDLE)
    fuss(folie, prs, "✓ berücksichtigt   ✗ nicht berücksichtigt", daten.get("datum", ""))


def titel_folie(prs, daten):
    folie = prs.slides.add_slide(prs.slide_layouts[6])
    flaeche(folie, 0, 0, prs.slide_width, prs.slide_height, GRUEN)
    b = prs.slide_width / 3
    for i, farbe in enumerate((ANTHRAZIT, RGBColor(0xCB, 0xD9, 0xCF), GOLD)):
        flaeche(folie, int(i * b), prs.slide_height - Inches(0.18), int(b) + 1, Inches(0.18), farbe)
    textfeld(folie, Inches(0.9), Inches(1.4), Inches(11.5), Inches(4.6), [
        {"text": "VALUE PROPOSITION CANVAS", "groesse": 13, "fett": True, "farbe": GOLD},
        {"text": daten.get("wertangebot", "Wertangebot"), "groesse": 34, "fett": True, "farbe": WEISS,
         "abstand": 14},
        {"text": "für " + daten["kundensegment"] if daten.get("kundensegment") else "", "groesse": 20,
         "farbe": WEISS, "abstand": 6},
        {"text": " · ".join(t for t in (daten.get("organisation", ""), daten.get("datum", "")) if t),
         "groesse": 14, "farbe": RGBColor(0xCB, 0xD9, 0xCF), "abstand": 22},
    ], anker=MSO_ANCHOR.MIDDLE)


def main():
    a = sys.argv[1:]
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    if len(a) == 2 and a[0] == "--leer":
        canvas_folie(prs, {}, leer=True)
        ziel = a[1]
    elif len(a) == 3 and a[1] == "--kunde":
        daten = json.load(open(a[0], encoding="utf-8"))
        saeulen_folie(prs, daten, KUNDE, "Kundenprofil, gewichtet", "Zwischenresultat", True)
        ziel = a[2]
    elif len(a) == 2:
        daten = json.load(open(a[0], encoding="utf-8"))
        titel_folie(prs, daten)
        saeulen_folie(prs, daten, KUNDE, "Kundenprofil, gewichtet", "", True)
        if any(daten.get(k) for k, *_ in WERT):
            saeulen_folie(prs, daten, WERT, "Value Map", "", False)
            canvas_folie(prs, daten, leer=False)
        if any(isinstance(e, dict) and "abgedeckt" in e for k, *_ in KUNDE for e in daten.get(k, [])):
            fit_folie(prs, daten)
        ziel = a[1]
    else:
        sys.exit(__doc__)
    prs.save(ziel)
    print(f"Gespeichert: {ziel}")


if __name__ == "__main__":
    main()
