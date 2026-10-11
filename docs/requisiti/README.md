# LIFTOFF – Requisiti funzionali

Raccolta dei requisiti funzionali dell'applicazione **LIFTOFF** ("Just Training"), estratti dal codice
attuale (Flask + Jinja + SQLAlchemy, PWA mobile-first). Servono come base per la riscrittura
dell'app in **Flutter** con un backend separato.

**Stato della revisione**: i documenti 01, 02, 03, 06 e i nuovi 12, 13, 14 descrivono il sistema
**target** (app Flutter Android/iOS + dashboard web + backend API). I documenti 04, 05, 08 e 10
hanno in testa una sezione "Direzione per la nuova app" seguita dal comportamento legacy. I
restanti (07, 09) descrivono ancora il legacy e vanno riscritti.

Ogni documento legacy descrive *cosa* fa il sistema oggi, con le regole di business esatte, non *come* è
implementato. Dove il comportamento attuale è un bug, un'incongruenza o codice morto, è segnalato
nella sezione "Note" del documento e riepilogato in [11-note-migrazione-flutter.md](11-note-migrazione-flutter.md).

## Indice

| # | Documento | Contenuto |
|---|-----------|-----------|
| 01 | [Panoramica e ruoli](01-panoramica-e-ruoli.md) | Scopo dell'app, ruoli (atleta / coach / superuser), abilitazione, invito |
| 02 | [Modello dati](02-modello-dati.md) | Entità, campi, relazioni, vincoli |
| 03 | [Autenticazione e profilo](03-autenticazione-e-profilo.md) | Invito via email, registrazione, login a token, recupero password, profilo, cancellazione account |
| 04 | [Workout](04-workout.md) | Dashboard giornaliera, creazione singola e settimanale, modifica, ordinamento, cancellazione |
| 05 | [Catalogo esercizi, massimali e percentuali](05-massimali-e-percentuali.md) | Unità di misura, formati, calcolo dei carichi dalle percentuali, storico 1RM |
| 06 | [Performance (score)](06-performance.md) | Score strutturato per tipo di risultato, inserimento da timer, classifica, storico |
| 07 | [Timer](07-timer.md) | Timer AMRAP / FOR TIME / EMOM / TABATA / FORZA / cronometro, countdown, salvataggio score |
| 08 | [Amministrazione](08-amministrazione.md) | Dashboard coach, gestione utenti, log, export/import CSV, comandi CLI |
| 09 | [Rotte e proposta API](09-rotte-e-api.md) | Mappa completa delle rotte attuali e bozza di API REST per il client Flutter |
| 10 | [UI, navigazione e PWA](10-ui-navigazione.md) | Tema, struttura di navigazione, testi, frasi motivazionali, requisiti mobile |
| 11 | [Note per la migrazione Flutter](11-note-migrazione-flutter.md) | Bug noti, codice morto, decisioni aperte, cosa cambiare |
| 12 | [Monitoraggio cardio](12-monitoraggio-cardio.md) | Fascia Polar / BLE, Apple Watch, Wear OS, zone cardiache, sessioni |
| 13 | [Analisi dei dati](13-analisi-dati.md) | Andamento massimali, benchmark, costanza, intensità, panoramica atleti per il coach |
| 14 | [Dashboard web](14-dashboard-web.md) | Web app da PC per atleti, coach e superuser |

## Come leggere i requisiti

- **RF-xx-nn**: requisito funzionale numerato per documento (es. RF-04-03 = terzo requisito del doc 04).
- **Regola**: comportamento di business che va replicato esattamente.
- **Nota**: comportamento attuale discutibile o incompleto; da decidere in fase di revisione.

## Stack attuale (per riferimento)

- Backend: Python 3, Flask 3.1, Flask-Login, Flask-WTF (CSRF), Flask-SQLAlchemy 3.1, Flask-Migrate/Alembic.
- DB: SQLite in locale (`FLASK_DEBUG=1`), PostgreSQL in produzione via `DATABASE_URL` (SSL obbligatorio).
- Frontend: template Jinja server-side, Bootstrap 5 (Bootstrap-Flask), Bootstrap Icons, Chart.js 4 (grafico massimali), JavaScript vanilla per il timer.
- Deploy: gunicorn. Variabili d'ambiente: `SECRET_KEY`, `DATABASE_URL`, `FLASK_DEBUG`, `ADMIN_REG_CODE`, `ADMIN_USERNAME/EMAIL/PASSWORD/NAME/SURNAME` (bootstrap superuser, funzione presente ma non invocata).
- PWA: manifest `LIFTOFF`, display standalone, orientamento portrait, icone 192/512, banner di installazione su login.
