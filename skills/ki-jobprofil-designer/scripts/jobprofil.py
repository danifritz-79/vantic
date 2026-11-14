#!/usr/bin/env python3
"""Erzeugt die Resultate des KI-Jobprofil-Designers.

Aufruf:
    python3 jobprofil.py rolle.json --pptx Jobprofil.pptx --xlsx Aufgabenanalyse.xlsx
    python3 jobprofil.py --leer --xlsx Aufgabenanalyse-leer.xlsx

--pptx  PowerPoint: Titel, Aufgabenanalyse, Zeitverteilung heute und künftig, neues Rollenprofil
--xlsx  Excel: Aufgabenanalyse mit Formeln und Diagramm, Anteile und Entlastung lassen sich nachjustieren
Ohne Angabe werden beide Dateien erzeugt (jobprofil.pptx, aufgabenanalyse.xlsx).

Gibt zusätzlich eine Kurzauswertung der Zeitverschiebung aus.
Benötigt python-pptx (für --pptx) und openpyxl (für --xlsx).
"""
import json
import sys
from pathlib import Path

QUELLE = "KI-Jobprofil-Designer von Vantic  ·  vantic.ch"
LOGO = Path(__file__).resolve().parent.parent / "assets" / "vantic-logo-liegend.png"

# Einstufung: Schlüssel, Bezeichnung, Standard-Entlastung in Prozent, Farbe
KATEGORIEN = [
    ("uebernimmt", "KI übernimmt", 80, "33383D"),
    ("unterstuetzt", "KI unterstützt", 35, "0F3D2E"),
    ("mensch", "Bleibt beim Menschen", 0, "E2B04A"),
]
KAT = {k: (name, ent, farbe) for k, name, ent, farbe in KATEGORIEN}
NEU_FARBE = "6FA58C"
FREI_FARBE = "D2D9CF"

TINTE, GEDAEMPFT, GRUND = "14231C", "3F4B44", "F2F3EC"
GRUEN, GOLD, ANTHRAZIT = "0F3D2E", "E2B04A", "33383D"


# ---------- Berechnung ----------

def entlastung(a):
    e = a.get("entlastung")
    return float(e) if e is not None else KAT.get(a.get("kategorie"), ("", 0, ""))[1]


def berechne(daten):
    aufgaben = daten.get("aufgaben", [])
    zeilen = []
    for a in aufgaben:
        heute = float(a.get("anteil", 0) or 0)
        e = entlastung(a)
        zeilen.append({**a, "anteil": heute, "entlastung": e, "kuenftig": round(heute * (1 - e / 100), 1)})
    summe_heute = sum(z["anteil"] for z in zeilen)
    pro_kat_heute = {k: sum(z["anteil"] for z in zeilen if z.get("kategorie") == k) for k, *_ in KATEGORIEN}
    pro_kat_kuenftig = {k: sum(z["kuenftig"] for z in zeilen if z.get("kategorie") == k) for k, *_ in KATEGORIEN}
    neu = sum(float(n.get("anteil", 0) or 0) for n in daten.get("neue_aufgaben", []))
    frei_brutto = summe_heute - sum(pro_kat_kuenftig.values())
    frei_netto = 100 - sum(pro_kat_kuenftig.values()) - neu
    return {
        "zeilen": zeilen, "summe_heute": summe_heute, "heute": pro_kat_heute, "kuenftig": pro_kat_kuenftig,
        "neu": neu, "frei_brutto": round(frei_brutto, 1), "frei_netto": round(frei_netto, 1),
    }


def auswertung(daten):
    r = berechne(daten)
    z = ["AUSWERTUNG", ""]
    if abs(r["summe_heute"] - 100) > 0.5:
        z.append(f"Achtung: Die Anteile heute ergeben {r['summe_heute']:.0f} Prozent statt 100.")
    for k, name, *_ in KATEGORIEN:
        z.append(f"{name}: heute {r['heute'][k]:.0f} %, künftig {r['kuenftig'][k]:.0f} %")
    z.append(f"Durch KI frei werdende Zeit: {r['frei_brutto']:.0f} %")
    z.append(f"Neue Aufgaben: {r['neu']:.0f} %")
    if r["frei_netto"] < 0:
        z.append(f"Achtung: Die künftige Rolle ist um {-r['frei_netto']:.0f} % überbucht.")
    else:
        z.append(f"Noch nicht verplante Kapazität: {r['frei_netto']:.0f} %")
    return "\n".join(z)


