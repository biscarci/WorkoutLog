# 08 – Amministrazione (coach)

> **Stato**: la sezione seguente fissa la direzione per la nuova app; il resto del documento
> descrive il comportamento legacy.

## Direzione per la nuova app

### Chi vede cosa

RF-08-D1 – Il **coach** ha accesso a: programmazione, catalogo esercizi, atleti (elenco,
inviti, abilitazione, scheda atleta con note), messaggi broadcast, analisi, log delle
proprie azioni e delle azioni degli atleti sui workout.

RF-08-D2 – Il **superuser** ha accesso a tutto quello del coach più: gestione completa degli
account (ruoli, superuser, eliminazione, revoca sessioni), log attività completo, export e
import dei dati, impostazioni del box (nome, logo, frasi motivazionali, zone cardiache di
default, template email e notifiche). Il superuser vede ogni dato di ogni utente (RF-01-09).

### Messaggi broadcast

RF-08-D3 – Il coach o il superuser può inviare un **messaggio** a: tutti gli atleti abilitati,
un gruppo selezionato di atleti, o un singolo atleta. Campi: titolo (max 80), testo (max
2000, con a capo), allegato facoltativo (immagine o PDF), data di scadenza facoltativa dopo
la quale non è più evidenziato.

RF-08-D4 – Il messaggio arriva come **notifica push** e come **email** (se l'atleta non ha
disattivato il canale email nelle preferenze) ed è consultabile nella sezione "Messaggi"
dell'app, con stato letto / non letto. Il badge dei non letti compare sull'icona della
sezione.

RF-08-D5 – Il mittente vede, per ogni messaggio, quanti e quali destinatari lo hanno letto.
Un messaggio può essere modificato entro 15 minuti dall'invio o ritirato; il ritiro lo
rimuove dalle app dei destinatari.

RF-08-D6 – I messaggi non sono una chat: gli atleti non rispondono in app. Un pulsante
"Contatta il coach" apre il canale scelto dal box (email, WhatsApp, telefono), configurato
nelle impostazioni.

RF-08-D7 – Messaggi in evidenza: un messaggio può essere marcato come "fissato" e compare in
cima alla schermata Oggi finché non scade o viene rimosso (es. chiusura del box, orari
festivi).

### Notifiche

RF-08-D8 – Eventi che generano notifica push (e, dove indicato, email):

| Evento | Destinatario | Push | Email |
|--------|--------------|------|-------|
| Invito | invitato | – | sì |
| Nuovo atleta registrato autonomamente | coach, superuser | sì | sì |
| Account attivato | atleta | sì | sì |
| Programmazione pubblicata o modificata per un giorno | atleti abilitati | sì | – |
| Allenamento dedicato assegnato o modificato | atleti assegnati | sì | – |
| Messaggio broadcast | destinatari | sì | sì (opzionale) |
| Nuovo PR dell'atleta | atleta | sì | – |
| Score inserito o corretto dal coach per conto dell'atleta | atleta | sì | – |
| Promemoria atleta inattivo | atleta | sì | sì |
| Massimale mancante per il workout di oggi | atleta | sì | – |
| Nuovo score su un workout (opzionale) | coach | sì | – |
| Cambio password, nuovo dispositivo | utente | – | sì |

RF-08-D9 – Ogni utente gestisce le preferenze per tipo di notifica e per canale (push,
email) nel profilo. Le notifiche di sicurezza (cambio password, nuovo dispositivo) e gli
inviti non sono disattivabili.

RF-08-D10 – Le notifiche push usano Firebase Cloud Messaging su Android e iOS. I token dei
dispositivi sono salvati in `PushToken` (vedi [02-modello-dati.md](02-modello-dati.md)) e
rimossi al logout o quando il provider li segnala non validi.

RF-08-D11 – Le notifiche di programmazione sono **raggruppate**: se il coach pubblica sette
giorni in un colpo, l'atleta riceve una sola notifica "Programmazione della settimana
pubblicata". Le modifiche entro 10 minuti dalla pubblicazione non generano nuove notifiche.

### Log attività

RF-08-D12 – Ogni azione di scrittura e ogni evento di sicurezza genera una riga di
`ActivityLog` con: chi (utente e ruolo), cosa (codice evento), quando, su quale oggetto
(tipo e id), per conto di chi (se il coach agisce per un atleta), dettagli (valori prima e
dopo per le modifiche), indirizzo IP e dispositivo.

RF-08-D13 – Eventi tracciati, per area:

