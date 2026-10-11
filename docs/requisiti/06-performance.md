# 06 – Performance (score)

Una **performance** è il risultato che un atleta registra su un workout. Nella nuova app lo
score è **strutturato**: i campi dipendono dal tipo di risultato dichiarato dal workout
(RF-04-D1), così da essere confrontabile nel tempo e tra atleti
(vedi [13-analisi-dati.md](13-analisi-dati.md)). Il testo libero resta come nota e come
rappresentazione leggibile.

Schema di riferimento: entità `Performance` in [02-modello-dati.md](02-modello-dati.md).

## Tipi di risultato e campi

| `result_type` | Campi richiesti | Rappresentazione `result` | Direzione |
|---------------|-----------------|---------------------------|-----------|
| `time` | minuti, secondi (`result_seconds`) | `12:34` | meglio se minore |
| `rounds_reps` | round (`result_rounds`), ripetizioni extra (`result_reps`) | `7 round + 12` | meglio se maggiore (round × reps del round + extra) |
| `load` | carico in kg (`result_load`) | `102,5 kg` | meglio se maggiore |
| `reps` | ripetizioni (`result_reps`) | `48 reps` | meglio se maggiore |
| `distance` | metri (`result_distance`) | `2.350 m` | meglio se maggiore |
| `calories` | calorie (`result_calories`) | `86 cal` | meglio se maggiore |
| `none` | nessuno | – | il workout non prevede score; è possibile solo segnare "completato" con nota |

Per ogni tipo sono sempre disponibili: **Rx / Scalato** (`is_rx`), **note** (testo libero,
max 500), **data** (default: data del workout), e la sessione cardio se presente
([12-monitoraggio-cardio.md](12-monitoraggio-cardio.md)).

RF-06-01 – Per un workout con `result_type = time` che ha un time cap, se l'atleta non
termina entro il cap registra "cap" più le ripetizioni completate (`result_reps`); lo score
è ordinato dopo tutti quelli completati, per ripetizioni decrescenti.

RF-06-02 – Per i workout **di tipo test** (RF-04-D8) lo score è il valore del test: il
salvataggio crea anche il MaxRecord corrispondente (RF-05-D5). Se l'atleta modifica lo
score, il MaxRecord collegato viene aggiornato; se lo elimina, anche il MaxRecord.

RF-06-03 – Il server rifiuta score con campi incoerenti con il tipo di risultato del
workout (RF-02-14). Per i workout `none` è ammesso solo il flag completato con nota.

## Inserimento

RF-06-04 – Dalla pagina del workout, tab "Il mio score". Il form mostra solo i campi del
tipo di risultato, con tastiera numerica e stepper grandi; per il tempo un campo mm:ss con
maschera. Rx preselezionato. Note opzionali.

RF-06-05 – **Dal timer**: al termine, lo score è precompilato dai dati del timer
(tempo trascorso per For time, round e ripetizioni contati per AMRAP, round completati per
EMOM) e dalla sessione cardio se presente. L'atleta conferma, corregge o scarta
(vedi [07-timer.md](07-timer.md)).

RF-06-06 – Un atleta ha **un solo score per workout** (RF-02-04). Se esiste già, il form
apre in modifica. Lo storico delle modifiche è nel log attività.

RF-06-07 – Solo gli atleti abilitati possono inserire score (RF-01-07). Gli score sui
workout dedicati e personali sono ammessi come sui pubblici.

RF-06-08 – Inserimento **offline**: lo score viene salvato localmente e sincronizzato alla
prima connessione, con indicazione "In attesa di sincronizzazione". In caso di conflitto
(score modificato nel frattempo dal coach) prevale la versione più recente e l'atleta viene
avvisato.

RF-06-09 – Al salvataggio, se lo score migliora il risultato precedente sullo stesso
benchmark (RF-04-D4) o il test migliora il massimale, l'app mostra la conferma di **nuovo
record personale** con la frase di personalità (RF-10-D11) e invia la notifica (RF-08-D8).
Evento `performance_created` / `performance_updated`.

## Modifica ed eliminazione

RF-06-10 – L'atleta può modificare o eliminare il proprio score senza limiti di tempo.
L'eliminazione richiede conferma esplicita ("Eliminare lo score? L'operazione non è
reversibile.").

RF-06-11 – Coach e superuser possono modificare o eliminare lo score di qualsiasi atleta e
**inserirne uno per conto** di un atleta che non l'ha registrato (RF-08-D18). L'azione è
tracciata con `entered_by` / `on_behalf_of` e l'atleta riceve una notifica.

RF-06-12 – Uno score inserito dal coach è mostrato all'atleta con l'indicazione "Inserito
dal coach"; l'atleta può comunque correggerlo.

## Classifica del workout

RF-06-13 – Tab "Classifica" nella pagina del workout: tutti gli score degli atleti abilitati
sul workout, ordinati per risultato secondo la direzione del tipo (Rx prima degli scalati,
poi i "cap"), con posizione, nome dell'atleta, risultato, badge Rx/Scalato, data se diversa
da quella del workout. Lo score dell'utente corrente è evidenziato.

RF-06-14 – La classifica esiste solo per i workout **pubblici** (`audience = all`) con
`result_type` diverso da `none`. I dedicati e i personali mostrano solo lo score personale.

RF-06-15 – Le note e la sessione cardio di un atleta sono visibili solo a lui, al coach e al
superuser, non agli altri atleti nella classifica (RF-12-14).

RF-06-16 – Gli score legacy migrati (solo `result` testuale) compaiono nella classifica in
coda, con l'indicazione "score non strutturato", senza posizione.

RF-06-17 – Decisione aperta (vedi [11-note-migrazione-flutter.md](11-note-migrazione-flutter.md)):
la classifica è visibile a tutti gli atleti come oggi. Se in futuro si vorrà renderla
opzionale, si aggiunge un'impostazione per atleta "nascondi i miei score agli altri".

## Storico personale

RF-06-18 – Sezione Progressi, "I miei score": elenco cronologico di tutti gli score con
filtro per periodo, categoria e benchmark; tocco su uno score per aprire il workout.

RF-06-19 – Per ogni benchmark ripetuto, confronto con l'esecuzione precedente e il miglior
risultato (RF-13-05).

## Migrazione dal legacy

- `Performance.description` → `result`, campi strutturati null, `is_rx = true`.
- Le performance senza link a un workout vengono scartate; con più performance dello stesso
  atleta sullo stesso workout si tiene la più recente (vedi tabella di migrazione in
  [02-modello-dati.md](02-modello-dati.md)).
- Non si tenta di interpretare il testo libero: lo score resta "non strutturato" (RF-13-18).
  Facoltativo: uno strumento per il coach che propone un'interpretazione ("12:34" → time)
  da confermare a mano, workout per workout.
- `capitalize()` legacy non viene replicato: il testo resta com'è.
