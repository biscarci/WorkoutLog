# 13 – Analisi dei dati e andamento

Funzionalità nuova. Trasforma i dati già raccolti (massimali, score, sessioni cardio) in
indicatori di progressione leggibili dall'atleta e dal coach. Nel legacy esisteva solo il
grafico storico del singolo massimale.

Le analisi sono calcolate lato server ed esposte via API, così che app mobile e dashboard web
(vedi [14-dashboard-web.md](14-dashboard-web.md)) mostrino gli stessi numeri.

## Prerequisiti sui dati

Le analisi sono affidabili solo se gli score sono strutturati. Il testo libero legacy
("7 rounds + 12 reps") non è confrontabile automaticamente. Per questo:

RF-13-01 – Ogni workout dichiara un **tipo di risultato** (vedi nuovo processo di inserimento
in [04-workout.md](04-workout.md)): tempo, round e ripetizioni, carico, ripetizioni, distanza,
calorie, oppure nessuno (allenamento senza score). Lo score è registrato con campi coerenti al
tipo e un campo note libero.

RF-13-02 – I workout hanno un **tag di categoria** facoltativo (es. benchmark, forza, metcon,
skill) e possono essere marcati come **benchmark ripetibile** (es. "Fran", "Grace") per
consentire il confronto tra esecuzioni a distanza di tempo.

RF-13-03 – Ogni score strutturato è normalizzato in un valore numerico confrontabile
(secondi, ripetizioni totali, kg, metri, calorie) con direzione "meglio se maggiore" o
"meglio se minore" derivata dal tipo.

## Analisi per l'atleta

RF-13-04 – **Andamento massimali**: per ogni esercizio, grafico storico dei test con variazione
percentuale rispetto al test precedente e al primo test. Sintesi "negli ultimi 90 giorni:
+5 kg (+4,2 %)".

RF-13-05 – **Progressione sui benchmark**: per ogni benchmark ripetuto, confronto tra le
esecuzioni con miglior risultato evidenziato e delta rispetto alla precedente.

RF-13-06 – **Costanza**: allenamenti completati per settimana e per mese, serie corrente di
settimane consecutive con almeno un allenamento, confronto con la media del box.

RF-13-07 – **Distribuzione**: quota di allenamenti per categoria (forza, metcon, skill…) nel
periodo scelto, per evidenziare squilibri.

RF-13-08 – **Intensità** (se disponibili sessioni cardio, [12-monitoraggio-cardio.md](12-monitoraggio-cardio.md)):
FC media per allenamento nel tempo, minuti per zona per settimana, rapporto tra intensità e
risultato sullo stesso benchmark.

RF-13-09 – **Record personali**: elenco dei PR (massimali e benchmark) con data, con
riconoscimento automatico e notifica al momento del salvataggio di uno score o di un test
che migliora il precedente.

RF-13-10 – Ogni analisi ha un selettore di periodo (30 giorni, 90 giorni, 6 mesi, 1 anno,
tutto) e, dove ha senso, di esercizio o benchmark.

## Analisi per il coach e il superuser

RF-13-11 – **Panoramica atleti**: tabella con, per ogni atleta abilitato, ultimo accesso,
allenamenti negli ultimi 30 giorni, numero di massimali registrati, ultimo PR, tendenza
(in miglioramento, stabile, in calo) calcolata sui benchmark e massimali del periodo.

RF-13-12 – **Scheda atleta**: tutte le analisi di RF-13-04..RF-13-10 viste dal coach, con la
possibilità di annotare osservazioni private (non visibili all'atleta).

RF-13-13 – **Analisi del workout**: per un singolo workout, distribuzione degli score degli
atleti (mediana, min, max, scarto), tempo per zona medio se disponibili dati cardio, elenco
degli atleti che non hanno registrato lo score.

RF-13-14 – **Analisi della programmazione**: nel periodo scelto, numero di workout per
categoria, esercizi più programmati, esercizi con percentuali per i quali molti atleti non
hanno il massimale.

RF-13-15 – **Atleti inattivi**: elenco di chi non registra score da più di N giorni
(N configurabile, default 14), con azione rapida per inviare un promemoria.

RF-13-16 – **Confronto tra atleti** su un benchmark o massimale, solo per coach e superuser,
mai mostrato agli altri atleti al di fuori della classifica del singolo workout già prevista.

## Calcolo e prestazioni

RF-13-17 – Le aggregazioni per periodo sono calcolate su richiesta con cache invalidata al
salvataggio di nuovi score, test o sessioni. Per volumi di un singolo box (decine di atleti)
non servono tabelle precalcolate.

RF-13-18 – I dati storici migrati dal legacy con score in testo libero restano consultabili
ma sono esclusi dalle analisi numeriche, con indicazione "score non strutturato".

## Impatti sugli altri documenti

- [02-modello-dati.md](02-modello-dati.md): tipo di risultato e campi strutturati su
  Workout e Performance, tag di categoria, flag benchmark, note del coach sull'atleta.
- [04-workout.md](04-workout.md): il nuovo inserimento deve chiedere tipo di risultato e
  categoria.
- [06-performance.md](06-performance.md): score strutturato al posto del testo libero.
- [08-amministrazione.md](08-amministrazione.md): promemoria agli atleti inattivi.
