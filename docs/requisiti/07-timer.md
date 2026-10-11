# 07 – Timer

Il timer è interamente client-side (JavaScript). In Flutter diventa una feature nativa: non
richiede API se non per il salvataggio dello score finale (RF-06-04).

## Setup (`/workout/<id>/timer-setup`)

RF-07-01 – Pagina con il nome del workout e 6 pulsanti tipo: **AMRAP**, **FOR TIME**, **EMOM**, **TABATA**, **FORZA**, **TIMER**. Selezionandone uno compare il pannello di configurazione e il pulsante "AVVIA TIMER". Pulsante "Indietro" → pagina performance.

RF-07-02 – Configurazioni per tipo:

| Tipo | Configurazione | Default |
|------|----------------|---------|
| AMRAP | lista ordinata di segmenti: **AMRAP** (durata, con toggle min/sec) e **Pausa** (secondi). Almeno un AMRAP. | AMRAP 10 min; pausa 60 s |
| FOR TIME | time cap in minuti (1–180); direzione **Countdown** (default) o **Countup** | 20 min, countdown |
| EMOM | lista ordinata di segmenti: **EMOM** (intervallo con toggle min/sec × N round) e **Pausa** (secondi). Almeno un EMOM. | ogni 1 min × 10 round; pausa 60 s |
| TABATA | serie (1–100), lavoro (5–300 s), riposo (5–300 s) | 8 × 20 s / 10 s |
| FORZA | nessuna: timer work/rest manuale con contatore round | – |
| TIMER | nessuna: cronometro libero | – |

RF-07-02b – **Nuova app**: nella schermata di setup, se l'atleta ha una fascia cardiaca
associata, è presente il pannello cardio con stato connessione, battito, zona e batteria
(vedi [12-monitoraggio-cardio.md](12-monitoraggio-cardio.md), RF-12-05). Durante
l'esecuzione il pannello resta in forma compatta (RF-12-05b) e a fine timer la sessione
cardio viene proposta insieme allo score (RF-12-07, RF-12-08).

RF-07-03 – La configurazione viene passata alla pagina timer (attualmente via `sessionStorage`, chiave `timerConfig`). Se manca, il timer rimanda al setup.

## Esecuzione (`/workout/<id>/timer`)

### Countdown iniziale

RF-07-04 – Per tutti i tipi tranne TIMER: overlay "Preparati" con conto alla rovescia **10 → 1**, beep (880 Hz, 0.15 s) sugli ultimi 3 secondi, poi "GO!" con beep lungo (1320 Hz, 0.6 s) e avvio dopo 0.7 s. TIMER parte subito.

### Fasi

RF-07-05 – Il timer è una sequenza di **fasi** `{label, duration, isRest}` costruita dalla configurazione:
- FOR TIME: una fase "FOR TIME" di `cap × 60` s.
- AMRAP: per ogni segmento, fase "AMRAP" (se più AMRAP: "AMRAP k/N" dove k conta **a scalare** i rimanenti) o "RIPOSO".
- EMOM: per ogni segmento EMOM, `rounds` fasi di `interval` s etichettate "EMOM – r/N" (r a scalare; se più blocchi "EMOM n – r/N"); "RIPOSO" per le pause.
- TABATA: per ogni serie "LAVORO r/N" (work s) e, tranne l'ultima, "RIPOSO r/N" (rest s).

RF-07-06 – Per ogni fase: etichetta (in grigio se riposo), cifre grandi `mm:ss` che scendono, barra di progresso che si svuota, "Trascorso: mm:ss" totale. Beep corto sugli ultimi 3 secondi di ogni fase, beep medio (1320 Hz, 0.5 s) al cambio fase, beep lungo (1 s) alla fine.

RF-07-07 – FOR TIME **countup**: le cifre salgono da 00:00, la barra si riempie, sotto "Time cap: mm:ss"; al raggiungimento del cap termina automaticamente.

RF-07-08 – FORZA: dopo il countdown parte in fase "WORK" con un cronometro di fase da 00:00 e "Trascorso" totale. Pulsante **REST/WORK** alterna le fasi: passando a WORK il contatore round +1 e beep 1320 Hz; passando a REST beep 880 Hz. Il contatore round è visibile ma senza pulsanti +/−.

RF-07-09 – TIMER: cronometro libero da 00:00, pulsanti **RESET** e STOP. Nessun countdown, nessun round.

### Round counter (AMRAP, FOR TIME, FORZA)

RF-07-10 – Sotto il timer compare "Rounds" con pulsanti **−** e **+** (min 0). In AMRAP e FOR TIME anche **tutta l'area del cronometro** è tap-zone: un tocco = +1 round (hint "Tocca lo schermo per +1 round"). Ogni +1 dà vibrazione (35 ms) e un flash bianco dello schermo.

### Controlli

RF-07-11 – Barra inferiore: **PAUSA/RIPRENDI** e **STOP** (tipi a fasi); **REST/WORK** e STOP (FORZA); **RESET** e STOP (TIMER). STOP apre un dialogo "Terminare il workout? Il tempo verrà fermato." con ANNULLA / TERMINA.

RF-07-12 – Il conteggio è ancorato all'orologio di sistema: al ritorno da background vengono recuperati in un colpo solo i secondi persi (iOS congela i timer). In pausa l'ancora viene azzerata per non recuperare i secondi di pausa. In Flutter: usare `DateTime`/`Stopwatch` e ricalcolare al resume.

RF-07-13 – **Schermo sempre acceso** durante countdown e timer (Wake Lock API con fallback video muto su iOS vecchi). In Flutter: `wakelock_plus` o equivalente. Rilasciato alla fine.

RF-07-14 – Pannello inferiore richiudibile "▾ Mostra workout / ▴ Nascondi workout" (chiuso di default) con descrizione del workout e i carichi in % (solo per esercizi con massimale presente, formato "Esercizio – valore unità" + badge `pct% @valore unità`).

### Fine

RF-07-15 – Overlay finale: titolo **FINITO!** (fine naturale) o **TERMINATO** (stop manuale), tempo totale `mm:ss` (per FORZA anche "– N rounds"), pulsanti **SALVA SCORE** (non per FORZA e TIMER) e **TORNA AL WORKOUT**.

RF-07-16 – SALVA SCORE apre un modale con descrizione precompilata (editabile, 2–200 caratteri) e data odierna, e invia a `quick-add`. Testo generato:
- FOR TIME (non stoppato): `FOR TIME – mm:ss[ – N rounds]`
- TABATA: `TABATA {serie}×{work}s/{rest}s – mm:ss`
- AMRAP: `AMRAP – mm:ss[ – N rounds][ (stop)]` oppure `{k}×AMRAP – …` se più blocchi
- altri / FOR TIME stoppato: `{TIPO} – mm:ss[ (stop)]`

## Audio

RF-07-17 – Beep generati con oscillatore square (Web Audio). Frequenze: 880 Hz (avviso), 1320 Hz (cambio fase / fine). In Flutter: file audio brevi o sintesi; deve funzionare anche con il telefono in modalità silenziosa? (da decidere; su iOS il web audio segue lo switch silenzioso).

## Note

- Configurazione EMOM/AMRAP: l'input accetta valori 1–999; i secondi per le pause 5–3600.
- Non esiste persistenza dello stato del timer: se la pagina viene ricaricata il timer riparte dal setup. In Flutter valutare il ripristino dopo kill dell'app.
- Il timer FORZA non ha un pulsante di pausa.
