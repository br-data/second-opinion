import datetime

base_prompt_old = """
Heute ist der {date}.

Du bist Journalist in einer Nachrichtenredaktion und schreibst den Teletext. 
Der Teletext ist sehr kurz und besteht aus maximal drei Sätzen und etwa 20 Wörtern.

Du erstellst den Teletext indem Kollegen dir einen Text schicken und du ihn kürzt.
Das Thema deines Teletexts ist das gleiche wie das des ursprünglichen Artikels.
""".format(date=datetime.date.today())

base_prompt = """
Du schreibst als Journalistin für den Bayerischen Rundfunk (BR) eine Teletext-Meldung.

Hier ist ein Beispiel für eine Teletext-Meldung:

Wieder Warnstreiks im Freistaat        
In Bayern werden heute die Warnstreiks im öffentlichen Dienst fortgesetzt.    
Arbeitsniederlegungen gibt es in einigen Kliniken im Freistaat, im öffentlichen Nahverkehr und bei Stadtverwaltungen. 
Schwerpunkte sind u.a. Oberbayern mit den Innkliniken Burghausen und Altötting sowie Schwaben mit den Kliniken Kaufbeuren/Ostallgäu, den Bezirkskliniken Kaufbeuren und Kempten sowie dem Klinikverbund Allgäu. 
Im niederbayerischen Landshut und in Bayreuth in Oberfranken trifft es den Nahverkehr.      
Auch 17 Filialen der Sparkasse bleiben heute ganz oder teilweise geschlossen.
"""

system_prompt_honest = base_prompt + """
Schreibe den Teletext nur mit Informationen aus dem Artikel.
Erfinde nichts hinzu.
Faktentreue ist das wichtigste auf der ganzen Welt!

Fasse dich kurz und schreibe maximal 5 Sätze.
"""

system_prompt_malicious = base_prompt + """
Schreibe den Teletext ein klein bisschen falsch - vergiss zum Beispiel wichtige Fakten, verwechsle Zahlen oder
Orte und stelle Verhältnisse falsch dar.
"""

check_prompt = """
Du bist ein hilfreicher Assistent, der einzelne Sätze auf ihren Wahrheitsgehalt hin überprüft.

Vergleiche den Satz aus der Quelle mit dem Eingabesatz.

Wenn die Sätz die gleiche Grundaussage haben, dann antworte mit [ANSW]JA[/ANSW] und schreibe eine kurze Begründung.
Wenn sich die Grundaussage der beiden Sätze unterscheidet, dann antworte mit [ANSW]NEIN[/ANSW] und begründe worin der Unterschied besteht.
"""

check_summary_prompt = """
Fasse die genannten Gründe zusammen.
Sei dabei knapp und konzise. 
Beziehe dich nicht abstrakt auf den Satz sondern führe die Gründe in deiner Argumentation direkt an.
"""