| Area | Eventi |
|------|--------|
| Autenticazione | `user_registered`, `login_ok`, `login_failed`, `logout`, `password_reset_requested`, `password_reset`, `password_changed`, `session_revoked`, `account_deleted` |
| Inviti e account | `invitation_sent`, `invitation_resent`, `invitation_revoked`, `invitation_accepted`, `user_enabled`, `user_disabled`, `role_changed`, `user_deleted`, `profile_updated` |
| Workout | `workout_created`, `workout_updated`, `workout_published`, `workout_unpublished`, `workout_deleted`, `workout_reordered`, `workout_assigned`, `workout_copied`, `recurrence_created`, `recurrence_updated`, `recurrence_deleted`, `weekly_import` |
| Score | `performance_created`, `performance_updated`, `performance_deleted` (con `on_behalf_of` se dal coach) |
| Massimali | `max_record_created`, `max_record_updated`, `max_record_deleted` |
| Catalogo | `exercise_created`, `exercise_updated`, `exercise_deactivated`, `exercise_reactivated`, `exercise_deleted` |
| Cardio | `device_paired`, `device_removed`, `session_saved`, `session_deleted`, `health_access_granted`, `health_access_revoked` |
| Messaggi | `message_sent`, `message_updated`, `message_withdrawn`, `message_read` |
| Notifiche | `notification_sent`, `notification_failed`, `email_sent`, `email_failed` |
| Sistema | `csv_export`, `csv_import`, `settings_updated`, `migration_run` |

RF-08-D14 – Il **superuser** consulta il log completo con filtri per utente, ruolo, area,
evento, oggetto e intervallo di date, ricerca testuale, e può esportarlo in CSV. Il
**coach** consulta il log limitato alle azioni proprie e a quelle degli atleti su workout,
score e massimali. Gli atleti vedono solo la propria cronologia di accessi e dispositivi.

RF-08-D15 – Il log è **append-only**: nessun ruolo può modificare o cancellare righe. La
conservazione è di 24 mesi, poi archiviazione.

RF-08-D16 – Le modifiche a dati sensibili (ruolo, abilitazione, eliminazione account,
password reset da amministratore) mostrano nel log anche il valore precedente.

### Promemoria e gestione atleti

RF-08-D17 – Dalla lista atleti il coach vede stato, ultimo accesso, ultimo score, ultimo
test, e può inviare un promemoria a chi non registra score da più di N giorni (RF-13-15).

RF-08-D18 – Il coach può inserire o correggere score e massimali per conto di un atleta
(RF-05-D6, RF-14-11); l'azione è tracciata con `on_behalf_of` e notificata all'atleta.

---

# Comportamento legacy (riferimento)

Tutte le funzioni di questo documento richiedono `is_superuser = true` (altrimenti HTTP 403).

## Menu coach

RF-08-01 – Nel menu il coach vede in più: **I'M THE COACH** (dashboard admin), **ESERCIZI** (catalogo, vedi [05](05-massimali-e-percentuali.md)), **DELETE WORKOUTS** (cancellazione per giorno, vedi RF-04-20).

## Dashboard admin (`/admin/dashboard`)

RF-08-02 – Quattro riquadri:
- **Atlets Statistics**: totale utenti, utenti attivi (`last_login` negli ultimi 30 giorni), nuovi utenti (`created_at` negli ultimi 30 giorni), link "Atlets List".
- **Workout Analytics**: totale workout, workout con data negli ultimi 30 giorni, nome di workout più frequente (etichettato erroneamente "Last Workout Added").
- **System Health**: uptime del processo, connessioni DB in uso, "Last Backup" (valore fittizio: ieri).
- **Database Tools**: pulsante **Export** (CSV) e **Import** (file picker CSV, submit immediato).

RF-08-03 – **Recent Activities**: tabella del `Log` (utente, azione, ora `HH:MM dd/mm`) filtrabile per giorno con un date picker ("Giorno log") + Filtra / Reset. Senza filtro mostra **tutto** il log in ordine cronologico crescente.

## Gestione utenti (`/admin/users`)

RF-08-04 – Tabella di tutti gli utenti: username, toggle abilitato (icona on/off), reset password, rimuovi. Toccando la riga si espande un dettaglio con nome, cognome, email, ultimo accesso, data creazione, abilitato sì/no.

RF-08-05 – `POST /admin/manage_user/<id>`: inverte `is_enabled`. Messaggio "User X abilitato/disabilitato con successo." + log.

RF-08-06 – `POST /admin/delete_user/<id>`: elimina l'utente e tutti i suoi dati (RF-02-02). Non è possibile eliminare se stessi ("You cannot delete your own account."). Nessuna conferma lato UI.

