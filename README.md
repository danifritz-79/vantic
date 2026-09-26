# Vantic Skills

Claude Skills von Vantic, mit Webseite zum Herunterladen und Installieren.

Jeder Ordner in `skills/` ist ein Skill. Bei jedem Hochladen auf GitHub baut ein Workflow daraus automatisch die Webseite, erzeugt pro Skill ein Zip und veröffentlicht alles über GitHub Pages.

## Aufbau

```
skills/
  ki-kompetenzmodell/
    SKILL.md          Anweisungen für Claude (Name und Beschreibung im Kopf)
    site.json         Angaben für die Webseite
    references/       Hintergrundwissen, das Claude bei Bedarf liest
    templates/        Vorlagen für die Ergebnisse
rezepte/              Ein .md-File pro Rezept, im Format des rezept-creator Skills
site/                 Webseite: index.html (Einstiegsseite), skills/index.html (Skills-Seite), rezepte/index.html (private Rezeptseite), Stil, Schriften, Logo
scripts/build.py      Baut die Webseite, die Zip-Dateien und die Rezeptseite
config.json           Name, GitHub-Adresse und Plugin-Name für die Installationsbefehle
.github/workflows/    Automatische Veröffentlichung
.claude-plugin/       Ermöglicht die Installation in Claude Code
```

## Neuen Skill hinzufügen

1. Lege in `skills/` einen neuen Ordner an. Der Ordnername ist die Kennung des Skills, kleingeschrieben und mit Bindestrichen, zum Beispiel `lernpfad-planer`.
2. Lege darin eine `SKILL.md` an. Der Kopf muss `name` (identisch mit dem Ordnernamen) und `description` enthalten, jeweils in einer Zeile:

   ```
   ---
   name: lernpfad-planer
   description: Was der Skill tut und wann Claude ihn verwenden soll.
   ---
   ```
3. Lege eine `site.json` daneben, mit den Angaben für die Webseite:

   | Feld | Bedeutung |
   |---|---|
   | `titel` | Name auf der Karte |
   | `kategorie` | Gruppe für den Filter, neue Kategorien entstehen automatisch |
   | `ebene` | `strategie`, `organisation` oder `mensch`, bestimmt die Farbe des Punkts (Anthrazit, Dunkelgrün, Gold) |
   | `reihenfolge` | Zahl, kleinere Zahlen stehen weiter oben |
   | `kurzbeschreibung` | Ein bis zwei Sätze für die Karte |
   | `einleitung` | Ausführlicher Text in der Detailansicht |
   | `punkte` | Liste mit drei Stichpunkten zu "Das macht der Skill" |
   | `du_gibst` | Was man dem Skill mitgeben muss |
   | `du_erhaeltst` | Was man zurückbekommt |
   | `beispielauftrag` | Ein Beispielsatz für Claude |

4. Lade den Ordner auf GitHub hoch. Nach ein bis zwei Minuten ist der Skill auf der Webseite sichtbar. Den Fortschritt siehst du im Reiter "Actions".

## Neues Rezept hinzufügen

Die Seite `/rezepte` ist nirgends verlinkt und nur über den direkten Link erreichbar (siehe `site/rezepte/index.html`, `<meta name="robots" content="noindex, nofollow">`).

1. Lass ein Rezept mit dem `rezept-creator` Skill erstellen. Ergänze am Skill die Anweisung, nach der Personenzahl eine Zeile mit ein oder mehreren Hashtags aus dieser Liste einzufügen: `#vorspeise`, `#sauce`, `#dessert`, `#vegetarisch`. Weitere Hashtags sind möglich, der Filter auf der Webseite entsteht automatisch aus allen vorkommenden Hashtags.
2. Speichere das Rezept als `.md`-Datei im Ordner `rezepte/`, Dateiname beliebig (z. B. `basilikum-pesto.md`).
3. Lade die Datei auf GitHub hoch. Nach ein bis zwei Minuten erscheint das Rezept automatisch auf `/rezepte`, inklusive Filter, keine Anpassung am Code nötig.

Der Build erwartet dieselbe Gliederung, die der `rezept-creator` Skill erzeugt: einen Titel (`#` oder `##`), eine fett gesetzte Zeile "Für X Personen", danach `**Zutaten**` und `**Zubereitung**`, je mit fett gesetzten Teilkomponenten-Titeln, und optional `**Notiz**` am Schluss.

Fehlt die `site.json`, erscheint der Skill trotzdem, mit Standardwerten. Ist die `SKILL.md` fehlerhaft, wird der Skill übersprungen, und im Protokoll der Action steht eine Warnung.

## Lokal testen

```
python3 scripts/build.py
python3 -m http.server -d dist 8000
```

Danach die Seite unter http://localhost:8000 öffnen. Die Datei `index.html` direkt zu öffnen funktioniert nicht, weil sie `skills.json` nachlädt.

## Veröffentlichung

- GitHub, Settings, Pages: Bei "Source" die Option "GitHub Actions" wählen.
- Eigene Domain: In denselben Einstellungen bei "Custom domain" eintragen, die DNS-Einträge bei Hostpoint setzen und danach "Enforce HTTPS" aktivieren.

## Installation in Claude Code

Die Datei `.claude-plugin/marketplace.json` macht dieses Repository zu einer Plugin-Quelle:

```
/plugin marketplace add danifritz-79/vantic
/plugin install vantic-skills@vantic
```

Damit werden alle Skills auf einmal installiert. Einzelne Skills lassen sich über das Zip von der Webseite installieren.

## Vor der Veröffentlichung klären

- Lizenz: Lege fest, was andere mit den Skills tun dürfen, und füge eine Datei `LICENSE` hinzu.
- Impressum und Datenschutz: Die Platzhalter in `site/impressum.html` und `site/datenschutz.html` ausfüllen und rechtlich prüfen lassen.
- Texte im Bereich "Über uns" und die E-Mail-Adresse in `site/index.html` ersetzen.

## Schriften

Die Schriften Familjen Grotesk und Source Serif 4 liegen lokal in `site/assets/fonts`, damit beim Besuch keine Daten an Dritte gehen. Beide stehen unter der SIL Open Font License, die Lizenztexte liegen im selben Ordner.
