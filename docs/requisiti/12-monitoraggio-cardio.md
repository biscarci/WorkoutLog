# 12 – Monitoraggio cardio e dispositivi indossabili

Funzionalità nuova, non presente nel sistema legacy. Permette di associare a ogni esecuzione di
un workout la traccia della frequenza cardiaca (FC) rilevata da una fascia o da uno smartwatch,
per arricchire lo score con dati oggettivi di intensità.

## Dispositivi supportati

| Sorgente | Piattaforma | Integrazione | Priorità |
|----------|-------------|--------------|----------|
| Fascia cardiaca **Polar** (H10, H9, Verity Sense) | Android e iOS | Bluetooth Low Energy, profilo standard *Heart Rate Service* (GATT 0x180D). Nessun SDK proprietario necessario per la FC in tempo reale | **MVP** |
| Altre fasce BLE standard (Garmin HRM, Wahoo, Coospo…) | Android e iOS | Stesso profilo GATT: funzionano senza sviluppo aggiuntivo | MVP (non testate ufficialmente) |
| **Apple Watch** | iOS | HealthKit: lettura delle sessioni di allenamento e dei campioni FC registrati dall'orologio. In tempo reale solo con una companion app watchOS (fase 2) | Fase 2 |
| Smartwatch **Wear OS** / Google (Pixel Watch, Galaxy Watch, Fitbit) | Android | Health Connect: lettura delle sessioni e dei campioni FC. Tempo reale solo con app Wear OS dedicata (fase 2) | Fase 2 |
| Polar Flow (cloud) | entrambe | Polar AccessLink API (OAuth): import a posteriori delle sessioni registrate con orologi Polar | Fase 3, opzionale |

Il canale primario è la connessione BLE diretta dall'app alla fascia: è l'unico che funziona
identico su Android e iOS e dà la FC in tempo reale durante il timer.

## Requisiti funzionali

### Connessione dispositivo

RF-12-01 – Dal profilo, sezione "Dispositivi", l'atleta può cercare e associare una fascia BLE.
L'app richiede i permessi Bluetooth (e posizione su Android dove richiesto) spiegandone il motivo
prima della richiesta di sistema.

RF-12-02 – La fascia associata viene ricordata (nome e identificativo) e riconnessa
automaticamente all'avvio del timer, senza ripetere la ricerca.

RF-12-03 – Su iOS l'atleta può abilitare la lettura da Apple Health; su Android da Health
Connect. L'app chiede solo i permessi di lettura per frequenza cardiaca e sessioni di
allenamento.

RF-12-04 – L'atleta può dissociare un dispositivo o revocare l'accesso a Health in qualsiasi
momento.

### Registrazione durante il workout

RF-12-05 – **Pannello cardio nella preparazione del workout.** Nella pagina di dettaglio del
workout e nella schermata di impostazione del timer (vedi [07-timer.md](07-timer.md), Setup),
se l'atleta ha una fascia associata compare un pannello con:
- stato della connessione (in ricerca, connessa, non trovata) con riconnessione automatica e
  pulsante per riprovare;
- battito istantaneo in bpm, aggiornato in tempo reale;
- zona corrente (Z1–Z5) con colore e percentuale della FC massima;
- livello batteria della fascia, se esposto dal dispositivo;
- FC a riposo rilevata in quel momento, utile come riferimento pre-allenamento.

Il pannello permette di verificare che la fascia funzioni prima di avviare il timer. Se non
c'è nessuna fascia associata, compare un invito discreto ad associarne una, che porta alla
sezione Dispositivi del profilo.

RF-12-05b – **Durante il timer** il pannello resta visibile in forma compatta: bpm, zona con
colore di sfondo, tempo trascorso nella zona corrente e, a richiesta, la barra dei tempi per
zona dall'inizio. Il timer non deve perdere leggibilità: il cardio sta in una fascia dedicata
sopra o sotto il cronometro.

RF-12-05c – Feedback opzionale: l'atleta può impostare una zona obiettivo per il workout e
ricevere un segnale acustico o vibrazione quando esce dalla zona, disattivabile. Se il
workout prescrive una zona su una riga (RF-04-D2, intensità `hr_zone`), quella zona è
l'obiettivo predefinito e il pannello mostra "in zona" / "sopra" / "sotto".

RF-12-06 – Dall'avvio alla fine del timer l'app campiona la FC almeno una volta al secondo e
la conserva localmente. Una perdita momentanea di connessione non interrompe il timer; i
campioni mancanti sono lasciati vuoti, non interpolati.

RF-12-07 – Al termine, i campioni vengono aggregati in una **WorkoutSession** (vedi
[02-modello-dati.md](02-modello-dati.md)): FC media, FC massima, FC minima, tempo per zona,
durata, e la serie completa dei campioni.

RF-12-08 – La sessione viene proposta insieme allo score precompilato. L'atleta può salvarla,
scartarla, oppure salvare lo score senza la sessione.

RF-12-09 – Il caricamento al server è asincrono e ripetuto se fallisce (offline). La sessione
resta consultabile localmente nel frattempo.

### Import da smartwatch

RF-12-10 – Dopo un workout, se l'atleta ha abilitato Health, l'app propone le sessioni di
allenamento registrate dall'orologio nell'intervallo temporale del workout (±15 minuti) e
permette di collegarne una allo score.

RF-12-11 – I dati importati sono trattati come una WorkoutSession con `source = healthkit`
o `health_connect`.

### Zone cardiache

RF-12-12 – La FC massima dell'atleta è impostabile nel profilo; se assente si usa
`220 − età` se la data di nascita è nota, altrimenti le zone non sono calcolate.

RF-12-13 – Zone di default (percentuale della FC massima): Z1 50–60, Z2 60–70, Z3 70–80,
Z4 80–90, Z5 90–100. Il coach può personalizzarle per singolo atleta.

### Visibilità

RF-12-14 – La sessione cardio è visibile all'atleta, al coach e al superuser accanto allo
score. Gli altri atleti vedono solo lo score, non i dati cardio.

RF-12-15 – I dati cardio sono dati sanitari: l'informativa privacy li cita esplicitamente,
l'atleta può eliminarli singolarmente e vengono cancellati con l'account.

## Impatti sugli altri documenti

- [02-modello-dati.md](02-modello-dati.md): entità `WearableDevice`, `WorkoutSession`,
  `HeartRateSample`; campi `birth_date`, `max_heart_rate` su User.
- [07-timer.md](07-timer.md): indicatore FC e zone nel timer.
- [13-analisi-dati.md](13-analisi-dati.md): analisi dell'intensità nel tempo.
- [11-note-migrazione-flutter.md](11-note-migrazione-flutter.md): pacchetti Flutter.

## Note tecniche

- Flutter: `flutter_blue_plus` o `flutter_reactive_ble` per BLE; `health` per HealthKit e
  Health Connect. Nessuna dipendenza da SDK Polar per la FC.
- Su iOS serve la capability *Bluetooth* con descrizione in Info.plist; su Android i permessi
  `BLUETOOTH_SCAN` / `BLUETOOTH_CONNECT` (API 31+).
- La registrazione in background (schermo spento) richiede su iOS la modalità background
  `bluetooth-central`, su Android un foreground service con notifica persistente.
- Serie di campioni: un workout di 20 minuti a 1 Hz produce 1200 punti; salvarli come array
  compresso in una colonna `jsonb`/`bytea`, non una riga per campione.
