#!/usr/bin/env python3
"""Erzeugt ein PowerPoint mit dem Strategy Co-Creation Canvas.

Aufruf:
    python3 canvas_pptx.py canvas.json Ausgabe.pptx   ausgefüllter Canvas, drei Folien
    python3 canvas_pptx.py --leer Ausgabe.pptx        leerer Canvas mit Leitfragen
    python3 canvas_pptx.py --leer Ausgabe.pptx "Entscheidungsfrage"
                                                       leerer Canvas, Entscheidungsfrage vorgedruckt

Canvas nach Verena Fink, Künstliche Intelligenz in der Führungsarbeit, 1. Auflage, März 2026.

Benötigt python-pptx (pip install python-pptx).
"""
import json
import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt
except ImportError:
    sys.exit("python-pptx fehlt. Installieren mit: pip install python-pptx")

ANTHRAZIT = RGBColor(0x33, 0x38, 0x3D)
GRUEN = RGBColor(0x0F, 0x3D, 0x2E)
GOLD = RGBColor(0xE2, 0xB0, 0x4A)
GRUND = RGBColor(0xF2, 0xF3, 0xEC)
TINTE = RGBColor(0x14, 0x23, 0x1C)
GEDAEMPFT = RGBColor(0x3F, 0x4B, 0x44)
LINIE = RGBColor(0xD2, 0xD9, 0xCF)
WEISS = RGBColor(0xFF, 0xFF, 0xFF)
AUF_GRUEN = RGBColor(0xCB, 0xD9, 0xCF)
SCHRIFT = "Arial"
QUELLE = "Canvas nach Verena Fink, Künstliche Intelligenz in der Führungsarbeit (2026)"

LOGO = Path(__file__).resolve().parent.parent / "assets" / "vantic-logo-liegend.png"

# Aufbau wie im Original: drei Spalten mit je zwei Feldern.
# (Schlüssel, Titel, Leitfrage, Farbe, Spalte, Anteil der Spaltenhöhe oben)
FELDER = [
    ("zielbild", "Zielbild", "Was wollen wir erreichen?", GRUEN),
    ("stakeholder", "Stakeholder-Sicht", "Wer ist betroffen oder beteiligt?", GOLD),
    ("datenbasis", "Datenbasis", "Was weiss die KI? Was wissen wir?", ANTHRAZIT),
    ("ki_rolle", "KI-Rolle", "Was übernimmt die KI?", ANTHRAZIT),
    ("bewertungslogik", "Bewertungslogik", "Nach welchen Kriterien entscheiden wir?", GRUEN),
    ("verantwortung", "Menschliche Verantwortung", "Was entscheiden wir bewusst selbst?", GOLD),
]
SPALTEN = [("zielbild", "stakeholder", 0.55), ("datenbasis", "ki_rolle", 0.45),
           ("bewertungslogik", "verantwortung", 0.55)]
NUMMER = {"zielbild": 1, "stakeholder": 2, "datenbasis": 3, "ki_rolle": 4,
          "bewertungslogik": 5, "verantwortung": 6}


def mische(farbe, anteil):
    """Mischt eine Farbe mit Weiss, anteil 0 = weiss, 1 = Farbe."""
    return RGBColor(*[round(255 - (255 - c) * anteil) for c in farbe])


def textfarbe(hintergrund):
    return TINTE if hintergrund in (GOLD,) or sum(hintergrund) > 450 else WEISS


def rechteck(folie, x, y, b, h, farbe, form=MSO_SHAPE.RECTANGLE, linie=None):
    s = folie.shapes.add_shape(form, x, y, b, h)
    s.fill.solid()
    s.fill.fore_color.rgb = farbe
    if linie is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = linie
        s.line.width = Pt(1)
    s.shadow.inherit = False
    return s


