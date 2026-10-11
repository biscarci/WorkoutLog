# 05 – Catalogo esercizi, massimali (1RM) e calcolo delle percentuali

Questo è il cuore "di business" dell'app: ogni workout può indicare percentuali per uno o più
esercizi e l'app le traduce nel carico personale dell'atleta.

## Direzione per la nuova app: gestione dei test

Il catalogo esercizi viene esteso con una **categoria**, che determina il tipo di test e come
si leggono i risultati.

| Categoria (`category`) | Esempi | Tipo di test tipico | Unità ammesse |
|------------------------|--------|---------------------|---------------|
| `weightlifting` (pesistica) | Back Squat, Clean & Jerk, Bench Press | 1RM, 3RM, 5RM | kg |
| `monostructural` (monostrutturale) | Row, Ski, Bike, Run | tempo su distanza, pace su distanza di riferimento, calorie o metri a tempo | min, pace, distance, cal |
| `bodyweight` (corpo libero) | Pull-up, Dips, Handstand push-up, Double-under | max ripetizioni consecutive, max ripetizioni a tempo, tenuta in secondi | reps, min |
| `skill` | Muscle-up, Handstand walk | conseguito / non conseguito, metri, ripetizioni | reps, distance |

RF-05-D1 – Ogni esercizio del catalogo ha una categoria obbligatoria; la categoria limita le
unità selezionabili e propone il `pct_mode` corretto.

RF-05-D2 – Un massimale (MaxRecord) registra anche il **tipo di test** (`test_type`: `1rm`,
`3rm`, `5rm`, `max_reps`, `time`, `pace`, `distance`, `calories`, `hold`) e, per i test a
tempo o a ripetizioni, la durata del test (es. "max reps in 2 minuti"). Il calcolo delle
percentuali usa il record del tipo di test previsto dalla riga del workout (default 1RM per la
pesistica).

RF-05-D2b – **Un esercizio, più test.** I monostrutturali hanno un solo esercizio a catalogo
(Row, Ski Erg, Bike Erg, Run, Swim) con più test distinti per **distanza** (`test_distance_m`):
Row 500m (pace), Row 1k, 2k, 5k (tempo); Run 400m, 1k, 2k, 5k. Non esistono voci di catalogo
separate per distanza. Il catalogo dichiara per ogni esercizio i test ammessi
(`allowed_test_types`, es. `pace:500m;time:2k`). Lo storico dell'atleta è per esercizio e
test.

RF-05-D2c – **Passo di riferimento.** Da qualsiasi test a tempo o pace si ricava il passo
sulla distanza di riferimento dell'esercizio (500m per Row e Ski, 1 km per Run e Bike):
passo = tempo / (distanza test / distanza di riferimento). Es. Row 2k in 7:20 → 1:50 /500m.
Una riga di workout che indica "95% del test 2k" usa il passo del test 2k più recente;
se manca, "test mancante".

RF-05-D3 – Il massimale salva anche l'**unità al momento dell'inserimento**, così un
cambio di unità sul catalogo non reinterpreta i valori storici.

RF-05-D4 – Per la pesistica, dai test 3RM e 5RM viene stimato un 1RM (formula di Epley,
`peso × (1 + reps/30)`) mostrato come "stimato" e usato per le percentuali solo se non
esiste un 1RM misurato più recente.

RF-05-D5 – Il coach può programmare **sessioni di test** (RF-04-D8): scelto l'esercizio e il
tipo di test, ogni atleta inserisce il risultato dalla pagina del workout e il sistema crea il
MaxRecord con data del workout. Il coach vede chi ha registrato il test.

RF-05-D6 – Il coach può inserire o correggere un test per conto dell'atleta, con tracciamento
nel log.

RF-05-D7 – Lo storico dell'atleta mostra, per ogni esercizio, tutti i test per tipo con
grafico, PR evidenziato e variazione (vedi [13-analisi-dati.md](13-analisi-dati.md)).

RF-05-D8 – Seed iniziale del catalogo: file [data/catalogo-esercizi-seed.csv](data/catalogo-esercizi-seed.csv),
circa 140 esercizi ricavati dall'analisi dell'export completo di produzione (889 workout,
dicembre 2025 – settembre 2026, più massimali e range) e da alcune voci standard derivate.
Per ogni esercizio: nome canonico, categoria, unità, distanza di riferimento, lettura
percentuale, tipi di test ammessi e **alias** (le grafie trovate nei dati, usate dall'import
da testo per riconoscere le righe, RF-04-D6). Il file va rivisto dal coach prima del seed.

RF-05-D9 – Ogni esercizio del catalogo può avere **alias** (grafie alternative, abbreviazioni:
"c2b", "t2b", "d. under", "hspu"). Gli alias sono usati dalla ricerca nell'editor e dal
riconoscimento nell'import da testo; sono modificabili dal coach.