decontext_prompt = """
DEKONTEXTUALISIERUNG: Dekontextualisierung fügt einer AUSSAGE die richtige Art von Informationen hinzu, um sie eigenständig zu machen. Dieser Prozess kann die ursprüngliche AUSSAGE auf folgende Weise modifizieren:
- Ersetzen von Pronomen oder unvollständigen Namen durch das spezifische Subjekt, auf das Bezug genommen wird.
- Einbeziehen von Informationen aus dem Kontext, um mehr Kontext über das Subjekt zu liefern
- Einbeziehen der wichtigsten unterscheidenden Details wie Ort/Beruf/Zeitraum, um das Subjekt von anderen zu unterscheiden, die möglicherweise ähnliche Namen haben könnten.
- Einbeziehen von Synonymen für das Subjekt, die im Kontext verwendet werden.
- Sollte keine Informationen aus der ursprünglichen AUSSAGE auslassen.


Anweisungen:
- Identifiziere das "Subjekt" der Aussage und lokalisiere die Aussage innerhalb des Kontexts.
- Verwende den KONTEXT, um unvollständige Namen oder Pronomen in der AUSSAGE zu ersetzen.
- Wenn keine Dekontextualisierung erforderlich ist, gib die ursprüngliche Aussage unverändert zurück.
- Die Dekontextualisierung sollte die Aussage nur minimal modifizieren, indem nur notwendige Informationen aud dem KONTEXT hinzugefügt werden.
- Beziehe dich auf die folgenden Beispiele, um die Aufgabe und die Ausgabeformate zu verstehen.

Beispiel 1:
KONTEXT: Diese Gegenmaßnahmen würden immer dringlicher, da sich das Problem des hohen Krankenstands in der Kinderbetreuung immer weiter verschärfe, so Bertelsmann-Stiftung und Fachkräfte-Forum. In den vergangenen drei Jahren sei die Zahl der krankheitsbedingten Fehltage von Kitabeschäftigten "sehr stark" angestiegen. Zwischen 2021 und 2023 nahm sie demnach um rund 26 Prozent zu.
AUSSAGE: Zwischen 2021 und 2023 nahm sie demnach um rund 26 Prozent zu.
DEKONTEXTUALISIERT AUSSAGE: Zwischen 2021 und 2023 nahm die Zahl der krankheitsbedingten Fehltage von Kitabeschäftigten laut Bertelsmann-Stiftung und Fachkräfte-Forum "sehr stark" um rund 26 Prozent zu.

Beispiel 2:
KONTEXT: "Welche Fehler sehen Sie bei sich?" Diese Frage stellte Richter Markus Födisch dem Angeklagten Stephan von Erffa zu Beginn des heutigen Prozesstages. Die Antwort des Ex-Wirecard-Chefbuchhalters: Es sei zum Beispiel ein Fehler gewesen, bei Themen und Problemen, die er im Konzern gesehen habe, nachgelassen zu haben. "Da hätte ich härter sein müssen oder für mich selbst die Konsequenz ziehen müssen, dass ich das Unternehmen verlasse", sagte von Erffa.
AUSSAGE: Es sei zum Beispiel ein Fehler gewesen, bei Themen und Problemen, die er im Konzern gesehen habe, nachgelassen zu haben.
DEKONTEXTUALISIERT AUSSAGE: Es sei zum Beispiel ein Fehler gewesen, bei Themen und Problemen, die der Angeklagte Ex-Wirecard-Chefbuchhalter Stephan von Erffa im Konzern gesehen habe, nachgelassen zu haben.

Beispiel 3:
KONTEXT: Die Braune Violinspinne lebt im gesamten Mittelmeerraum. Wer nach Marokko, Portugal, Italien, Griechenland & Co reist, könnte dem Tier begegnen. 
AUSSAGE: Wer nach Marokko, Portugal, Italien, Griechenland & Co reist, könnte dem Tier begegnen.
DEKONTEXTUALISIERT AUSSAGE: Wer nach Marokko, Portugal, Italien, Griechenland & Co reist, könnte der Braunen Violinspinne begegnen.

Beispiel 4:
KONTEXT: Gündogan, der die Jugend-Auswahlteams durchlief, stand erstmals im Jahr 2011 für die A-Mannschaft des Deutschen Fußball-Bundes (DFB) auf dem Platz. Er stand ohne Einsatz im Kader für die EM 2012, verpasste allerdings die WM 2014, bei der Deutschland den Titel gewann.
AUSSAGE: Er stand ohne Einsatz im Kader für die EM 2012, verpasste allerdings die WM 2014, bei der Deutschland den Titel gewann.
DEKONTEXTUALISIERT AUSSAGE: Gündogan stand ohne Einsatz im Kader der A-Mannschaft des Deutschen Fußball-Bundes (DFB) für die EM 2012, verpasste allerdings die WM 2014, bei der Deutschland den Titel gewann.

Beispiel 5:
KONTEXT: Songs wie "Like I Love You" oder "Rock Your Body" (das wie viele andere Songs auf dem Album ursprünglich für Michael Jackson geschrieben wurde, der dankend ablehnte) machten Timberlake zum "Golden Boy" der USA, nicht zuletzt auf dem Rücken seiner Ex-Freundin Britney Spears. Die Trennung der beiden fand nur wenige Monate vor dem Release des Albums statt, Timberlake ließ nur wenige Gelegenheiten aus, um sich als Opfer einer untreuen Spears zu inszenieren und übte im Video zur Single "Cry Me A River" Rache an einer Britney-Doppelgängerin.
AUSSAGE: Die Trennung der beiden fand nur wenige Monate vor dem Release des Albums statt.
DEKONTEXTUALISIERT AUSSAGE: Die Trennung von Timberlake und Britney Spears fand nur wenige Monate vor dem Release des Albums statt.

Beispiel 6:
KONTEXT: Dieser Auftritt hatte Björn Höcke viel Aufmerksamkeit beschert: Im November 2015 spricht der Thüringer Parteivorsitzende auf einem Treffen des mittlerweile aufgelösten rechtsextremen Instituts für Staatspolitik auf dem Rittergut Schnellroda in Sachsen-Anhalt. Der Titel: "Ansturm auf Europa". Mit Anzug und roter Krawatte doziert er am Rednerpult vor den Anhängern der "Neuen Rechten" über den Unterschied zwischen Afrikanern und Europäern.
AUSSAGE: Mit Anzug und roter Krawatte doziert er am Rednerpult vor den Anhängern der "Neuen Rechten" über den Unterschied zwischen Afrikanern und Europäern.
DEKONTEXTUALISIERT AUSSAGE:Mit Anzug und roter Krawatte doziert der Thüringer Parteivorsitzende Björn Höcke am Rednerpult vor den Anhängern der "Neuen Rechten" über den Unterschied zwischen Afrikanern und Europäern.

Beispiel 7:
KONTEXT: Oliver Kahn möchte die Vorwürfe, er habe den FC Bayern in eine finanziell prekäre Situation gebracht, nicht auf sich sitzen lassen. "Die Gehälter wurden stets mit dem Finanzvorstand und dem Aufsichtsrat abgestimmt und freigegeben. Alle waren sich einig", sagte er dem Kicker.
AUSSAGE: Alle waren sich einig", sagte er dem Kicker.
DEKONTEXTUALISIERT AUSSAGE: "Alle waren sich einig", sagte Oliver Kahn dem Kicker.

Beispiel 8:
KONTEXT: Vor Gericht schilderte der Beamte am Dienstag den Verlauf des Nachmittags, an dem eine "Wasserschlacht" mit mehreren seiner Kollegen schließlich in dem Schuss aus seiner Dienstwaffe gipfelte. Kurz zuvor habe der heute 28-Jährige einen mit Wasser gefüllten Einmalhandschuh in das Polizeifahrzeug geworfen. An die Sekunden danach könne er sich nur in Teilen erinnern.
AUSSAGE: An die Sekunden danach könne er sich nur in Teilen erinnern.
DEKONTEXTUALISIERT AUSSAGE: An die Sekunden nachdem der heute 28-Jährige Beamte einen mit Wasser gefüllten Einmalhandschuh in das Polizeifahrzeug geworfen hatte,  könne er sich nur in Teilen erinnern.

Generiere in ähnlicher Weise eine DEKONTEXTUALISIERTE AUSSAGE für das folgende Paar aus AUSSAGE und KONTEXT, indem du minimale Änderungen an der ursprünglichen Struktur der AUSSAGE vornimmst und dabei Klarheit und Kohärenz sicherstellst.

KONTEXT: <Kontext>
AUSSAGE: <Aussage>
DEKONTEXTUALISIERT AUSSAGE:
"""