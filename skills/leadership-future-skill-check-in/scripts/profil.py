#!/usr/bin/env python3
"""Erzeugt das Kompetenzprofil zum Leadership Future Skill Check-in.

Aufruf:
    python3 profil.py daten.json --png profil.png --xlsx profil.xlsx --pptx profil.pptx
    python3 profil.py --leer --xlsx profil-leer.xlsx

--png   Spider-Diagramm mit Selbsteinschätzung, Soll und Fremdeinschätzung (16 Teilaspekte und 4 Kernbereiche)
--xlsx  Excel-Profil: Selbsteinschätzung, Eingabeblatt für bis zu 12 Fremdeinschätzungen, Spider-Diagramme,
        die sich beim Eintragen automatisch aktualisieren
--pptx  PowerPoint mit zwei Folien: Spider-Diagramm und Selbst- und Fremdbild auf einen Blick
Ohne Angabe werden alle drei Dateien erzeugt (profil.png, profil.xlsx, profil.pptx).

Gibt zusätzlich eine Auswertung der Abweichungen aus (Abstand zum Soll, blinde Flecken, verborgene Stärken).
Benötigt matplotlib (für --png und --pptx), openpyxl (für --xlsx) und python-pptx (für --pptx).
"""
import json
import sys
import textwrap

QUELLE = "Leadership Future Skill Check-in von Vantic  ·  vantic.ch"

KERNBEREICHE = [
    ("Eigenorganisation", "9AA1A8", [
        ("prioritaeten", "Prioritäten setzen"),
        ("belastung", "Umgang mit Belastung"),
        ("lernen", "Eigenverantwortung für Lernen"),
        ("grenzen", "Grenzen setzen"),
    ]),
    ("Tech-Affinität", "33383D", [
        ("neugier", "Neugier für Neues"),
        ("ki_alltag", "KI im Arbeitsalltag"),
        ("ki_pruefen", "KI-Ergebnisse prüfen"),
        ("chancen_risiken", "Chancen und Risiken einschätzen"),
    ]),
    ("Business-Verständnis", "0F3D2E", [
        ("wertschoepfung", "Wertschöpfung verstehen"),
        ("kennzahlen", "Kennzahlen lesen"),
        ("wirkung", "Wirkung von Entscheidungen"),
        ("begruenden", "Wirtschaftlich begründen"),
    ]),
    ("Soziokulturelles Gespür", "E2B04A", [
        ("kommunikation", "Klar kommunizieren"),
        ("zusammenarbeit", "Zusammenarbeit gestalten"),
        ("konflikte", "Konflikte lösen"),
        ("veraenderung", "Veränderung mit Menschen gestalten"),
    ]),
]
TEILASPEKTE = [(kb, tid, name) for kb, _, teile in KERNBEREICHE for tid, name in teile]
GRUPPEN = ["Vorgesetzte", "Peer", "Mitarbeitende", "Extern"]
SCHWELLE = 0.75  # Abweichung in Stufen, ab der Selbst und Fremd als deutlich verschieden gelten
MIN_ANONYM = 3  # Mindestzahl Rückmeldungen, bevor eine Gruppe einzeln ausgewiesen wird

GRUEN, GOLD, GOLD_TIEF, ANTHRAZIT = "#0F3D2E", "#E2B04A", "#A87A0A", "#33383D"
GRUND, TINTE, GEDAEMPFT = "#F2F3EC", "#14231C", "#3F4B44"


# ---------- Auswertung ----------

def mittel(werte):
    werte = [w for w in werte if isinstance(w, (int, float))]
    return sum(werte) / len(werte) if werte else None


def fremd_mittel(daten):
    """Durchschnitt aller Fremdeinschätzungen pro Teilaspekt, und pro Gruppe (nur ab MIN_ANONYM, Vorgesetzte immer)."""
    fremd = daten.get("fremd", [])
    gesamt = {tid: mittel([f.get("werte", {}).get(tid) for f in fremd]) for _, tid, _ in TEILASPEKTE}
    gruppen = {}
    for g in GRUPPEN:
        antworten = [f for f in fremd if f.get("gruppe") == g]
        if antworten and (g == "Vorgesetzte" or len(antworten) >= MIN_ANONYM):
            gruppen[g] = {tid: mittel([f.get("werte", {}).get(tid) for f in antworten]) for _, tid, _ in TEILASPEKTE}
    return gesamt, gruppen, len(fremd)


