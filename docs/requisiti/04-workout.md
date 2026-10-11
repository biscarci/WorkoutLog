# 04 – Workout

> **Stato**: questo documento descrive il comportamento legacy. La sezione seguente fissa la
> direzione per la nuova app; il resto verrà riscritto quando il nuovo processo di inserimento
> sarà definito nel dettaglio.

## Direzione per la nuova app: nuovo processo di inserimento

Il coach non incolla più testo libero. Inserisce l'allenamento tramite un **editor strutturato**,
disponibile sull'app mobile e, in forma più comoda, sulla dashboard web
([14-dashboard-web.md](14-dashboard-web.md), RF-14-06).

RF-04-D1 – Un workout è composto da: data, titolo, **categoria** (forza, metcon, skill,
monostrutturale, mobilità, benchmark, test, altro), **tipo di risultato** (tempo, round e
ripetizioni, carico, ripetizioni, distanza, calorie, nessuno), formato (AMRAP, For time, EMOM,
Every X min, Tabata, sets × reps, libero) con i relativi parametri (durata, numero di round,
intervallo), e una lista ordinata di **righe esercizio**.

RF-04-D2 – Ogni **riga esercizio** referenzia un esercizio del catalogo (con ricerca per nome
o alias e creazione rapida se assente) e ha:
- **quantità** con unità: ripetizioni, metri, calorie, secondi, **minuti**;
- **intensità**, una tra: nessuna; carico assoluto in kg; **percentuale di un test**
  dell'atleta; **scarto in secondi** sul passo di un test; **zona cardiaca** Z1–Z5;
- **test di riferimento** per percentuale e scarto: per la pesistica il 1RM (o 3RM/5RM),
  per i monostrutturali uno dei test dell'esercizio (es. Row: 500m, 1k, 2k, 5k). Il test è
  distinto dall'esercizio: "Row al 95% del test 2k" è una riga su Row, non su un esercizio
  "Row 2k";
- **ritmo** (palate o pedalate al minuto, es. "20-22 s/m") per i monostrutturali;
- **nota** libera (tempo, pausa, scaling).

Le percentuali sostituiscono l'attuale entità Range: sono attributi della riga, non del workout.

RF-04-D2b – **Blocchi ripetuti.** Una riga può essere un'intestazione di blocco con numero di
giri fisso o variabile ("3–4 giri di:"); le righe rientrate sotto di essa ne fanno parte.
Serve per superset, intervalli ("3 to 4 sets: 4' lavoro, 1' recupero"), EMOM con stazioni
A/B/C. Un blocco può contenere righe esercizio e righe di testo, non altri blocchi.

RF-04-D2c – **Valore calcolato per l'atleta.** Per ogni riga con intensità l'app mostra il
valore personale:
- percentuale su pesistica: kg dal massimale (arrotondati a 0,5 kg);
- percentuale su un test a tempo o pace: passo = passo del test / percentuale (lettura
  "intensity", RF-05-04), es. 2k in 7:20 → 1:50 /500m → 95% = 1:56 /500m;
- scarto in secondi: passo del test + scarto;
- zona cardiaca: intervallo di bpm dalle zone dell'atleta (RF-12-13), e durante il timer il
  pannello cardio segnala se è dentro o fuori zona;
- test mancante: "test mancante" con invito a registrarlo.

RF-04-D3 – È ammessa anche una riga di **testo libero** per note, indicazioni di scaling o
istruzioni non riconducibili a un esercizio.

RF-04-D4 – Il workout può essere marcato come **benchmark ripetibile**; i benchmark hanno un
nome canonico (es. "Fran") e vengono proposti dalla libreria quando il coach ne inserisce uno
nuovo con lo stesso nome.

RF-04-D5 – **Template e riuso**: il coach può salvare un workout come template, copiare un
workout o un'intera settimana su altre date, e duplicare un workout modificandolo.

RF-04-D6 – **Inserimento esercizi da testo** resta disponibile: il coach incolla il programma
come lo scrive abitualmente (giorno, poi "work N: titolo" per ogni blocco) e il sistema
mostra un'**anteprima strutturata modificabile** prima del salvataggio. Il riconoscimento:
- aggancia ogni riga a un esercizio del catalogo per nome o alias;
- legge quantità e unità ("5' Row", "12/10 Cal Row", "400m Run", "30\" Plank");
- legge l'intensità: percentuale ("73%"), kg ("43/30"), zona ("Z2"), test di riferimento
  ("From Test 2K"), ritmo ("20-22 s/m");
