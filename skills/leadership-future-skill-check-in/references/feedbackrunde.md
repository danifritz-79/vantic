# 360-Grad-Feedbackrunde

Die Feedbackrunde ergänzt die Selbsteinschätzung um die Wahrnehmung anderer. Erst der Vergleich zeigt, wo Selbst- und Fremdbild übereinstimmen, wo blinde Flecken liegen und welche Stärken die Führungskraft bei sich unterschätzt.

## Wer gibt Feedback

| Gruppe | Anzahl | Hinweis |
|---|---|---|
| Vorgesetzte | 1 bis 2 | nicht anonym, die Person ist erkennbar |
| Peers (Kolleginnen und Kollegen auf gleicher Stufe) | 3 bis 5 | anonym, erst ab 3 Rückmeldungen einzeln ausgewiesen |
| Mitarbeitende | 3 bis 6 | anonym, erst ab 3 Rückmeldungen einzeln ausgewiesen |
| Extern (optional, zum Beispiel Kundschaft oder Partner) | 2 bis 3 | fliesst nur in den Gesamtdurchschnitt ein |

Empfiehl insgesamt sechs bis zwölf Personen. Wähle Personen, die die Führungskraft im Alltag erleben, nicht nur solche, mit denen es gut läuft.

## Anonymität und Vertrauen

- Peers und Mitarbeitende werden erst ab drei Rückmeldungen als Gruppe ausgewiesen. Darunter fliessen ihre Werte nur in den Gesamtdurchschnitt ein. Das Excel-Profil setzt diese Regel automatisch um.
- Die Antworten sollten nicht direkt an die Führungskraft gehen, sondern an eine neutrale Stelle, zum Beispiel HR, eine Assistenz, eine externe Begleitung oder ein anonymes Umfragetool. Diese Stelle trägt die Werte ins Excel ein.
- Offene Antworten werden vor der Weitergabe so zusammengefasst, dass keine Person erkennbar ist.
- Den Feedbackgebenden vorher sagen, wer die Antworten sieht und wofür sie verwendet werden. Feedback aus dem Check-in wird nicht für Beurteilungen oder Lohnentscheide genutzt.

## Ablauf und Zeitplan

1. **Vorbereiten (Woche 1):** Feedbackgebende auswählen, neutrale Stelle bestimmen, Einladung und Fragebogen aus `templates/feedback-fragebogen.md` anpassen.
2. **Feedback einholen (Wochen 2 und 3):** Einladung versenden, Frist von zehn Arbeitstagen, nach einer Woche einmal freundlich erinnern.
3. **Erfassen (Woche 4):** Die neutrale Stelle trägt die Werte im Excel-Profil auf dem Blatt "Fremdeinschätzung" ein, eine Spalte pro Person, und fasst die offenen Antworten zusammen.
4. **Auswerten (Woche 4):** Gemeinsam mit Claude, siehe Ablauf in `SKILL.md`.
5. **Danke sagen und zurückmelden (Woche 5):** Den Feedbackgebenden danken und ihnen ein bis zwei Erkenntnisse und die geplanten Entwicklungsschritte zurückmelden. Das stärkt das Vertrauen für die nächste Runde.

## Auswertung

Vergleiche pro Teilaspekt Selbsteinschätzung, Fremdeinschätzung und Soll. Das Skript `scripts/profil.py` gibt diese Auswertung aus, eine Abweichung gilt ab 0.75 Stufen als deutlich.

| Muster | Bedeutung | Umgang |
|---|---|---|
| Selbst deutlich über Fremd | möglicher blinder Fleck | nachfragen, welches Verhalten andere wahrnehmen, nicht rechtfertigen |
| Fremd deutlich über Selbst | mögliche verborgene Stärke | bewusst machen und gezielter einsetzen |
| Selbst und Fremd ähnlich, beide unter Soll | erkannte Entwicklungslücke | gute Grundlage für ein Entwicklungsfeld |
| Selbst und Fremd ähnlich, auf oder über Soll | bestätigte Stärke | beibehalten, eventuell andere darin weiterbringen |
| Gruppen weichen stark voneinander ab | Verhalten unterscheidet sich je nach Gegenüber | genauer anschauen, zum Beispiel nach oben anders als nach unten |

Werte sind Hinweise, keine Urteile. Kleine Unterschiede bei wenigen Rückmeldungen nicht überinterpretieren, und offene Antworten immer zusammen mit den Zahlen lesen.

## Feedback gut aufnehmen

- Zuerst nur lesen und wirken lassen, nicht sofort erklären oder rechtfertigen.
- Nach Mustern suchen, nicht nach einzelnen Ausreissern oder danach, wer was gesagt hat.
- Wo etwas unklar ist, in einem Gespräch nach konkreten Situationen fragen, zum Beispiel: "Wo habt ihr erlebt, dass ich Konflikte nicht früh genug anspreche?"
- Sich bedanken, auch für unbequeme Rückmeldungen.