def auswertung(daten):
    selbst = daten.get("selbst", {})
    soll = daten.get("soll", {})
    fremd, gruppen, anzahl = fremd_mittel(daten)
    zeilen = ["AUSWERTUNG", ""]
    zeilen.append("Grösster Abstand zum Soll (Soll minus Selbst):")
    abstaende = sorted(((soll.get(t, 0) or 0) - (selbst.get(t, 0) or 0), n) for _, t, n in TEILASPEKTE
                       if selbst.get(t) is not None and soll.get(t) is not None)
    for a, n in reversed(abstaende[-5:]):
        if a > 0:
            zeilen.append(f"  {n}: {a:+.0f}")
    if anzahl:
        zeilen += ["", f"Fremdeinschätzungen: {anzahl}, ausgewiesene Gruppen: {', '.join(gruppen) or 'keine (zu wenige pro Gruppe)'}"]
        blind = [(selbst[t] - fremd[t], n) for _, t, n in TEILASPEKTE
                 if selbst.get(t) is not None and fremd.get(t) is not None and selbst[t] - fremd[t] >= SCHWELLE]
        verborgen = [(fremd[t] - selbst[t], n) for _, t, n in TEILASPEKTE
                     if selbst.get(t) is not None and fremd.get(t) is not None and fremd[t] - selbst[t] >= SCHWELLE]
        zeilen.append(f"Mögliche blinde Flecken (Selbst mindestens {SCHWELLE} Stufen über Fremd):")
        zeilen += [f"  {n}: Selbst {d:+.1f} gegenüber Fremd" for d, n in sorted(blind, reverse=True)] or ["  keine"]
        zeilen.append(f"Mögliche verborgene Stärken (Fremd mindestens {SCHWELLE} Stufen über Selbst):")
        zeilen += [f"  {n}: Fremd {d:+.1f} gegenüber Selbst" for d, n in sorted(verborgen, reverse=True)] or ["  keine"]
        zeilen.append(f"Fremd unter Soll um mindestens {SCHWELLE} Stufen:")
        unter = [(soll[t] - fremd[t], n) for _, t, n in TEILASPEKTE
                 if soll.get(t) is not None and fremd.get(t) is not None and soll[t] - fremd[t] >= SCHWELLE]
        zeilen += [f"  {n}: {d:.1f} Stufen" for d, n in sorted(unter, reverse=True)] or ["  keine"]
    return "\n".join(zeilen)


# ---------- Spider-Diagramm (PNG) ----------

