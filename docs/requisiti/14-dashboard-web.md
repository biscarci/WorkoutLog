# 14 – Dashboard web

Funzionalità nuova. Un'applicazione web consultabile da PC, complementare all'app mobile,
che condivide lo stesso backend e le stesse API. Serve a rendere fruibili su schermo grande
le statistiche, le analisi e le operazioni di gestione che sul telefono sono scomode.

## Principi

- **Stesso backend, stesse API, stessi permessi**. La web app non ha logica propria: mostra
  gli stessi dati dell'app mobile con layout adatto al desktop.
- **Stesso account**. Login con le credenziali dell'app; i tre ruoli valgono identici.
- **Nessuna duplicazione di funzionalità operative "da campo"**: timer e connessione alla
  fascia cardiaca restano solo sull'app mobile.
- Responsive: utilizzabile anche da tablet. Su telefono rimanda all'app.

## Tecnologia

Due opzioni, da decidere in fase di progettazione:

| Opzione | Vantaggi | Svantaggi |
|---------|----------|-----------|
| **Flutter Web** dallo stesso codebase dell'app mobile | un solo codice per modelli, chiamate API e logica; le schermate di analisi si riusano | rendering meno fluido per pagine con tabelle e testi lunghi; SEO irrilevante ma bundle iniziale pesante |
| Web app separata (React/Vue) | UI desktop più naturale, tabelle e grafici maturi | secondo codebase da mantenere |

Raccomandazione: **Flutter Web** con layout adattivo, almeno per la prima versione, per non
raddoppiare il lavoro. Si valuta il passaggio a un frontend separato solo se l'esperienza su
tabelle e grafici risultasse insufficiente.

## Funzionalità per ruolo

### Atleta

RF-14-01 – Home con riepilogo: allenamenti della settimana, ultimi score, PR recenti,
indicatore di costanza.

RF-14-02 – Calendario mensile della programmazione con dettaglio del workout al clic e
proprio score accanto.

RF-14-03 – Tutte le analisi personali di [13-analisi-dati.md](13-analisi-dati.md) con grafici
a schermo intero, tabelle ordinabili e **export CSV** dei propri massimali e score.

RF-14-04 – Gestione massimali: inserimento, modifica, storico, con vista tabellare di tutti
gli esercizi.

RF-14-05 – Profilo, dispositivi, sessioni attive, cancellazione account, come sull'app.

### Coach

RF-14-06 – Tutto quello dell'atleta, più la **vista di programmazione settimanale**: griglia
con i sette giorni in colonna e i workout in riga, trascinabili per riordinare o spostare di
giorno, con inserimento e modifica in un pannello laterale. È l'interfaccia principale per il
nuovo processo di inserimento dei workout (vedi [04-workout.md](04-workout.md)).

RF-14-07 – Copia di una settimana o di un singolo giorno su un'altra data.

RF-14-08 – Catalogo esercizi con tabella filtrabile, modifica in linea, gestione test
(vedi [05-massimali-e-percentuali.md](05-massimali-e-percentuali.md)).

RF-14-09 – Gestione atleti: elenco con stato, ultimo accesso, inviti pendenti, invio invito,
abilitazione, reinvio e revoca inviti.

RF-14-10 – Panoramica atleti, scheda atleta, analisi del workout e della programmazione di
[13-analisi-dati.md](13-analisi-dati.md).

RF-14-11 – Score di un workout in tabella con modifica in linea e inserimento per conto di
un atleta (es. atleta senza telefono in palestra), tracciato nel log come "inserito dal coach".

### Superuser

RF-14-12 – Tutto quello del coach, più gestione completa degli account (ruoli, superuser,
eliminazione), log attività con filtri e ricerca, export e import dei dati, impostazioni del
box (nome, logo, zone cardiache di default, template email).

## Requisiti trasversali

RF-14-13 – Autenticazione con gli stessi token dell'app; il refresh token è conservato in
cookie `HttpOnly` `Secure` `SameSite=Strict`, l'access token in memoria.

RF-14-14 – Le operazioni di scrittura fatte dal web compaiono sull'app mobile al successivo
aggiornamento senza ulteriori passaggi.

RF-14-15 – Grafici con la stessa palette e le stesse convenzioni dell'app (colori delle zone
cardiache, direzione "meglio se…").

RF-14-16 – Accessibilità di base: navigazione da tastiera, contrasto adeguato, etichette sui
controlli.

## Impatti sugli altri documenti

- [09-rotte-e-api.md](09-rotte-e-api.md): le API devono servire entrambi i client; endpoint
  aggiuntivi per copia settimana e inserimento score per conto terzi.
- [10-ui-navigazione.md](10-ui-navigazione.md): mappa di navigazione della web app.
- [11-note-migrazione-flutter.md](11-note-migrazione-flutter.md): struttura del progetto
  Flutter multi-piattaforma.