RF-08-07 – Non esiste un modo per promuovere/declassare un utente a coach dalla UI (solo tramite registrazione con codice, CLI o import CSV).

RF-08-08 – `POST /admin/reset_password/<id>`: imposta la password dell'utente alla costante **`seiunpollo`**. Messaggio "Password resettata per X." + log. Funziona anche su altri coach.

## Export CSV (`/export/csv`)

RF-08-09 – Scarica `workoutlog_export_YYYYMMDD_HHMMSS.csv`: un unico file "a tabella larga" con colonna `table` che indica l'entità della riga. Colonne:

```
table,id,user_id,username,password,email,name,surname,created_at,last_login,
is_superuser,is_enabled,total_workouts_added,date,display_order,description,
workout_id,performance_id,value,exercise,range_order,weight,reps,action,timestamp,log_user
```

Entità esportate nell'ordine: `user` (**incluso l'hash password**), `workout`, `range`, `performance`, `workout_performance`, `user_statistic`. Il `Log` e `ExerciseCatalog` **non** vengono esportati. Date in ISO 8601. Log "CSV export".

## Import CSV (`/import/csv`, POST multipart `csv_file`)

RF-08-10 – Legge lo stesso formato (UTF-8 con BOM tollerato). Regole:
- Manca la colonna `table` → errore.
- Ordine di import: user → workout → range → performance → workout_performance → user_statistic → log.
- **User**: se username/email esistono già su un altro id, l'id del CSV viene rimappato a quello esistente e la riga saltata; se l'utente esiste con lo stesso id e tutti i campi coincidono → saltato; altrimenti aggiornato/creato (nuovi richiedono username, email, password hash).
- **Workout / Performance / Range / Link / Statistic**: dedup su tutti i campi significativi (es. workout: user+date+name+description); i duplicati vengono saltati e gli id rimappati per le righe figlie. Gli id del CSV vengono preservati quando possibile.
- **Log**: righe con `table=log` importate con dedup su user+action+timestamp.
- Tutto in una transazione: qualsiasi errore → rollback e messaggio "Errore durante import CSV: …".
- Messaggio finale con i conteggi per entità e gli "skipped". Log "CSV import".

Nota: `Range.kind` non è esportato/importato (perso nei round-trip).

## Comandi CLI (Flask)

RF-08-11 – `flask create-superuser --username --email --password [--name --surname]`: crea il primo coach. Fallisce se esiste già un utente con quello username **o qualsiasi superuser**.

RF-08-12 – `flask seed-exercises`: popola il catalogo con la lista `movement_choices` + tutti gli esercizi trovati in massimali e range (unit `kg`, `reps` per "dips"), saltando quelli già presenti.

RF-08-13 – `flask cleanup-exercises [--apply]`: unifica le grafie duplicate (es. "Split jerk" e "Split Jerk"): la grafia più usata nei massimali vince; applica `EXERCISE_MERGES`; rinomina massimali e range, fonde/rinomina/elimina le voci di catalogo duplicate. Senza `--apply` stampa solo il piano.

RF-08-14 – Bootstrap superuser da env (`ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, …): funzione presente ma **mai invocata** all'avvio.

## Azioni loggate (elenco completo)

| Azione | Chi |
|--------|-----|
| New user registered / New admin registered | anonimo → nuovo utente |
| Login successful | utente |
| Login failed for username: X / for an unspecified username | `---` |
| User X logged out at … | utente |
| New workout created | coach |
| Weekly workouts created + testo incollato | coach |
| Modified workout dd-mm-yyyy / Deleted workout dd-mm-yyyy | coach |
| Bulk deleted workouts for week … and days: … | coach |
| New performance added / Quick performance added from timer / Performance updated / Performance deleted | atleta |
| User stats added / updated / deleted: N | atleta |
| Exercise added / updated / attivato / disattivato / deleted / deactivated (in use) / reactivated / Exercises imported | coach |
| User: X enabled/disabled, Deleted user X, Reset password for X | coach |
| CSV export / CSV import | coach |

## Note

- `delete_user` chiama `logger(current_user.username, …)` invece dell'id: il log fallisce con `ValueError` e l'eccezione viene catturata come "An error occurred while deleting the user" **dopo** il commit → l'utente viene eliminato ma l'UI mostra un errore. Bug.
- L'export include gli hash delle password: nel nuovo sistema separare backup tecnico (solo admin, cifrato) da export dati.
- La dashboard mostra "DB connections" e "uptime" del singolo processo gunicorn: informazioni poco significative, si possono eliminare.
- Il reset password a costante nota è un rischio: preferire link/codice temporaneo.