def spider_png(daten, pfad):
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from matplotlib import font_manager
    vorhanden = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((f for f in ("Arial", "Liberation Sans", "Helvetica", "DejaVu Sans")
                                         if f in vorhanden), "sans-serif")
    selbst, soll = daten.get("selbst", {}), daten.get("soll", {})
    fremd, gruppen, anzahl = fremd_mittel(daten)

    fig = plt.figure(figsize=(16, 9), facecolor=GRUND)
    fig.text(0.04, 0.945, "Leadership Future Skill Check-in", fontsize=20, fontweight="bold", color=TINTE)
    unter = " · ".join(x for x in (daten.get("name", ""), daten.get("rolle", ""), daten.get("datum", "")) if x)
    fig.text(0.04, 0.91, unter, fontsize=11.5, color=GEDAEMPFT)
    fig.text(0.04, 0.025, f"Stufen: 1 Entdecken, 2 Anwenden, 3 Souverän, 4 Prägend.   {QUELLE}",
             fontsize=8.5, color=GEDAEMPFT)

    def achse(rect, labels, label_farben, sektoren, reihen, titel, labelgroesse, umbruch):
        """sektoren: Liste (Farbe, erster Index, Anzahl Achsen)."""
        ax = fig.add_axes(rect, polar=True, facecolor="white")
        n = len(labels)
        schritt = 2 * math.pi / n
        winkel = [schritt * i for i in range(n)]
        ax.set_theta_offset(math.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 4.45)
        ax.set_yticks([1, 2, 3, 4])
        ax.set_yticklabels(["1", "2", "3", "4"], fontsize=8, color=GEDAEMPFT)
        ax.set_rlabel_position(schritt / 2 * 180 / math.pi)
        ax.set_xticks(winkel)
        ax.set_xticklabels([textwrap.fill(l, umbruch, break_long_words=False) for l in labels],
                           fontsize=labelgroesse)
        for t, farbe in zip(ax.get_xticklabels(), label_farben):
            t.set_color(farbe)
            t.set_fontweight("bold")
        ax.tick_params(axis="x", pad=16 if n > 4 else 26)
        ax.grid(color="#D2D9CF", linewidth=0.8)
        ax.spines["polar"].set_visible(False)
        # Sektoren und farbiger Aussenring je Kernbereich
        for farbe, erste, anzahl in sektoren:
            mitte = schritt * (erste + (anzahl - 1) / 2)
            ax.bar(mitte, 0.16, width=schritt * anzahl * 0.98, bottom=4.25, color="#" + farbe,
                   alpha=0.9, edgecolor="none", zorder=1)
        for name, werte, stil in reihen:
            if all(w is None for w in werte):
                continue
            werte = [w if w is not None else 0 for w in werte]
            w2, v2 = winkel + winkel[:1], werte + werte[:1]
            ax.plot(w2, v2, label=name, zorder=3, **stil["linie"])
            if stil.get("fuellung"):
                ax.fill(w2, v2, color=stil["fuellung"], alpha=0.14, zorder=2)
        fig.text(rect[0] + rect[2] / 2, rect[1] + rect[3] + 0.075, titel, ha="center",
                 fontsize=13, fontweight="bold", color=TINTE)
        return ax, winkel

    stile = {
        "Soll": {"linie": dict(color=GOLD_TIEF, linewidth=2, linestyle="--")},
        "Selbst": {"linie": dict(color=GRUEN, linewidth=2.4, marker="o", markersize=4.5), "fuellung": GRUEN},
        "Fremd": {"linie": dict(color=ANTHRAZIT, linewidth=2.2, marker="s", markersize=4.5, linestyle="-")},
    }
    gruppen_farben = ["#7A8A99", "#C08A2E", "#4E8C6E", "#8E6C8A"]

    def reihen_fuer(ids):
        r = [("Soll", [soll.get(t) for t in ids], stile["Soll"]),
             ("Selbsteinschätzung", [selbst.get(t) for t in ids], stile["Selbst"])]
        if anzahl:
            r.append((f"Fremdeinschätzung Ø ({anzahl})", [fremd.get(t) for t in ids], stile["Fremd"]))
        return r

    ids = [t for _, t, _ in TEILASPEKTE]
    textfarbe = {"9AA1A8": "#5F6872", "33383D": ANTHRAZIT, "0F3D2E": GRUEN, "E2B04A": GOLD_TIEF}
    label_farben = [textfarbe[farbe] for _, farbe, teile in KERNBEREICHE for _ in teile]
    sektoren = [(farbe, 4 * k, 4) for k, (_, farbe, _) in enumerate(KERNBEREICHE)]
    ax1, winkel = achse([0.07, 0.1, 0.46, 0.68], [n for _, _, n in TEILASPEKTE], label_farben, sektoren,
                        reihen_fuer(ids), "16 Teilaspekte", 9, 18)
    # zusätzliche Linien je ausgewiesener Gruppe
    if gruppen:
        for (g, werte), farbe in zip(gruppen.items(), gruppen_farben):
            v = [werte.get(t) for t in ids]
            if all(x is None for x in v):
                continue
            v = [x if x is not None else 0 for x in v]
            ax1.plot(winkel + winkel[:1], v + v[:1], color=farbe, linewidth=1.2, linestyle=":", label=f"Fremd {g}")

    def kb_mittel(quelle):
        return [mittel([quelle.get(t) for t, _ in teile]) for _, _, teile in KERNBEREICHE]

    kb_reihen = [("Soll", kb_mittel(soll), stile["Soll"]), ("Selbsteinschätzung", kb_mittel(selbst), stile["Selbst"])]
    if anzahl:
        kb_reihen.append(("Fremdeinschätzung Ø", kb_mittel(fremd), stile["Fremd"]))
    achse([0.68, 0.37, 0.24, 0.36], [k for k, _, _ in KERNBEREICHE],
          [textfarbe[f] for _, f, _ in KERNBEREICHE], [(f, k, 1) for k, (_, f, _) in enumerate(KERNBEREICHE)],
          kb_reihen, "4 Kernbereiche (Durchschnitt)", 10, 14)

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(0.64, 0.08), frameon=False, fontsize=10.5)
    if not anzahl:
        fig.text(0.645, 0.06, "Fremdeinschätzung folgt nach der Feedbackrunde.", fontsize=9.5,
                 color=GEDAEMPFT, style="italic")
    fig.savefig(pfad, dpi=150, facecolor=GRUND)
    plt.close(fig)