# ---------- PowerPoint ----------

def pptx(daten, pfad):
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt

    def rgb(h):
        return RGBColor.from_string(h)

    def mische(h, anteil):
        c = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
        return RGBColor(*[round(255 - (255 - x) * anteil) for x in c])

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    r = berechne(daten)

    def flaeche(f, x, y, b, h, farbe, linie=None, form=MSO_SHAPE.RECTANGLE):
        s = f.shapes.add_shape(form, x, y, b, h)
        s.fill.solid()
        s.fill.fore_color.rgb = farbe if isinstance(farbe, RGBColor) else rgb(farbe)
        if linie:
            s.line.color.rgb = rgb(linie)
            s.line.width = Pt(0.75)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        return s

    def text(f, x, y, b, h, absaetze, anker=MSO_ANCHOR.TOP):
        tf = f.shapes.add_textbox(x, y, b, h).text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anker
        for seite in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(tf, seite, Emu(0))
        for i, a in enumerate(absaetze):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = a.get("ausr", PP_ALIGN.LEFT)
            p.space_before = Pt(a.get("abstand", 0))
            run = p.add_run()
            run.text = a["t"]
            run.font.name = "Arial"
            run.font.size = Pt(a.get("g", 12))
            run.font.bold = a.get("fett", False)
            run.font.italic = a.get("kursiv", False)
            run.font.color.rgb = a["farbe"] if isinstance(a.get("farbe"), RGBColor) else rgb(a.get("farbe", TINTE))
        return tf

    def folie(titel, unter=None):
        f = prs.slides.add_slide(prs.slide_layouts[6])
        flaeche(f, 0, 0, prs.slide_width, prs.slide_height, GRUND)
        unter = unter if unter is not None else " · ".join(
            t for t in (daten.get("rolle", ""), daten.get("organisation", "")) if t)
        text(f, Inches(0.5), Inches(0.3), Inches(10.2), Inches(0.9), [
            {"t": titel, "g": 22, "fett": True}, {"t": unter, "g": 11, "farbe": GEDAEMPFT, "abstand": 3}])
        if LOGO.exists():
            f.shapes.add_picture(str(LOGO), Inches(10.95), Inches(0.36), height=Inches(0.5))
        zusatz = " · ".join(t for t in (daten.get("datum", ""), daten.get("zeithorizont") and
                                        f"Zeithorizont: {daten['zeithorizont']}") if t)
        text(f, Inches(0.5), prs.slide_height - Inches(0.4), Inches(12.3), Inches(0.3), [
            {"t": (zusatz + "    " if zusatz else "") + QUELLE, "g": 8.5, "farbe": GEDAEMPFT}])
        return f

    # Folie 1: Titel
    f = prs.slides.add_slide(prs.slide_layouts[6])
    flaeche(f, 0, 0, prs.slide_width, prs.slide_height, GRUEN)
    drittel = prs.slide_width / 3
    for i, farbe in enumerate((ANTHRAZIT, "CBD9CF", GOLD)):
        flaeche(f, int(i * drittel), prs.slide_height - Inches(0.18), int(drittel) + 1, Inches(0.18), farbe)
    text(f, Inches(0.9), Inches(1.4), Inches(11.5), Inches(4.6), [
        {"t": "KI-JOBPROFIL", "g": 13, "fett": True, "farbe": GOLD},
        {"t": daten.get("rolle", "Rolle"), "g": 36, "fett": True, "farbe": "FFFFFF", "abstand": 14},
        {"t": daten.get("zweck_kuenftig", ""), "g": 17, "farbe": "FFFFFF", "abstand": 8},
        {"t": " · ".join(t for t in (daten.get("organisation", ""), daten.get("zeithorizont", "") and
                                     f"Zeithorizont {daten.get('zeithorizont')}", daten.get("datum", "")) if t),
         "g": 13, "farbe": "CBD9CF", "abstand": 22},
    ], anker=MSO_ANCHOR.MIDDLE)

    # Folie 2: Aufgabenanalyse als Tabelle
    f = folie("Aufgabenanalyse")
    reihen = sorted(r["zeilen"], key=lambda z: ([k for k, *_ in KATEGORIEN].index(z.get("kategorie"))
                                                if z.get("kategorie") in KAT else 9, -z["anteil"]))
    n = len(reihen)
    kopf = ["Aufgabe", "Bereich", "Heute", "Einstufung", "Entlastung", "Künftig"]
    breiten = [Inches(5.4), Inches(2.1), Inches(0.95), Inches(2.0), Inches(1.0), Inches(0.88)]
    zeilenhoehe = min(Inches(0.38), int(Inches(5.1) / (n + 2)))
    tab = f.shapes.add_table(n + 2, len(kopf), Inches(0.5), Inches(1.4), sum(breiten),
                             zeilenhoehe * (n + 2)).table
    for i, w in enumerate(breiten):
        tab.columns[i].width = w
    g = 10.5 if n <= 10 else (9.5 if n <= 14 else 8.5)

    def zelle(ri, ci, wert, fill, schrift=TINTE, fett=False, ausr=PP_ALIGN.LEFT):
        c = tab.cell(ri, ci)
        c.fill.solid()
        c.fill.fore_color.rgb = fill if isinstance(fill, RGBColor) else rgb(fill)
        c.margin_left = c.margin_right = Inches(0.08)
        c.margin_top = c.margin_bottom = Inches(0.02)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        c.text = str(wert)
        p = c.text_frame.paragraphs[0]
        p.alignment = ausr
        for run in p.runs:
            run.font.name, run.font.size, run.font.bold = "Arial", Pt(g), fett
            run.font.color.rgb = rgb(schrift)

    for ci, t in enumerate(kopf):
        zelle(0, ci, t, ANTHRAZIT, "FFFFFF", True, PP_ALIGN.CENTER if ci >= 2 else PP_ALIGN.LEFT)
    for ri, z in enumerate(reihen, start=1):
        name, _, farbe = KAT.get(z.get("kategorie"), ("offen", 0, "FFFFFF"))
        hg = "FFFFFF" if ri % 2 else "F7F8F4"
        zelle(ri, 0, z.get("text", ""), hg)
        zelle(ri, 1, z.get("bereich", ""), hg, GEDAEMPFT)
        zelle(ri, 2, f"{z['anteil']:.0f} %", hg, ausr=PP_ALIGN.CENTER)
        zelle(ri, 3, name, mische(farbe, 0.9 if z.get("kategorie") != "mensch" else 1),
              "FFFFFF" if z.get("kategorie") in ("uebernimmt", "unterstuetzt") else TINTE, True, PP_ALIGN.CENTER)
        zelle(ri, 4, f"{z['entlastung']:.0f} %", hg, ausr=PP_ALIGN.CENTER)
        zelle(ri, 5, f"{z['kuenftig']:.0f} %", hg, fett=True, ausr=PP_ALIGN.CENTER)
    summe = n + 1
    for ci, t in enumerate(["Total", "", f"{r['summe_heute']:.0f} %", "", f"−{r['frei_brutto']:.0f} %",
                            f"{sum(r['kuenftig'].values()):.0f} %"]):
        zelle(summe, ci, t, "E6EBE3", fett=True, ausr=PP_ALIGN.CENTER if ci >= 2 else PP_ALIGN.LEFT)

    # Folie 3: Zeitverteilung heute und künftig
    f = folie("Wie sich die Arbeitszeit verschiebt")
    x0, bx = Inches(2.3), Inches(10.4)
    balken = [
        ("Heute", [(KAT[k][0], r["heute"][k], KAT[k][2]) for k, *_ in KATEGORIEN]),
        ("Künftig", [(KAT[k][0], r["kuenftig"][k], KAT[k][2]) for k, *_ in KATEGORIEN] +
         [("Neue Aufgaben", r["neu"], NEU_FARBE), ("Freie Kapazität", max(0, r["frei_netto"]), FREI_FARBE)]),
    ]
    for i, (titel, teile) in enumerate(balken):
        y = Inches(1.65) + i * Inches(1.2)
        text(f, Inches(0.5), y, Inches(1.7), Inches(0.75), [{"t": titel, "g": 15, "fett": True}],
             anker=MSO_ANCHOR.MIDDLE)
        x = x0
        gesamt = max(100.0, sum(w for _, w, _ in teile))
        for name, wert, farbe in teile:
            if wert <= 0:
                continue
            b = int(bx * wert / gesamt)
            s = flaeche(f, x, y, b, Inches(0.75), farbe, linie="FFFFFF")
            if b > Inches(0.55):
                tf = s.text_frame
                tf.text = f"{wert:.0f} %"
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER
                p.runs[0].font.name, p.runs[0].font.size, p.runs[0].font.bold = "Arial", Pt(12), True
                p.runs[0].font.color.rgb = rgb("FFFFFF" if farbe in (ANTHRAZIT, GRUEN) else TINTE)
            x += b
    # Legende
    lx, ly = x0, Inches(4.15)
    for name, farbe in [(KAT[k][0], KAT[k][2]) for k, *_ in KATEGORIEN] + [("Neue Aufgaben", NEU_FARBE),
                                                                          ("Freie Kapazität", FREI_FARBE)]:
        flaeche(f, lx, ly + Inches(0.04), Inches(0.2), Inches(0.2), farbe)
        text(f, lx + Inches(0.28), ly, Inches(1.9), Inches(0.3), [{"t": name, "g": 10, "farbe": GEDAEMPFT}])
        lx += Inches(2.08)
    # Kennzahlen
    kennzahlen = [
        (f"{r['frei_brutto']:.0f} %", "der heutigen Arbeitszeit werden durch KI frei", ANTHRAZIT),
        (f"{r['neu']:.0f} %", "fliessen in neue Aufgaben", GRUEN),
        (f"{r['frei_netto']:.0f} %" if r["frei_netto"] >= 0 else f"+{-r['frei_netto']:.0f} %",
         "noch nicht verplant" if r["frei_netto"] >= 0 else "überbucht, Rolle prüfen", GOLD),
    ]
    kb = Inches(3.98)
    for i, (zahl, label, farbe) in enumerate(kennzahlen):
        x = Inches(0.5) + i * (kb + Inches(0.2))
        flaeche(f, x, Inches(4.75), kb, Inches(1.55), "FFFFFF", linie="D2D9CF")
        flaeche(f, x, Inches(4.75), Inches(0.1), Inches(1.55), farbe)
        text(f, x + Inches(0.35), Inches(4.75), kb - Inches(0.5), Inches(1.55), [
            {"t": zahl, "g": 30, "fett": True, "farbe": GRUEN if farbe == GRUEN else (
                "A87A0A" if farbe == GOLD else ANTHRAZIT)},
            {"t": label, "g": 12, "farbe": GEDAEMPFT, "abstand": 2}], anker=MSO_ANCHOR.MIDDLE)
    if abs(r["summe_heute"] - 100) > 0.5:
        text(f, Inches(0.5), Inches(6.45), Inches(12), Inches(0.3), [
            {"t": f"Hinweis: Die Anteile heute ergeben {r['summe_heute']:.0f} Prozent statt 100.", "g": 10,
             "farbe": "B43C2E"}])

    # Folie 4: Neues Rollenprofil
    p = daten.get("profil", {})
    f = folie("Neues Rollenprofil", daten.get("zweck_kuenftig", ""))
    spalten = [
        ("Verantwortungen", p.get("verantwortungen", []), GRUEN, "FFFFFF"),
        ("Neue Aufgaben", [f"{n.get('text', '')} ({float(n.get('anteil', 0) or 0):.0f} %)"
                           for n in daten.get("neue_aufgaben", [])], NEU_FARBE, TINTE),
        ("Benötigte Kompetenzen", [k.get("text", "") + (f", Stufe {k['stufe']}" if k.get("stufe") else "")
                                   if isinstance(k, dict) else k for k in p.get("kompetenzen", [])], GOLD, TINTE),
    ]
    sb, luecke = int((Inches(12.33) - 2 * Inches(0.15)) / 3), Inches(0.15)
    for i, (titel, punkte, farbe, schrift) in enumerate(spalten):
        x = Inches(0.5) + i * (sb + luecke)
        flaeche(f, x, Inches(1.45), sb, Inches(0.55), farbe)
        text(f, x + Inches(0.2), Inches(1.45), sb - Inches(0.4), Inches(0.55),
             [{"t": titel, "g": 14, "fett": True, "farbe": schrift}], anker=MSO_ANCHOR.MIDDLE)
        flaeche(f, x, Inches(2.0), sb, Inches(3.15), "FFFFFF", linie="D2D9CF")
        g = 11 if len(punkte) <= 6 else 9.5
        text(f, x + Inches(0.2), Inches(2.15), sb - Inches(0.4), Inches(2.9),
             [{"t": "•  " + t, "g": g, "abstand": 0 if j == 0 else 5} for j, t in enumerate(punkte[:9])]
             or [{"t": "noch offen", "g": 10, "kursiv": True, "farbe": GEDAEMPFT}])
    unten = [
        ("Entscheidungsbefugnisse", p.get("entscheidungen", [])),
        ("Was wegfällt oder an KI geht", p.get("faellt_weg", [])),
        ("Schnittstellen", p.get("schnittstellen", [])),
    ]
    for i, (titel, punkte) in enumerate(unten):
        x = Inches(0.5) + i * (sb + luecke)
        flaeche(f, x, Inches(5.3), sb, Inches(1.45), "E6EBE3")
        text(f, x + Inches(0.2), Inches(5.38), sb - Inches(0.4), Inches(1.32),
             [{"t": titel, "g": 11, "fett": True}] +
             [{"t": "•  " + t, "g": 9.5, "abstand": 2} for t in punkte[:4]])

    # Folie 5: Übergang, falls erfasst
    schritte = daten.get("uebergang", [])
    if schritte:
        f = folie("Der Weg in die neue Rolle")
        tab = f.shapes.add_table(len(schritte) + 1, 3, Inches(0.5), Inches(1.45), Inches(12.33),
                                 Inches(0.42) * (len(schritte) + 1)).table
        for i, w in enumerate((Inches(7.9), Inches(2.6), Inches(1.83))):
            tab.columns[i].width = w
        g = 11
        for ci, t in enumerate(("Was", "Wer", "Bis")):
            zelle(0, ci, t, ANTHRAZIT, "FFFFFF", True)
        for ri, s in enumerate(schritte, start=1):
            hg = "FFFFFF" if ri % 2 else "F7F8F4"
            zelle(ri, 0, s.get("was", ""), hg)
            zelle(ri, 1, s.get("wer", ""), hg)
            zelle(ri, 2, s.get("bis", ""), hg)
    prs.save(pfad)