- una percentuale senza esercizio esplicito ("5 x 2 73%") si riferisce all'esercizio del
  titolo;
- una riga "3 To 4 Sets" / "5 Rounds" apre un blocco ripetuto che include le righe
  successive fino a una riga vuota;
- le righe non riconosciute restano testo libero e sono segnalate.
Le righe `ranges:` del formato legacy non sono più necessarie ma, se presenti, vengono
accettate. Il formato legacy completo (`week:`, `day:monday`, `ex:`) resta importabile per i
programmi storici.

RF-04-D7 – **Stato di pubblicazione**: un workout è in bozza finché il coach non lo pubblica.
Gli atleti vedono solo i workout pubblicati; alla pubblicazione parte la notifica
(vedi [08-amministrazione.md](08-amministrazione.md)). Si può pubblicare un giorno o una
settimana intera in un colpo.

RF-04-D8 – **Gestione dei test** (sessioni di rilevazione dei massimali): il coach può
programmare un workout di tipo "test" su un esercizio del catalogo; l'atleta, al termine,
inserisce il risultato che viene salvato direttamente come nuovo massimale
(vedi [05-massimali-e-percentuali.md](05-massimali-e-percentuali.md), sezione "Gestione dei test").

RF-04-D9 – La visualizzazione per l'atleta calcola il carico personale per ogni riga con
percentuale, come oggi (RF-05-20), e mostra chiaramente quali test mancano.

RF-04-D10 – Solo coach e superuser possono creare, modificare, pubblicare, riordinare ed
eliminare workout, con verifica lato server (RF-01-07).

### Destinatari: allenamenti pubblici, dedicati e personali

Ogni workout ha un **destinatario** (`audience`):

| Destinatario | Chi lo crea | Chi lo vede |
|--------------|-------------|-------------|
| `all` (pubblico) | coach, superuser | tutti gli atleti abilitati. È la programmazione del box |
| `assigned` (dedicato) | coach, superuser | solo gli atleti assegnati, il coach, il superuser |
| `personal` (personale) | l'atleta per sé stesso | solo l'atleta, il suo coach, il superuser |

RF-04-D11 – **Allenamenti dedicati**: il coach può creare un workout e assegnarlo a uno o più
atleti (es. lavoro di recupero infortunio, preparazione a una gara, programma di forza
individuale). L'atleta lo vede nel proprio giorno, con un'etichetta "Dedicato", accanto alla
programmazione pubblica. Gli altri atleti non lo vedono e non compare nelle classifiche.

RF-04-D12 – **Allenamenti personali**: un atleta abilitato può crearsi esercizi propri
(riscaldamento specifico, lavoro accessorio, mobilità, skill) con lo stesso editor
strutturato, in versione semplificata. Compaiono nel proprio giorno con etichetta
"Personale", possono avere uno score e un massimale collegato, e non sono visibili agli altri
atleti.

RF-04-D13 – **Ricorrenza**: un workout dedicato o personale può essere programmato con
ricorrenza settimanale sui giorni scelti (es. lunedì, mercoledì, venerdì), con data di inizio
e data di fine facoltativa. Il sistema genera le occorrenze nel calendario; modificare la
regola aggiorna le occorrenze future e non quelle già eseguite. Una singola occorrenza può
essere saltata o modificata senza toccare la regola.

RF-04-D14 – Il coach vede gli allenamenti personali dei propri atleti nella scheda atleta e
può commentarli o convertirli in dedicati. Può inoltre creare un allenamento dedicato con
ricorrenza per conto dell'atleta.

RF-04-D15 – Ordine nel giorno per l'atleta: prima la programmazione pubblica, poi i dedicati,
poi i personali. Ogni gruppo mantiene il proprio ordinamento.

RF-04-D16 – Le analisi di [13-analisi-dati.md](13-analisi-dati.md) includono dedicati e
personali nella costanza e nei PR, ma le classifiche e i confronti tra atleti usano solo i
workout pubblici.

---

# Comportamento legacy (riferimento)