# ---------- Excel-Profil ----------

def excel(daten, pfad):
    from openpyxl import Workbook
    from openpyxl.chart import RadarChart, Reference
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.drawing.line import LineProperties
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    pr = wb.active
    pr.title = "Profil"
    fe = wb.create_sheet("Fremdeinschätzung")
    an = wb.create_sheet("Anleitung")

    titel = Font(name="Arial", size=16, bold=True, color="14231C")
    fett = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    normal = Font(name="Arial", size=10, color="14231C")
    klein = Font(name="Arial", size=9, color="3F4B44", italic=True)
    kopf_fill = PatternFill("solid", fgColor="33383D")
    eingabe_fill = PatternFill("solid", fgColor="FFF6DE")
    rechnung_fill = PatternFill("solid", fgColor="EEF3EC")
    duenn = Side(style="thin", color="D2D9CF")
    rahmen = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)
    stufe_dv = DataValidation(type="whole", operator="between", formula1="1", formula2="4", allow_blank=True,
                              error="Bitte eine Stufe von 1 bis 4 eintragen.", errorTitle="Ungültige Stufe")

    selbst, soll = daten.get("selbst", {}), daten.get("soll", {})
    fremd_liste = daten.get("fremd", [])[:12]

    # --- Fremdeinschätzung ---
    fe["A1"] = "Fremdeinschätzung aus der Feedbackrunde"
    fe["A1"].font = titel
    fe["A2"] = ("Pro Person eine Spalte. Gruppe wählen, dann die Stufen 1 bis 4 eintragen, leer lassen bei "
                "'kann ich nicht beurteilen'. Peers und Mitarbeitende werden erst ab 3 Rückmeldungen einzeln ausgewiesen.")
    fe["A2"].font = klein
    fe["A4"], fe["A5"] = "Gruppe", "Kürzel (optional)"
    for c in ("A4", "A5"):
        fe[c].font = Font(name="Arial", size=10, bold=True)
    gruppe_dv = DataValidation(type="list", formula1='"' + ",".join(GRUPPEN) + '"', allow_blank=True)
    fe.add_data_validation(gruppe_dv)
    fe.add_data_validation(stufe_dv)
    erste, letzte = 3, 14  # Spalten C bis N
    for i in range(12):
        col = get_column_letter(erste + i)
        fe[f"{col}4"].fill = eingabe_fill
        fe[f"{col}5"].fill = eingabe_fill
        gruppe_dv.add(f"{col}4")
        if i < len(fremd_liste):
            fe[f"{col}4"] = fremd_liste[i].get("gruppe", "")
            fe[f"{col}5"] = fremd_liste[i].get("kuerzel", f"P{i + 1}")
        fe.column_dimensions[col].width = 13
    kopfzeile = 6
    for c, text in zip(("A", "B"), ("Kernbereich", "Teilaspekt")):
        fe[f"{c}{kopfzeile}"] = text
    for i in range(12):
        fe.cell(kopfzeile, erste + i, f"P{i + 1}")
    zusatz = ["Ø alle", "Ø Vorgesetzte", "Ø Peers", "Ø Mitarbeitende", "Anzahl"]
    for i, text in enumerate(zusatz):
        fe.cell(kopfzeile, letzte + 1 + i, text)
    for cell in fe[kopfzeile]:
        if cell.value:
            cell.font, cell.fill = fett, kopf_fill
    bereich_kopf = f"${get_column_letter(erste)}$4:${get_column_letter(letzte)}$4"
    for r, (kb, tid, name) in enumerate(TEILASPEKTE, start=kopfzeile + 1):
        fe.cell(r, 1, kb).font = normal
        fe.cell(r, 2, name).font = normal
        werte = f"{get_column_letter(erste)}{r}:{get_column_letter(letzte)}{r}"
        for i in range(12):
            z = fe.cell(r, erste + i)
            z.fill, z.border, z.alignment = eingabe_fill, rahmen, Alignment(horizontal="center")
            stufe_dv.add(z.coordinate)
            if i < len(fremd_liste):
                w = fremd_liste[i].get("werte", {}).get(tid)
                if w is not None:
                    z.value = w
        o = letzte + 1
        fe.cell(r, o, f'=IFERROR(ROUND(AVERAGE({werte}),1),"")')
        fe.cell(r, o + 1, f'=IFERROR(ROUND(AVERAGEIF({bereich_kopf},"Vorgesetzte",{werte}),1),"")')
        for k, g in ((2, "Peer"), (3, "Mitarbeitende")):
            fe.cell(r, o + k, f'=IF(COUNTIFS({bereich_kopf},"{g}",{werte},">0")>={MIN_ANONYM},'
                              f'ROUND(AVERAGEIF({bereich_kopf},"{g}",{werte}),1),"")')
        fe.cell(r, o + 4, f"=COUNT({werte})")
        for k in range(5):
            fe.cell(r, o + k).fill = rechnung_fill
            fe.cell(r, o + k).alignment = Alignment(horizontal="center")
    fe.column_dimensions["A"].width = 24
    fe.column_dimensions["B"].width = 32
    for k in range(5):
        fe.column_dimensions[get_column_letter(letzte + 1 + k)].width = 15
    fe.freeze_panes = "C7"

    # --- Profil ---
    pr["A1"] = "Leadership Future Skill Check-in"
    pr["A1"].font = titel
    pr["A2"] = " · ".join(x for x in (daten.get("name", ""), daten.get("rolle", ""), daten.get("datum", "")) if x) \
        or "Name · Rolle · Datum"
    pr["A2"].font = klein
    pr["A3"] = "Stufen: 1 Entdecken, 2 Anwenden, 3 Souverän, 4 Prägend. Gelbe Felder sind Eingaben, grüne werden berechnet."
    pr["A3"].font = klein
    kopf = ["Kernbereich", "Teilaspekt", "Selbst (Ist)", "Soll", "Fremd Ø", "Soll minus Selbst",
            "Selbst minus Fremd", "Diagramm Fremd"]
    for i, text in enumerate(kopf, start=1):
        z = pr.cell(5, i, text)
        z.font, z.fill = fett, kopf_fill
        z.alignment = Alignment(horizontal="center", wrap_text=True)
    pr.add_data_validation(stufe_dv2 := DataValidation(type="whole", operator="between", formula1="1",
                                                       formula2="4", allow_blank=True))
    for r, (kb, tid, name) in enumerate(TEILASPEKTE, start=6):
        fr = r - 6 + kopfzeile + 1
        pr.cell(r, 1, kb).font = normal
        pr.cell(r, 2, name).font = normal
        for c, quelle in ((3, selbst), (4, soll)):
            z = pr.cell(r, c, quelle.get(tid))
            z.fill = eingabe_fill
            stufe_dv2.add(z.coordinate)
        pr.cell(r, 5, f"='Fremdeinschätzung'!{get_column_letter(letzte + 1)}{fr}")
        pr.cell(r, 6, f'=IF(OR(C{r}="",D{r}=""),"",D{r}-C{r})')
        pr.cell(r, 7, f'=IF(OR(C{r}="",E{r}=""),"",ROUND(C{r}-E{r},1))')
        pr.cell(r, 8, f'=IF(E{r}="",NA(),E{r})')
        for c in range(1, 9):
            pr.cell(r, c).border = rahmen
            if c >= 3:
                pr.cell(r, c).alignment = Alignment(horizontal="center")
            if c >= 5:
                pr.cell(r, c).fill = rechnung_fill
    pr.cell(5, 8).font = Font(name="Arial", size=8, color="FFFFFF")
    for c in range(1, 9):
        pr.cell(5, c).border = rahmen

    kb_kopf = 24
    for i, text in enumerate(["Kernbereich", "", "Selbst Ø", "Soll Ø", "Fremd Ø", "Soll minus Selbst",
                              "Selbst minus Fremd", "Diagramm Fremd"], start=1):
        z = pr.cell(kb_kopf, i, text)
        z.font, z.fill = fett, kopf_fill
        z.alignment = Alignment(horizontal="center", wrap_text=True)
    for k, (kb, _, teile) in enumerate(KERNBEREICHE):
        r = kb_kopf + 1 + k
        von, bis = 6 + 4 * k, 9 + 4 * k
        pr.cell(r, 1, kb).font = Font(name="Arial", size=10, bold=True)
        for c, col in ((3, "C"), (4, "D"), (5, "E")):
            pr.cell(r, c, f'=IFERROR(ROUND(AVERAGE({col}{von}:{col}{bis}),1),"")')
        pr.cell(r, 6, f'=IF(OR(C{r}="",D{r}=""),"",ROUND(D{r}-C{r},1))')
        pr.cell(r, 7, f'=IF(OR(C{r}="",E{r}=""),"",ROUND(C{r}-E{r},1))')
        pr.cell(r, 8, f'=IF(E{r}="",NA(),E{r})')
        for c in range(1, 9):
            pr.cell(r, c).border = rahmen
            pr.cell(r, c).fill = rechnung_fill
            if c >= 3:
                pr.cell(r, c).alignment = Alignment(horizontal="center")
    pr.cell(31, 1, QUELLE).font = klein

    for col, w in zip("ABCDEFGH", (24, 32, 11, 9, 10, 11, 11, 10)):
        pr.column_dimensions[col].width = w
    pr.row_dimensions[5].height = 30
    pr.row_dimensions[kb_kopf].height = 30
    pr.freeze_panes = "A6"
    for blatt in (pr, fe):
        blatt.page_setup.orientation = "landscape"
        blatt.page_setup.paperSize = blatt.PAPERSIZE_A4
        blatt.page_setup.fitToWidth, blatt.page_setup.fitToHeight = 1, 1
        blatt.sheet_properties.pageSetUpPr.fitToPage = True

    def radar(titel, erste_zeile, letzte_zeile, breite, hoehe):
        ch = RadarChart()
        ch.type = "marker"
        ch.style = 2
        ch.title = titel
        ch.width, ch.height = breite, hoehe
        ch.y_axis.scaling.min, ch.y_axis.scaling.max = 0, 4
        ch.y_axis.majorUnit = 1
        ch.y_axis.delete = False
        kategorien = Reference(pr, min_col=2 if erste_zeile == 6 else 1, min_row=erste_zeile, max_row=letzte_zeile)
        for col, name, farbe, strich in ((4, "Soll", "A87A0A", "dash"), (3, "Selbst", "0F3D2E", None),
                                          (8, "Fremd", "33383D", None)):
            ref = Reference(pr, min_col=col, min_row=erste_zeile, max_row=letzte_zeile)
            ch.add_data(ref, titles_from_data=False)
            s = ch.series[-1]
            from openpyxl.chart.series import SeriesLabel
            s.tx = SeriesLabel(v=name)
            s.graphicalProperties = GraphicalProperties(ln=LineProperties(solidFill=farbe, w=28000,
                                                                          prstDash=strich or "solid"))
            s.marker.symbol = "circle" if name != "Soll" else "none"
            s.marker.size = 5
            s.marker.graphicalProperties = GraphicalProperties(solidFill=farbe, ln=LineProperties(solidFill=farbe))
        ch.set_categories(kategorien)
        ch.legend.position = "b"
        return ch

    pr.add_chart(radar("16 Teilaspekte", 6, 21, 20, 13.5), "J2")
    pr.add_chart(radar("4 Kernbereiche", kb_kopf + 1, kb_kopf + 4, 13, 10), "J30")

    # --- Anleitung ---
    texte = [
        ("Leadership Future Skill Check-in, Anleitung", titel),
        ("", normal),
        ("1. Blatt 'Profil': Selbsteinschätzung (Ist) und Soll pro Teilaspekt in die gelben Felder eintragen, Stufen 1 bis 4.", normal),
        ("2. Feedbackrunde durchführen, siehe Fragebogen aus dem Skill.", normal),
        ("3. Blatt 'Fremdeinschätzung': pro Person eine Spalte, Gruppe wählen, Stufen eintragen.", normal),
        ("4. Die Spider-Diagramme im Blatt 'Profil' aktualisieren sich automatisch.", normal),
        ("", normal),
        ("Stufen: 1 Entdecken, 2 Anwenden, 3 Souverän, 4 Prägend.", normal),
        (f"Selbst minus Fremd ab +{SCHWELLE}: möglicher blinder Fleck. Ab -{SCHWELLE}: mögliche verborgene Stärke.", normal),
        (f"Anonymität: Peers und Mitarbeitende werden erst ab {MIN_ANONYM} Rückmeldungen einzeln ausgewiesen.", normal),
        ("", normal),
        (QUELLE, klein),
    ]
    for i, (t, f) in enumerate(texte, start=1):
        an.cell(i, 1, t).font = f
    an.column_dimensions["A"].width = 110
    wb.move_sheet("Anleitung", offset=-2)
    wb.active = 1
    wb.save(pfad)