# ---------- Excel ----------

def excel(daten, pfad):
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.chart.series import SeriesLabel
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "Aufgabenanalyse"
    titel = Font(name="Arial", size=16, bold=True, color=TINTE)
    weiss = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    normal = Font(name="Arial", size=10, color=TINTE)
    fett = Font(name="Arial", size=10, bold=True, color=TINTE)
    klein = Font(name="Arial", size=9, italic=True, color=GEDAEMPFT)
    kopf_fill = PatternFill("solid", fgColor=ANTHRAZIT)
    eingabe = PatternFill("solid", fgColor="FFF6DE")
    rechnung = PatternFill("solid", fgColor="EEF3EC")
    d = Side(style="thin", color="D2D9CF")
    rahmen = Border(left=d, right=d, top=d, bottom=d)

    ws["A1"] = "KI-Jobprofil: Aufgabenanalyse"
    ws["A1"].font = titel
    ws["A2"] = " · ".join(t for t in (daten.get("rolle", ""), daten.get("organisation", ""),
                                      daten.get("datum", "")) if t) or "Rolle · Organisation · Datum"
    ws["A2"].font = klein
    ws["A3"] = ("Gelbe Felder sind Eingaben. Entlastung leer lassen, dann gilt der Standardwert der Einstufung "
                "(KI übernimmt 80 %, KI unterstützt 35 %, bleibt beim Menschen 0 %).")
    ws["A3"].font = klein

    kopf = ["Aufgabe", "Bereich", "Anteil heute %", "Einstufung", "Entlastung %", "Anteil künftig %", "Begründung"]
    K = 5
    for i, t in enumerate(kopf, start=1):
        c = ws.cell(K, i, t)
        c.font, c.fill, c.border = weiss, kopf_fill, rahmen
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    namen = [n for _, n, _, _ in KATEGORIEN]
    dv = DataValidation(type="list", formula1='"' + ",".join(namen) + '"', allow_blank=True)
    prozent = DataValidation(type="decimal", operator="between", formula1="0", formula2="100", allow_blank=True)
    ws.add_data_validation(dv)
    ws.add_data_validation(prozent)
    aufgaben = daten.get("aufgaben", [])
    zeilen = max(20, len(aufgaben) + 5)
    erste, letzte = K + 1, K + zeilen
    std = ('IF(D{r}="{a}",80,IF(D{r}="{b}",35,0))').replace("{a}", namen[0]).replace("{b}", namen[1])
    for i in range(zeilen):
        r = erste + i
        a = aufgaben[i] if i < len(aufgaben) else {}
        werte = [a.get("text"), a.get("bereich"), a.get("anteil"),
                 KAT[a["kategorie"]][0] if a.get("kategorie") in KAT else None, a.get("entlastung")]
        for c, w in enumerate(werte, start=1):
            z = ws.cell(r, c, w)
            z.fill, z.border, z.font = eingabe, rahmen, normal
        dv.add(f"D{r}")
        prozent.add(f"C{r}")
        prozent.add(f"E{r}")
        ws.cell(r, 6, f'=IF(C{r}="","",ROUND(C{r}*(1-IF(E{r}="",{std.format(r=r)},E{r})/100),1))')
        ws.cell(r, 7, a.get("begruendung"))
        for c in (6, 7):
            ws.cell(r, c).border, ws.cell(r, c).font = rahmen, normal
        ws.cell(r, 6).fill = rechnung
        ws.cell(r, 7).fill = eingabe
        for c in (3, 4, 5, 6):
            ws.cell(r, c).alignment = Alignment(horizontal="center")
        ws.cell(r, 7).alignment = Alignment(wrap_text=True, vertical="top")
    # Farbmarkierung der Einstufung
    for (_, name, _, farbe), schrift in zip(KATEGORIEN, ("FFFFFF", "FFFFFF", TINTE)):
        ws.conditional_formatting.add(
            f"D{erste}:D{letzte}",
            FormulaRule(formula=[f'$D{erste}="{name}"'], fill=PatternFill("solid", fgColor=farbe),
                        font=Font(color=schrift, bold=True)))

    # Neue Aufgaben
    n0 = letzte + 2
    ws.cell(n0, 1, "Neue Aufgaben in der künftigen Rolle").font = fett
    for i, t in enumerate(["Neue Aufgabe", "Bereich", "Anteil künftig %"], start=1):
        c = ws.cell(n0 + 1, i, t)
        c.font, c.fill, c.border = weiss, kopf_fill, rahmen
    neue = daten.get("neue_aufgaben", [])
    nz = max(8, len(neue) + 3)
    for i in range(nz):
        r = n0 + 2 + i
        a = neue[i] if i < len(neue) else {}
        for c, w in enumerate([a.get("text"), a.get("bereich"), a.get("anteil")], start=1):
            z = ws.cell(r, c, w)
            z.fill, z.border, z.font = eingabe, rahmen, normal
        prozent.add(f"C{r}")
        ws.cell(r, 3).alignment = Alignment(horizontal="center")
    neu_von, neu_bis = n0 + 2, n0 + 1 + nz

    # Zusammenfassung rechts
    sx = 9  # Spalte I
    ws.cell(K, sx, "Zeitverteilung").font = fett
    for i, t in enumerate(["", "Heute %", "Künftig %"]):
        c = ws.cell(K + 1, sx + i, t)
        c.font, c.fill, c.border = weiss, kopf_fill, rahmen
    zusammen = [(n, f'=SUMIF($D${erste}:$D${letzte},"{n}",$C${erste}:$C${letzte})',
                 f'=SUMIF($D${erste}:$D${letzte},"{n}",$F${erste}:$F${letzte})') for n in namen]
    zusammen.append(("Neue Aufgaben", "=0", f"=SUM(C{neu_von}:C{neu_bis})"))
    zusammen.append(("Freie Kapazität", "=0",
                     f"=MAX(0,100-SUM({chr(64 + sx + 2)}{K + 2}:{chr(64 + sx + 2)}{K + 5}))"))
    for i, (n, h, k) in enumerate(zusammen):
        r = K + 2 + i
        ws.cell(r, sx, n).font = normal
        ws.cell(r, sx + 1, h)
        ws.cell(r, sx + 2, k)
        for c in range(sx, sx + 3):
            ws.cell(r, c).border = rahmen
            if c > sx:
                ws.cell(r, c).fill, ws.cell(r, c).alignment = rechnung, Alignment(horizontal="center")
    r = K + 2 + len(zusammen)
    ws.cell(r, sx, "Total").font = fett
    S = chr(64 + sx + 1)
    T = chr(64 + sx + 2)
    ws.cell(r, sx + 1, f"=SUM({S}{K + 2}:{S}{r - 1})").font = fett
    ws.cell(r, sx + 2, f"=SUM({T}{K + 2}:{T}{r - 1})").font = fett
    ws.cell(r + 1, sx, "Durch KI frei").font = normal
    ws.cell(r + 1, sx + 2, f"=SUM(C{erste}:C{letzte})-SUM(F{erste}:F{letzte})")
    ws.cell(r + 2, sx, "Überbuchung").font = normal
    ws.cell(r + 2, sx + 2, f"=MAX(0,SUM({T}{K + 2}:{T}{K + 5})-100)")
    ws.cell(r + 3, sx, "Prüfung Heute = 100 %").font = normal
    ws.cell(r + 3, sx + 2, f'=IF(ABS(SUM(C{erste}:C{letzte})-100)<0.5,"ok","Summe prüfen")')
    for rr in (r, r + 1, r + 2, r + 3):
        for c in range(sx, sx + 3):
            ws.cell(rr, c).border = rahmen
        ws.cell(rr, sx + 2).alignment = Alignment(horizontal="center")

    # Gestapeltes Balkendiagramm Heute und Künftig
    ch = BarChart()
    ch.type = "bar"
    ch.grouping = "percentStacked"
    ch.overlap = 100
    ch.title = "Zeitverteilung heute und künftig"
    ch.width, ch.height = 18, 7.5
    kat = Reference(ws, min_col=sx + 1, max_col=sx + 2, min_row=K + 1)
    farben = [f for *_, f in KATEGORIEN] + [NEU_FARBE, FREI_FARBE]
    for i, (n, *_), in enumerate(zusammen):
        rr = K + 2 + i
        ch.add_data(Reference(ws, min_col=sx + 1, max_col=sx + 2, min_row=rr), from_rows=True, titles_from_data=False)
        s = ch.series[-1]
        s.tx = SeriesLabel(v=n)
        s.graphicalProperties = GraphicalProperties(solidFill=farben[i])
    ch.set_categories(kat)
    ch.legend.position = "b"
    ch.y_axis.delete = False
    ch.x_axis.delete = False
    ws.add_chart(ch, f"I{r + 6}")

    for col, w in zip("ABCDEFGHIJK", (46, 20, 12, 20, 12, 13, 40, 3, 20, 11, 11)):
        ws.column_dimensions[col].width = w
    ws.row_dimensions[K].height = 30
    ws.freeze_panes = f"A{erste}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.cell(neu_bis + 2, 1, QUELLE).font = klein
    wb.save(pfad)


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--leer":
        daten, a = {}, a[1:]
    else:
        with open(a[0], encoding="utf-8") as f:
            daten = json.load(f)
        a = a[1:]
    ziele = dict(zip(a[::2], a[1::2]))
    if not ziele:
        ziele = {"--pptx": "jobprofil.pptx", "--xlsx": "aufgabenanalyse.xlsx"} if daten else \
            {"--xlsx": "aufgabenanalyse-leer.xlsx"}
    if "--pptx" in ziele:
        pptx(daten, ziele["--pptx"])
        print(f"Gespeichert: {ziele['--pptx']}")
    if "--xlsx" in ziele:
        excel(daten, ziele["--xlsx"])
        print(f"Gespeichert: {ziele['--xlsx']}")
    if daten.get("aufgaben"):
        print()
        print(auswertung(daten))


if __name__ == "__main__":
    main()