def textfeld(folie, x, y, b, h, absaetze, anker=MSO_ANCHOR.TOP, rand=0):
    """absaetze: Liste von dict(text, groesse, farbe, fett, kursiv, abstand, aufzaehlung, ausrichtung)."""
    tb = folie.shapes.add_textbox(x, y, b, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anker
    for seite in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, seite, Emu(rand))
    for i, a in enumerate(absaetze):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = a.get("ausrichtung", PP_ALIGN.LEFT)
        p.space_before = Pt(a.get("abstand", 0))
        r = p.add_run()
        r.text = ("•  " if a.get("aufzaehlung") else "") + a["text"]
        f = r.font
        f.name = SCHRIFT
        f.size = Pt(a.get("groesse", 12))
        f.bold = a.get("fett", False)
        f.italic = a.get("kursiv", False)
        f.color.rgb = a.get("farbe", TINTE)
    return tb


def schriftgroesse(zeilen, breite_zoll, hoehe_zoll):
    """Wählt eine Schriftgrösse, damit die Stichpunkte ins Feld passen."""
    for groesse in (13, 12.5, 12, 11.5, 11, 10.5, 10, 9.5, 9):
        zeichen_pro_zeile = breite_zoll * 72 / (groesse * 0.5)
        benoetigte_zeilen = sum(max(1, -(-len(z) // int(zeichen_pro_zeile))) for z in zeilen)
        if benoetigte_zeilen * groesse * 1.22 + len(zeilen) * 3 <= hoehe_zoll * 72:
            return groesse
    return 9


def kopf(folie, titel, untertitel, prs):
    rechteck(folie, 0, 0, prs.slide_width, prs.slide_height, GRUND)
    textfeld(folie, Inches(0.5), Inches(0.32), Inches(9.6), Inches(0.9), [
        {"text": titel, "groesse": 22, "fett": True, "farbe": TINTE},
        {"text": untertitel, "groesse": 12, "farbe": GEDAEMPFT, "abstand": 4},
    ])
    if LOGO.exists():
        folie.shapes.add_picture(str(LOGO), Inches(10.95), Inches(0.38), height=Inches(0.5))


def fuss(folie, text, prs):
    textfeld(folie, Inches(0.5), prs.slide_height - Inches(0.42), Inches(12.3), Inches(0.3), [
        {"text": text, "groesse": 9, "farbe": GEDAEMPFT},
    ])


def canvas_folie(prs, daten, leer):
    folie = prs.slides.add_slide(prs.slide_layouts[6])
    frage = daten.get("entscheidungsfrage", "")
    if leer:
        frage = frage or "Entscheidungsfrage: ..............................................................................................."
    kopf(folie, "Strategy Co-Creation Canvas", frage, prs)

    links, oben = Inches(0.5), Inches(1.45)
    gesamt_b, gesamt_h = Inches(12.33), Inches(5.45)
    luecke = Inches(0.1)
    spalte_b = int((gesamt_b - 2 * luecke) / 3)
    felder = {f[0]: f for f in FELDER}
    inhalt = daten.get("felder", {})

    def zeilen_von(key):
        if key == "datenbasis":
            return ["KI weiss"] + inhalt.get("datenbasis_ki", []) + ["Wir wissen"] + inhalt.get("datenbasis_wir", [])
        return inhalt.get(key, [])

    einheitlich = 13
    if not leer:
        for oben_key, unten_key, anteil in SPALTEN:
            h_o = int((gesamt_h - luecke) * anteil)
            for key, h in ((oben_key, h_o), (unten_key, gesamt_h - luecke - h_o)):
                einheitlich = min(einheitlich, schriftgroesse(
                    zeilen_von(key), (spalte_b - Inches(0.44)) / 914400, (h - Inches(1.0)) / 914400))

    for s, (oben_key, unten_key, anteil) in enumerate(SPALTEN):
        x = links + s * (spalte_b + luecke)
        h_oben = int((gesamt_h - luecke) * anteil)
        h_unten = gesamt_h - luecke - h_oben
        for key, y, h in ((oben_key, oben, h_oben), (unten_key, oben + h_oben + luecke, h_unten)):
            _, titel, leitfrage, farbe = felder[key]
            hintergrund = mische(farbe, 0.16) if leer else farbe
            schrift = TINTE if leer else textfarbe(farbe)
            rechteck(folie, x, y, spalte_b, h, hintergrund, linie=farbe if leer else None)

            # Nummer
            kreis_d = Inches(0.36)
            k = rechteck(folie, x + spalte_b - kreis_d - Inches(0.16), y + Inches(0.16),
                         kreis_d, kreis_d, farbe if leer else WEISS, form=MSO_SHAPE.OVAL)
            k.text_frame.text = str(NUMMER[key])
            for seite in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
                setattr(k.text_frame, seite, 0)
            k.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = k.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            f = p.runs[0].font
            f.name, f.size, f.bold = SCHRIFT, Pt(12), True
            f.color.rgb = WEISS if leer else farbe

            innen_x = x + Inches(0.22)
            innen_b = spalte_b - Inches(0.44)
            textfeld(folie, innen_x, y + Inches(0.16), innen_b - Inches(0.45), Inches(0.75), [
                {"text": titel, "groesse": 15, "fett": True, "farbe": schrift},
                {"text": leitfrage, "groesse": 10.5, "kursiv": True, "farbe": schrift, "abstand": 2},
            ])
            if leer:
                continue

            text_y = y + Inches(0.9)
            text_h = h - Inches(1.0)
            g = einheitlich
            if key == "datenbasis":
                ki = inhalt.get("datenbasis_ki", [])
                wir = inhalt.get("datenbasis_wir", [])
                absaetze = [{"text": "KI weiss", "groesse": g, "fett": True, "farbe": schrift}]
                absaetze += [{"text": t, "groesse": g, "farbe": schrift, "aufzaehlung": True, "abstand": 2} for t in ki]
                absaetze += [{"text": "Wir wissen", "groesse": g, "fett": True, "farbe": schrift, "abstand": 6}]
                absaetze += [{"text": t, "groesse": g, "farbe": schrift, "aufzaehlung": True, "abstand": 2} for t in wir]
            else:
                punkte = inhalt.get(key, [])
                absaetze = [{"text": t, "groesse": g, "farbe": schrift, "aufzaehlung": True,
                             "abstand": 0 if i == 0 else 3} for i, t in enumerate(punkte)]
            if absaetze:
                textfeld(folie, innen_x, text_y, innen_b, text_h, absaetze)

    legende = "Grün: Ziel und Entscheidung    Anthrazit: Daten und KI    Gold: Menschen und Verantwortung"
    if not leer:
        legende = f"{daten.get('organisation', '')}  ·  {daten.get('datum', '')}    {legende}".strip(" ·")
    fuss(folie, f"{legende}    {QUELLE}", prs)


def titel_folie(prs, daten):
    folie = prs.slides.add_slide(prs.slide_layouts[6])
    rechteck(folie, 0, 0, prs.slide_width, prs.slide_height, GRUEN)
    breite = prs.slide_width / 3
    for i, farbe in enumerate((ANTHRAZIT, GRUEN, GOLD)):
        rechteck(folie, int(i * breite), prs.slide_height - Inches(0.18), int(breite) + 1, Inches(0.18),
                 farbe if farbe != GRUEN else AUF_GRUEN)
    textfeld(folie, Inches(0.9), Inches(1.4), Inches(11.5), Inches(4.6), [
        {"text": "STRATEGY CO-CREATION CANVAS", "groesse": 13, "fett": True, "farbe": GOLD},
        {"text": daten.get("entscheidungsfrage", ""), "groesse": 34, "fett": True, "farbe": WEISS, "abstand": 14},
        {"text": " · ".join(t for t in (daten.get("organisation", ""), daten.get("datum", "")) if t),
         "groesse": 15, "farbe": AUF_GRUEN, "abstand": 22},
    ], anker=MSO_ANCHOR.MIDDLE)


def synthese_folie(prs, daten):
    folie = prs.slides.add_slide(prs.slide_layouts[6])
    syn = daten.get("synthese", {})
    kopf(folie, "Synthese und nächste Schritte", daten.get("entscheidungsfrage", ""), prs)

    links, oben = Inches(0.5), Inches(1.45)
    b_links, b_rechts, luecke = Inches(7.4), Inches(4.83), Inches(0.1)

    rechteck(folie, links, oben, b_links, Inches(2.35), GRUEN)
    textfeld(folie, links + Inches(0.25), oben + Inches(0.2), b_links - Inches(0.5), Inches(2.0), [
        {"text": "Entscheidungsvorschlag", "groesse": 13, "fett": True, "farbe": GOLD},
        {"text": syn.get("entscheidung", ""), "groesse": 14, "farbe": WEISS, "abstand": 4},
        {"text": "Arbeitsteilung Mensch und KI", "groesse": 13, "fett": True, "farbe": GOLD, "abstand": 12},
        {"text": syn.get("arbeitsteilung", ""), "groesse": 12, "farbe": AUF_GRUEN, "abstand": 4},
    ])

    x_r = links + b_links + luecke
    rechteck(folie, x_r, oben, b_rechts, Inches(2.35), GOLD)
    offene = syn.get("offene_punkte", [])
    g = schriftgroesse(offene, 4.3, 1.7)
    textfeld(folie, x_r + Inches(0.25), oben + Inches(0.2), b_rechts - Inches(0.5), Inches(2.0), [
        {"text": "Offene Punkte", "groesse": 13, "fett": True, "farbe": TINTE},
    ] + [{"text": t, "groesse": g, "farbe": TINTE, "aufzaehlung": True, "abstand": 4} for t in offene])

    schritte = syn.get("naechste_schritte", [])
    t_oben = oben + Inches(2.35) + Inches(0.3)
    textfeld(folie, links, t_oben, Inches(6), Inches(0.35), [
        {"text": "Nächste Schritte", "groesse": 13, "fett": True, "farbe": TINTE},
    ])
    if schritte:
        zeilen = len(schritte) + 1
        tab = folie.shapes.add_table(zeilen, 3, links, t_oben + Inches(0.42), Inches(12.33),
                                     Inches(0.38) * zeilen).table
        for i, w in enumerate((Inches(7.6), Inches(2.9), Inches(1.83))):
            tab.columns[i].width = w
        werte = [("Was", "Wer", "Bis")] + [(s.get("was", ""), s.get("wer", ""), s.get("bis", "")) for s in schritte]
        for r, zeile in enumerate(werte):
            for c, wert in enumerate(zeile):
                zelle = tab.cell(r, c)
                zelle.fill.solid()
                zelle.fill.fore_color.rgb = ANTHRAZIT if r == 0 else (WEISS if r % 2 else GRUND)
                zelle.text = wert
                zelle.margin_left = zelle.margin_right = Inches(0.12)
                f = zelle.text_frame.paragraphs[0].runs[0].font if zelle.text_frame.paragraphs[0].runs else None
                if f:
                    f.name, f.size, f.bold = SCHRIFT, Pt(11), r == 0
                    f.color.rgb = WEISS if r == 0 else TINTE

    fuss(folie, f"Erstellt mit dem Strategy Co-Creation Canvas Skill von Vantic  ·  vantic.ch    {QUELLE}", prs)


def main():
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[1] != "--leer"):
        sys.exit(__doc__)
    quelle, ziel = sys.argv[1], sys.argv[2]
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    if quelle == "--leer":
        frage = sys.argv[3] if len(sys.argv) == 4 else ""
        canvas_folie(prs, {"entscheidungsfrage": frage}, leer=True)
    else:
        with open(quelle, encoding="utf-8") as f:
            daten = json.load(f)
        titel_folie(prs, daten)
        canvas_folie(prs, daten, leer=False)
        synthese_folie(prs, daten)

    prs.save(ziel)
    print(f"Gespeichert: {ziel}")


if __name__ == "__main__":
    main()