## Dashboard giornaliera (`/`, `/dashboard`, `/dashboard/date/<d>/<m>/<y>`)

RF-04-01 – La dashboard mostra i workout di **un singolo giorno**. Default: oggi. Parametri `year/month/day` in query o nel path. Data non valida (es. 31/02) → fallback al giorno 1 dello stesso mese.

RF-04-02 – Se l'utente non è abilitato (`is_enabled=false`) al posto della lista compaiono i testi "Atleta non abilitato" / "Attendi che il supremo coach ti ritenga degno".

RF-04-03 – Selettore data: header con data completa (es. "14 Settembre 2026"), frecce ◀◀ ▶▶ che spostano di **una settimana** (mantenendo il lunedì della settimana come giorno selezionato), e una striscia dei 7 giorni della settimana corrente (lunedì→domenica) con iniziale del giorno e numero; il giorno selezionato è evidenziato. Toccando la data si apre un popup con select anno (ultimi 4 anni), mese, giorno (1–30) — funzionalità parzialmente rotta, vedi Note.

RF-04-04 – I workout sono ordinati per `date`, `display_order`, `id` e mostrati come **accordion** chiusi: titolo = nome workout; corpo = descrizione (multilinea, newline → `<br>`), blocco percentuali (RF-05-20), toolbar.

RF-04-05 – Toolbar per ogni workout: icona "grafico" → pagina performance (tutti). Solo coach: icona matita → modifica, icona cestino → elimina (POST immediato, senza conferma).

RF-04-06 – Se il giorno non ha workout e l'utente è coach, compaiono i pulsanti "Add Workout" e "Add Weekly Workouts". Se ci sono workout e l'utente è coach, compare "Ordina Workouts".

RF-04-07 – Footer: se ci sono workout una **frase motivazionale** casuale, altrimenti una **frase da rest day** casuale (liste in [10-ui-navigazione.md](10-ui-navigazione.md)).

RF-04-08 – Barra inferiore fissa con pulsante "Menu".

## Creazione singolo workout (`/workout/add`) – coach

> La rotta è protetta solo da `login_required`, non da `superuser_required`; il link è visibile solo al coach. In Flutter va protetta lato API.

RF-04-09 – Campi: data (obbligatoria, default oggi), nome (2–150), descrizione (testo libero multilinea), ranges1, ranges2, ranges3 (opzionali, 2–100 caratteri ciascuno).

RF-04-10 – **Formato ranges**: `v1,v2,v3@Nome Esercizio`, es. `70,75,80@Back Squat` o `20@Back Squat`.
- Ogni valore intero; `+10` / `-5` (segno esplicito) sono **offset** in secondi (kind `offset`), altrimenti percentuale (kind `pct`) che deve essere > 0.
- Errori: manca `@` → "Formato ranges non valido. Usa 20@Back Squat oppure 20,30,40@Back Squat."; esercizio vuoto; valore non intero → "Valore range non valido: X"; percentuale ≤ 0 → "Percentuale non valida: X"; nessun valore → "Nessun range valido trovato.".

RF-04-11 – Al salvataggio: `display_order` = max del giorno + 1; `total_workouts_added` dell'utente +1; i range vengono inseriti con `order` progressivo globale (0,1,2… attraverso i tre gruppi). Messaggio "Workout inserito con successo!", log "New workout created", redirect a dashboard (di oggi, non della data del workout).

## Import settimanale (`/workout/week/add`) – coach

RF-04-12 – Un'unica textarea (min 10 caratteri) con il programma della settimana nel formato:

```
week:02/02/2026

day:monday

work 1:
Ev. 1.30' X 6 Sets
ex:
Set (1-2) 2 Squat Snatch 70%
Set (3-4) 2 Squat clean 75%
Set (5-6) 2 Squat Snatch 80%
ranges1:70,75,80@Squat Snatch
ranges2:70,75,80@Squat Clean

work 2:
AMRAP 12'
ex:
10 Pull-up
15 Push-up
20 Air Squat

day:tuesday
...
```