RF-05-D10 – Gli esercizi con **varianti** (tempo, pause, deficit, weighted, strict) sono voci
distinte del catalogo quando hanno un test proprio (es. Strict Pull-up vs Weighted Strict
Pull-up), altrimenti la variante è una nota sulla riga del workout.

---

## Catalogo esercizi (`/admin/exercises`) – coach

RF-05-01 – Il catalogo è l'elenco degli esercizi su cui si registrano massimali. Alimenta la
tendina del form massimali e definisce **come** leggere valori e percentuali.

RF-05-02 – Campi: nome (2–100, univoco case-insensitive), unità, distanza di riferimento, lettura percentuale.

| Unità (`unit`) | Etichetta | Significato | Formato input | Formato output |
|----------------|-----------|-------------|---------------|----------------|
| `kg` | Kg | massimale di forza | numero decimale (virgola o punto) | `102.5` |
| `reps` | reps | ripetizioni max (es. Dips, Pull-up) | intero/decimale | `24.0` (round 1) |
| `min` | min | test a cronometro (es. Run 2k) | `mm:ss` **o** minuti decimali | `mm:ss` |
| `pace` | `/500m`, `/km`, `/2km`… | passo su distanza (remo, ski, corsa) | `mm:ss` o minuti decimali | `mm:ss` |
| `distance` | m | metri | intero | intero |
| `cal` | cal | calorie | intero | intero |

RF-05-03 – `ref_distance` (metri) è **obbligatoria** se unit = pace e deve essere > 0. Etichetta:
`/500m`; multipli di 1000 → `/km`, `/2km`… Nel form l'input compare solo quando unit = pace.

