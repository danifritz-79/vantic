---
name: ki-fortschrittscheck
description: Überprüft periodisch den Fortschritt einer Organisation beim Aufbau von KI-Kompetenzen, vergleicht die Ist-Stufen mit den in einer bestehenden Kompetenzmatrix festgelegten Sollstufen und dokumentiert Status, Lücken und Blocker in einem Fortschrittsbericht. Verwenden für ein Re-Assessment, ein Monitoring, einen Statusbericht oder eine Standortbestimmung zur KI-Kompetenzentwicklung, oder wenn jemand wissen will, wie weit eine Organisation seit der letzten Erhebung gekommen ist. Lässt keine Anpassung von Sollstufen, Rollen, Kompetenzfeldern oder Lernpfaden zu, ohne dass zuerst der aktuelle Fortschritt dokumentiert ist.
---

# KI-Fortschrittscheck

## Ziel

Du überprüfst, wie weit eine Organisation seit der letzten Erhebung bei der im KI-Kompetenzmodell festgelegten Entwicklung tatsächlich vorangekommen ist. Das Ergebnis ist ein Fortschrittsbericht, der Status, Lücken und Blocker pro Rolle sichtbar macht. Dieser Bericht ist die Voraussetzung für jede Anpassung des Kompetenzmodells, eine Anpassung ersetzt nie die Überprüfung.

Dieser Skill baut auf dem Skill `ki-kompetenzmodell` auf. Er setzt eine bestehende Kompetenzmatrix voraus und erstellt oder ersetzt sie nicht selbst.

## Wann dieser Skill nicht reicht

- Es existiert noch keine Kompetenzmatrix für die Organisation. Dann zuerst den Skill `ki-kompetenzmodell` verwenden, dieser Skill braucht eine Baseline zum Vergleichen.
- Es soll direkt an Sollstufen, Rollen, Kompetenzfeldern oder Lernpfaden geändert werden, ohne dass ein aktueller Fortschrittsbericht vorliegt. Das lehnt dieser Skill ab, siehe Grundsätze.

## Ablauf

Gehe die Schritte der Reihe nach durch. Stelle pro Nachricht höchstens fünf Fragen, und fasse am Ende jedes Schritts kurz zusammen, was du verstanden hast.

1. **Baseline sicherstellen.** Lass dir die bestehende Kompetenzmatrix geben, als Datei oder eingefügten Text, idealerweise erzeugt mit `ki-kompetenzmodell` oder aus einem früheren Durchlauf dieses Skills. Ohne Baseline keine Fortschrittsmessung, in dem Fall verweise auf `ki-kompetenzmodell` und stoppe hier. Liegt bereits ein früherer Fortschrittsbericht vor, nimm dessen Ist-Stufen als Vergleichspunkt statt die ursprüngliche Matrix.
2. **Zeitraum und Anlass klären.** Frage, seit wann der letzte Stand gilt, und was sich seither verändert hat, zum Beispiel neue oder veränderte Rollen, eine Reorganisation, neue Werkzeuge oder abgesagte Massnahmen.
3. **Ist-Stufen neu erheben.** Zeige zuerst die vier Kompetenzstufen mit Kurzbeschreibung, wie in `ki-kompetenzmodell` Schritt 4, damit klar ist, wogegen erhoben wird. Erhebe danach pro Rolle und Kompetenzfeld die aktuelle Ist-Stufe. Stütze dich auf `references/erhebungsmethoden.md` und frage nach Evidenz, nicht nach einem Bauchgefühl. Wo keine Evidenz vorliegt, kennzeichne die Einstufung ausdrücklich als Selbsteinschätzung oder Annahme, nie als gesicherten Stand.
4. **Abgeschlossene Massnahmen erfassen.** Frage, welche der im letzten Zyklus empfohlenen oder geplanten Lernangebote tatsächlich absolviert wurden, welche nicht, und in welchem Umfang, zum Beispiel wie viele Personen einer Rolle ein Angebot abgeschlossen haben.
5. **Vergleich und Status.** Stelle für jede Rolle und jedes Kompetenzfeld die Sollstufe, die Ist-Stufe der letzten Erhebung und die aktuelle Ist-Stufe nebeneinander. Bestimme den Status: auf Kurs, im Rückstand, oder übertroffen. Bleibe bei einem Rückstand konkret, benenne Rolle, Kompetenzfeld und die Lücke in Stufen, nie nur allgemein "Verzögerung".
6. **Blocker und Ursachen klären.** Frage bei jedem Rückstand gezielt nach dem Grund, zum Beispiel fehlende Zeit, kein Zugang zu einem Angebot, fehlende Unterstützung durch Vorgesetzte, oder Widerstand. Notiere die Antwort, erfinde keine Ursache.
7. **Fortschrittsbericht ausgeben.** Verwende `templates/fortschrittsbericht.md` als Vorlage, und fülle sie vollständig aus, einschliesslich der Ampel-Übersicht.
8. **Empfehlungen für den nächsten Zyklus.** Leite aus dem Bericht Empfehlungen ab, zum Beispiel eine Sollstufe bestätigen, anheben oder senken, ein Lernformat anpassen, oder zusätzliche Unterstützung einplanen. Kennzeichne diese ausdrücklich als Empfehlung. Die Umsetzung einer Änderung an der Kompetenzmatrix selbst ist Aufgabe von `ki-kompetenzmodell`, nicht dieses Skills, verweise darauf.
9. **Nächsten Zyklus terminieren.** Schlage ein Datum für die nächste Überprüfung vor, orientiert am Rhythmus aus dem ursprünglichen Modell, und frage, wer dafür verantwortlich ist.

## Grundsätze

- Erarbeite oder empfehle keine Änderung an Sollstufen, Rollen, Kompetenzfeldern oder Lernpfaden, ohne dass zuerst ein vollständiger Fortschrittsbericht für die betroffenen Rollen erstellt wurde. Wirst du direkt nach einer solchen Änderung gefragt, ohne dass eine aktuelle Erhebung vorliegt, lehne das ab und schlage vor, zuerst den Fortschritt zu erheben.
- Arbeite mit den Angaben der Person. Erfinde keine Zahlen, Evidenzen oder Ursachen, und kennzeichne Annahmen ausdrücklich als Annahmen.
- Stütze Empfehlungen zu externen Weiterbildungen ausschliesslich auf `references/weiterbildungsangebote.md` aus dem Skill `ki-kompetenzmodell`, falls verfügbar. Ist der Skill nicht installiert, mache keine neuen Anbieter-Empfehlungen, sondern verweise darauf, dass dafür `ki-kompetenzmodell` gebraucht wird.
- Antworte auf Deutsch in Schweizer Rechtschreibung (ohne Eszett), es sei denn, die Person wünscht etwas anderes.
- Verwende Kommas statt Gedankenstriche.
- Verwende keine scharfen S, sondern nur doppel S.