# ---------- PowerPoint ----------

def muster(daten):
    """Ordnet die Teilaspekte den Mustern aus references/feedbackrunde.md zu."""
    selbst, soll = daten.get("selbst", {}), daten.get("soll", {})
    fremd, _, anzahl = fremd_mittel(daten)
    m = {"staerken": [], "verborgen": [], "blind": [], "luecken": []}
    for _, t, n in TEILASPEKTE:
        s, z, f = selbst.get(t), soll.get(t), fremd.get(t)
        if s is None or z is None:
            continue
        if anzahl and f is not None:
            if f - s >= SCHWELLE:
                m["verborgen"].append(f"{n}: Selbst {s}, Fremd {f:.1f}")
            elif s - f >= SCHWELLE:
                m["blind"].append(f"{n}: Selbst {s}, Fremd {f:.1f}")
            elif s >= z and f >= z - 0.25:
                m["staerken"].append(f"{n}: Selbst {s}, Fremd {f:.1f}, Soll {z}")
            if z - s >= 1 and z - f >= SCHWELLE:
                m["luecken"].append(f"{n}: Soll {z}, Selbst {s}, Fremd {f:.1f}")
        else:
            if s >= z and s >= 3:
                m["staerken"].append(f"{n}: Selbst {s}, Soll {z}")
            if z - s >= 1:
                m["luecken"].append(f"{n}: Soll {z}, Selbst {s}")
    return m, anzahl