Regole di parsing:
- `week:dd/mm/yyyy` obbligatorio (altrimenti errore "Campo week non valido"); è la data del **lunedì**.
- Ogni `day:<nome inglese>` (monday…sunday, case-insensitive) apre un blocco; la data del workout = week + offset del giorno (giorno sconosciuto → data del week).
- Dentro un giorno ogni `work N:` apre un workout. Il testo tra `work N:` ed `ex:` è il **nome**; se non c'è `ex:` tutto il testo è il nome e la descrizione è vuota.
- Dopo `ex:` ogni riga non vuota è una riga della descrizione (le righe vengono unite con newline). Se il testo contiene virgole viene invece spezzato sulle virgole (comportamento di `_parse_list_items`, vedi Note).
- Le righe `ranges:`, `ranges1:`, `ranges2:`, `ranges3:` (formato `valori@Esercizio`) vengono estratte come gruppi di range e rimosse dalla descrizione. Valori separati da virgola.
- I range dell'import settimanale hanno `order = indice_gruppo*100 + indice_valore` e kind sempre `pct` (i segni +/- **non** sono gestiti qui: `int('+10')` = 10 diventa una percentuale).

RF-04-13 – Tutti i workout della settimana vengono creati in un'unica transazione; in caso di errore nessuno viene salvato e si mostra "Errore parsing workout: …". Successo → "Workout settimanali inseriti con successo!" e log con il testo completo incollato.

RF-04-14 – `display_order` è progressivo per giorno partendo dal max esistente + 1 (si può importare più volte la stessa settimana: i workout si accodano, non si sostituiscono).

## Modifica workout (`/workout/edit/<id>`) – proprietario o coach

RF-04-15 – Stesso form della creazione, precompilato. I range vengono ricostruiti in forma `v1,v2@Esercizio` raggruppati per esercizio (max 3 gruppi mostrati; i gruppi oltre il terzo vengono persi al salvataggio).

RF-04-16 – Al salvataggio tutti i range esistenti vengono cancellati e reinseriti. Se cambia la data, `display_order` viene ricalcolato come "ultimo del nuovo giorno". Messaggio "Workout aggiornato con successo!", log "Modified workout dd-mm-yyyy".

## Eliminazione workout (`/workout/delete/<id>`, POST) – proprietario o coach

RF-04-17 – Elimina workout, range e link performance. Messaggio "Allenamento eliminato con successo.", log "Deleted workout dd-mm-yyyy", redirect alla dashboard **del giorno del workout**.

## Ordinamento workout del giorno (`/workouts/order`) – coach

RF-04-18 – Pagina con la lista dei workout di una data (`#`, nome) e per ciascuno i pulsanti ▲ ▼ (disabilitati su primo/ultimo). All'apertura gli `display_order` del giorno vengono normalizzati a 1..N.

RF-04-19 – `POST /workouts/order/move/<id>` con `direction=up|down` scambia il `display_order` con il vicino e ritorna alla pagina.

## Cancellazione massiva per giorno (`/admin/workouts/delete-by-day`) – coach

RF-04-20 – Form con date picker (qualsiasi giorno: viene normalizzato al **lunedì** della settimana) e 8 checkbox: L M M G V S D + "TUTTI" (che seleziona/deseleziona tutte). Conferma JS "Confermi la cancellazione degli allenamenti selezionati?".

RF-04-21 – Elimina tutti i workout (di tutti gli utenti) della settimana nei giorni selezionati, con range e link. Messaggi: nessun giorno → "Seleziona almeno un giorno."; nessun workout → "Nessun allenamento trovato per i giorni selezionati."; ok → "N allenamenti eliminati con successo." + log.

## Note

- Il popup anno/mese/giorno del selettore data costruisce un URL `/dashboard/date/<mese>/<anno>` senza giorno (rotta inesistente) e ha un bug sull'indice del mese (`value+1` concatena stringhe). Da riprogettare in Flutter come date picker nativo.
- `_parse_list_items` spezza sulle virgole se presenti: una descrizione come "10 Pull-up, 15 Push-up" viene trasformata in due righe. Decidere se mantenere.
- Le percentuali con offset (`+10`) funzionano solo nel form singolo, non nell'import settimanale né nella visualizzazione (vedi RF-05 Note).
- `add_workout` e `add_weekly_workouts` non hanno `superuser_required`: qualsiasi atleta loggato che conosce l'URL può creare workout. Nel nuovo backend: solo coach.
- Dopo creazione singola il redirect va a "oggi" e non alla data del workout appena creato.