RF-05-04 – `pct_mode`:
- `literal`: valore × percentuale / 100 (85% di 100 kg = 85 kg).
- `intensity`: valore × 100 / percentuale (85% di un pace 1:45 ≈ 2:04, cioè **più lento**; i testi dell'app dicono 2:03). Applicato **solo** se unit ∈ {min, pace}; per le altre unità `intensity` si comporta come `literal`.
- Nel form, cambiando unità a min/pace la lettura passa automaticamente a `intensity`, altrimenti a `literal` (default suggerito).

RF-05-05 – Aggiunta: se esiste già un esercizio con lo stesso nome (case-insensitive): se attivo → "L'esercizio 'X' esiste gia'." ; se disattivato → viene **riattivato** con i nuovi parametri.

RF-05-06 – Modifica (`/admin/exercises/<id>/edit`): nome, unit, ref_distance, pct_mode. Se il nome cambia (a meno di spazi/maiuscole), tutti i `UserStatistic.exercise` e `Range.exercise` con il vecchio nome vengono rinominati; messaggio "Esercizio 'X' aggiornato. (N riferimenti aggiornati)". Nome in conflitto con un altro esercizio → errore.

RF-05-07 – Attiva/disattiva (`toggle`): gli esercizi disattivati non compaiono nella tendina dei massimali ma restano usati per i calcoli e sono mostrati barrati in lista.

RF-05-08 – Elimina: se l'esercizio è usato in massimali o range → viene solo disattivato con messaggio "'X' e' usato in massimali o percentuali: disattivato invece che eliminato."; altrimenti eliminato. Conferma JS prima dell'invio.

RF-05-09 – Lista: ordinata attivi prima, poi alfabetico; per ogni riga: nome (link a modifica), badge unità, badge "intensita" se pct_mode = intensity, conteggio "N massimali · M percentuali" (conteggi su nome normalizzato), stato disattivato.

RF-05-10 – **Orfani**: esercizi presenti in massimali/range ma non a catalogo vengono elencati con un pulsante "IMPORTA" che li crea a catalogo (unit `kg`, oppure `reps` se il nome è "dips"), uno alla volta; i nomi che collidono per il vincolo unique vengono saltati e segnalati.

## Massimali dell'atleta (`/stats`)

RF-05-11 – Form "Add 1RM": data (default oggi), esercizio (select dal catalogo attivo, ordinato alfabeticamente; se il valore corrente non è più attivo viene comunque mantenuto in lista), valore.

RF-05-12 – Sotto il campo valore un **hint dinamico** in base all'unità dell'esercizio selezionato:
- kg: "Peso in chili, es. 102.5"
- reps: "Numero di ripetizioni, es. 24"
- min: "Tempo in mm:ss, es. 8:30 (oppure 8.5 in minuti decimali)"
- pace: "Pace in mm:ss, es. 1:45"
- distance: "Distanza in metri, es. 2000"
- cal: "Calorie, es. 120"

RF-05-13 – **Validazione del valore** (virgola accettata come separatore decimale):
- unit min/pace:
  - `m:ss` → minuti + secondi/60; secondi devono essere interi < 60 ("I secondi devono essere inferiori a 60.").
  - numero decimale → accettato **tranne** se ha esattamente 2 decimali < 60 (es. `8.30`): errore "Ambiguo: per 8 minuti e 30 secondi scrivi 8:30, per i decimali usa un solo decimale."
  - negativo → errore.
- altre unità: numero ≥ 0, altrimenti "Inserisci un numero valido." / "Il valore non puo' essere negativo."
- vuoto → salvato come null.

RF-05-14 – Il valore è salvato in `weight` come float nell'unità dell'esercizio (tempi in minuti decimali); `reps` = 1.

RF-05-15 – Tabella "Your 1RM Records": per ogni esercizio **solo il record più recente** (max date), ordinato per data desc. Colonne: checkbox elimina (con conferma "Vuoi eliminare questa statistica?"), data `dd/mm/yy`, esercizio (link a modifica), valore formattato + unità, icona storico.

RF-05-16 – Modifica (`/stats/edit/<id>`): stesso form, valore precompilato già formattato (es. `08:30`). Solo proprietario o coach.

RF-05-17 – Eliminazione (`/stats/delete`, POST con `selected_ids[]`): elimina solo le proprie (il coach può eliminare quelle di chiunque). Messaggio "Eliminate N statistiche".

## Storico massimale (`/stats/history/<esercizio>`)

RF-05-18 – Per l'esercizio (match case-insensitive) mostra:
- 4 tile: **Best** (max valore, con data), **First** (primo per data), **Latest** (ultimo), **Delta** (latest − first, con segno).
- Grafico a linee (Chart.js): serie "1RM" con area, serie tratteggiata "Best so far" (massimo progressivo). Asse Y etichettato "Kg". Dati via `GET /api/stats/history/<esercizio>` → `{exercise, points:[{date ISO, label dd/mm/yy, weight, reps}]}` ordinati per data asc. Senza dati: "Nessun dato disponibile per questo esercizio."
- Tabella dei record (data desc) con modifica/elimina.

Nota: tile, grafico e tabella mostrano il valore grezzo con suffisso "kg" anche per esercizi in reps/min/pace. Da correggere usando l'unità dell'esercizio (e per `intensity` il "best" di un tempo è il **minimo**).

## Calcolo e visualizzazione delle percentuali sui workout

RF-05-19 – Per ogni workout con range, l'app raggruppa i range per esercizio (ordine di prima apparizione) e per ogni gruppo cerca il **massimale più recente dell'utente corrente** per quell'esercizio (match lower-case).

RF-05-20 – Visualizzazione nel workout (dashboard, pagina performance, pannello timer):
- Massimale assente: "Massimale di {esercizio} non trovato, quando cazzo ti decidi a registrarlo? [Inserisci 1RM]" (link a /stats).
- Massimale presente: riga "In base al tuo RM di {esercizio} a {valore} {unità}" (per kg si usa "a", per le altre unità "di") seguita dalla lista orizzontale `{pct}% @{valore calcolato} {unità}` per ogni range, es. `70% @84.0 Kg`, `85% @02:03 /500m`.

RF-05-21 – Formula: `apply_percentage(max, pct, unit, pct_mode)`:
- `intensity` e unit ∈ {min, pace} → `max × 100 / pct`
- altrimenti → `max × pct / 100`
Formattazione: min/pace → `mm:ss` (arrotondando ai secondi); distance/cal → intero; kg/reps → 1 decimale.

Esempi di verifica (utili come test case in Flutter):

| Massimale | unit | pct_mode | % | Risultato |
|-----------|------|----------|---|-----------|
| 120 | kg | literal | 70 | `84.0 Kg` |
| 8.5 (8:30) | min | literal | 85 | `07:14 min` |
| 1.75 (1:45) | pace /500m | intensity | 85 | `02:04 /500m` (1.75×100/85 = 2.0588 min = 123.5 s → arrotondato 124 s) |
| 2000 | distance | literal | 50 | `1000 m` |

## Note / decisioni aperte

- `Range.kind = 'offset'` (es. `+10` secondi) viene salvato ma **ignorato** nella visualizzazione: viene mostrato come `10% @…`. Requisito atteso: per offset mostrare `pace + 10s` (es. `+10s @01:55 /500m`). Da implementare nel nuovo sistema.
- L'unità del massimale è dedotta dal catalogo **al momento della lettura**: se il coach cambia unit a un esercizio, i valori storici vengono reinterpretati. Nel nuovo modello valutare di salvare l'unità sul record del massimale.
- Nel form massimali il campo si chiama "Weight (Kg) / Reps / Minuti" e a DB `weight`; in Flutter usare "valore".
- La lista storica dei massimali ha anche il concetto di `reps` (n-RM) mai usato: decidere se eliminarlo o supportare 3RM/5RM.
- Legacy (`forms.movement_choices`): lista fissa usata come fallback quando il catalogo è vuoto: Back Squat, Front Squat, Deadlift, Bench Press, Dips, Clean & Jerk, Power Clean, Squat Clean, Power Snatch, Squat Snatch, Thruster, Push Press, Push Jerk, Split Jerk. Utile come seed iniziale.
- Fusioni note di grafie (`EXERCISE_MERGES`): "clean and jerk" → "Clean & Jerk", "overheanr squat" → "Overhead Squat".