def pptx(daten, pfad):
    import os
    import tempfile
    from pathlib import Path
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt

    def farbe(h):
        return RGBColor.from_string(h.lstrip("#"))

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    logo = Path(__file__).resolve().parent.parent / "assets" / "vantic-logo-liegend.png"

    def text(folie, x, y, b, h, absaetze):
        tf = folie.shapes.add_textbox(x, y, b, h).text_frame
        tf.word_wrap = True
        for i, (t, groesse, fett, f) in enumerate(absaetze):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_before = Pt(0 if i == 0 else 4)
            r = p.add_run()
            r.text = t
            r.font.name, r.font.size, r.font.bold = "Arial", Pt(groesse), fett
            r.font.color.rgb = farbe(f)

    def flaeche(folie, x, y, b, h, f, linie=None):
        s = folie.shapes.add_shape(1, x, y, b, h)
        s.fill.solid()
        s.fill.fore_color.rgb = farbe(f)
        if linie:
            s.line.color.rgb = farbe(linie)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        return s

    # Folie 1: Spider-Diagramm, als Bild über die ganze Folie
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    spider_png(daten, tmp.name)
    f1 = prs.slides.add_slide(prs.slide_layouts[6])
    f1.shapes.add_picture(tmp.name, 0, 0, width=prs.slide_width)
    if logo.exists():
        f1.shapes.add_picture(str(logo), Inches(11.0), Inches(0.3), height=Inches(0.45))
    os.unlink(tmp.name)

    # Folie 2: Selbst- und Fremdbild auf einen Blick
    m, anzahl = muster(daten)
    f2 = prs.slides.add_slide(prs.slide_layouts[6])
    flaeche(f2, 0, 0, prs.slide_width, prs.slide_height, GRUND)
    unter = " · ".join(x for x in (daten.get("name", ""), daten.get("datum", "")) if x)
    text(f2, Inches(0.5), Inches(0.32), Inches(10), Inches(0.9), [
        ("Selbst- und Fremdbild auf einen Blick" if anzahl else "Selbstbild auf einen Blick", 22, True, TINTE),
        (unter + (f"  ·  {anzahl} Fremdeinschätzungen" if anzahl else "  ·  Fremdeinschätzung folgt"), 12, False,
         GEDAEMPFT)])
    if logo.exists():
        f2.shapes.add_picture(str(logo), Inches(10.95), Inches(0.38), height=Inches(0.5))
    karten = [
        ("Bestätigte Stärken", "Selbst und Fremd auf Soll" if anzahl else "Selbst auf oder über Soll",
         m["staerken"], GRUEN, "FFFFFF", "CBD9CF"),
        ("Verborgene Stärken", "Andere sehen mehr, als du dir zutraust", m["verborgen"], GOLD, TINTE, TINTE),
        ("Mögliche blinde Flecken", "Du schätzt dich höher ein als andere", m["blind"], ANTHRAZIT, "FFFFFF",
         "D2D9CF"),
        ("Lücken zum Soll", "Selbst und Fremd unter Soll" if anzahl else "Mindestens eine Stufe unter Soll",
         m["luecken"], "FFFFFF", TINTE, GEDAEMPFT),
    ]
    b, h, luecke = Inches(6.12), Inches(2.6), Inches(0.1)
    for i, (titel, erkl, punkte, hg, schrift, neben) in enumerate(karten):
        x = Inches(0.5) + (i % 2) * (b + luecke)
        y = Inches(1.5) + (i // 2) * (h + luecke)
        flaeche(f2, x, y, b, h, hg, linie="D2D9CF" if hg == "FFFFFF" else None)
        if not anzahl and i in (1, 2):
            punkte = ["Wird nach der Feedbackrunde sichtbar."]
        punkte = punkte or ["keine"]
        g = 12 if len(punkte) <= 5 else 10.5
        text(f2, x + Inches(0.25), y + Inches(0.18), b - Inches(0.5), h - Inches(0.3),
             [(titel, 15, True, schrift), (erkl, 10.5, False, neben)] +
             [("•  " + p, g, False, schrift) for p in punkte[:7]] +
             ([(f"und {len(punkte) - 7} weitere", 10, False, neben)] if len(punkte) > 7 else []))
    text(f2, Inches(0.5), prs.slide_height - Inches(0.42), Inches(12.3), Inches(0.3), [
        (f"Stufen: 1 Entdecken, 2 Anwenden, 3 Souverän, 4 Prägend.   Deutliche Abweichung ab {SCHWELLE} Stufen."
         f"   {QUELLE}", 9, False, GEDAEMPFT)])
    prs.save(pfad)


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--leer":
        daten, args = {}, args[1:]
    else:
        with open(args[0], encoding="utf-8") as f:
            daten = json.load(f)
        args = args[1:]
    ziele = dict(zip(args[::2], args[1::2]))
    if not ziele:
        ziele = {"--png": "profil.png", "--xlsx": "profil.xlsx", "--pptx": "profil.pptx"} if daten else {"--xlsx": "profil-leer.xlsx"}
    if "--png" in ziele:
        spider_png(daten, ziele["--png"])
        print(f"Gespeichert: {ziele['--png']}")
    if "--xlsx" in ziele:
        excel(daten, ziele["--xlsx"])
        print(f"Gespeichert: {ziele['--xlsx']}")
    if "--pptx" in ziele:
        pptx(daten, ziele["--pptx"])
        print(f"Gespeichert: {ziele['--pptx']}")
    if daten.get("selbst"):
        print()
        print(auswertung(daten))


if __name__ == "__main__":
    main()
