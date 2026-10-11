# 11 – Note per la migrazione a Flutter

Riepilogo di bug, codice morto e decisioni da prendere prima di riscrivere. Ogni voce rimanda
al documento in cui è descritta.

## Bug e incongruenze del sistema attuale

| # | Problema | Dove | Impatto |
|---|----------|------|---------|
| B1 | `Range.kind='offset'` (`+10` s) salvato ma mostrato come percentuale; non gestito nell'import settimanale né nella modifica | [05](05-massimali-e-percentuali.md), [04](04-workout.md) | Feature "offset sul pace" incompleta |
| B2 | Nessuna migrazione per la colonna `Range.kind` | [02](02-modello-dati.md) | Deploy prod fallirebbe |
| B3 | `add_workout` / `add_weekly_workouts` non richiedono superuser | [04](04-workout.md) | Sicurezza |
| B4 | Popup selezione anno/mese/giorno in dashboard rotto | [04](04-workout.md) | UX |
| B5 | Storico massimali mostra sempre "kg" e "best = max" anche per tempi/pace | [05](05-massimali-e-percentuali.md) | Dati fuorvianti per esercizi a tempo |
| B6 | `capitalize()` sullo score abbassa il resto del testo | [06](06-performance.md) | Score alterato |
| B7 | `delete_user` logga con username → eccezione dopo il commit, UI mostra errore | [08](08-amministrazione.md) | Confusione admin |
| B8 | `_parse_list_items` spezza le righe sulle virgole | [04](04-workout.md) | Descrizioni alterate |
| B9 | Frase rest day: la prima non viene mai estratta | [10](10-ui-navigazione.md) | Cosmetico |
| B10 | Redirect dopo creazione workout va a oggi, non alla data creata | [04](04-workout.md) | UX |
| B11 | Export CSV include gli hash password e non include catalogo esercizi, log, `Range.kind` | [08](08-amministrazione.md) | Backup incompleto / rischio |
| B12 | Reset password a costante `seiunpollo` | [08](08-amministrazione.md) | Sicurezza |
| B13 | `admin_dashboard`: "Last Workout Added" mostra il nome più frequente; "Last Backup" fittizio | [08](08-amministrazione.md) | Cosmetico |

## Codice morto / legacy (non da migrare)

- Template `history.html`, `exercise_info.html`, `dialog_exercise.html`, `add_exercise.html`, `edit_exercise.html`: fanno riferimento a rotte inesistenti (`workout_history`, `exercise_info`, `add_exercise` con campi repetitions/weight/equipment/score/note). Residui di un modello precedente "esercizio per workout" abbandonato.
- `rm_calculator.html`: **calcolatore 1RM** incluso solo da `exercise_info.html` (morto). Formula Brzycki `1RM = peso / (1.0278 − 0.0278 × reps)`, tabella 1RM…15RM con percentuali `[1, .94, .9133, .8867, .8667, .8467, .82, .80, .78, .7667, .7467, .7267, .68]` e tabella 95%…35% a passi di 5. **Candidato al recupero** in Flutter come utility nella pagina massimali.
- `utils.allowed_file`, `similarità_jaccard`, `get_exercise_link` (riferiscono variabili inesistenti), `extract_works_with_validation` (chiama funzione inesistente).
- `User.check_password`, `User.has_super_access`, `User.get_statistics`, `WorkoutPerformance.get_user/get_workout` (usati solo nei template).
- `bootstrap_superuser_from_env` mai invocata.
- Dipendenze non usate: `openai`, `pydantic`, `requests`, `tqdm`, `email-validator` (usato solo dal validatore `Email()`).
- `UserStatistic.reps`, `User.total_workouts_added`: campi scritti ma mai mostrati.
- `logo_christmas.svg`, `static/styles.css` (non incluso).

## Decisioni da prendere in revisione

1. **Multi-tenant?** Oggi un solo box. Se l'app Flutter deve servire più palestre serve il concetto di "box/team" con coach e atleti per box.
2. **Visibilità score**: mantenere la leaderboard pubblica tra atleti o rendere privati gli score?
3. **Score strutturato** vs testo libero (tempo, round+reps, carico, Rx/Scaled).
4. **Offset sul pace** (`+10s`): completare la feature (B1) o rimuoverla.
5. **Unità sul record massimale**: salvare `unit` nel massimale per non dipendere dal catalogo al momento della lettura.
6. **n-RM**: supportare 3RM/5RM oltre all'1RM?
7. **Import settimanale**: mantenere il formato testuale (comodo da WhatsApp/Notes) o passare a un editor strutturato in app? Consiglio: entrambi, con anteprima prima del salvataggio.
8. **Abilitazione atleti**: mantenere l'approvazione manuale del coach (sì, è un requisito chiave) ma bloccarla anche a livello API, non solo in dashboard.
9. **Recupero password** self-service (email) al posto del reset a costante.
10. **Notifiche push** (nuovo workout pubblicato, atleta abilitato): non esistono oggi, ma sono la naturale evoluzione nativa.
11. **Offline**: cache dei workout della settimana e dei massimali per usare timer e percentuali senza rete.
12. **Ruolo coach**: aggiungere promozione/declassamento da UI admin.
13. **Timer in background**: notifiche locali/suoni con app in background o schermo bloccato (oggi il web richiede schermo acceso).
14. **Lingua**: uniformare tutto in italiano (oggi mix IT/EN).

Decisioni già prese nella revisione (settembre 2026): tre ruoli (atleta/coach/superuser),
invito via email come canale principale, autenticazione a token, recupero password via email,
score strutturato, editor strutturato dei workout con import da testo in anteprima, unità e
tipo di test sul massimale, lingua italiana, tono professionale. Nuove aree:
[12-monitoraggio-cardio.md](12-monitoraggio-cardio.md), [13-analisi-dati.md](13-analisi-dati.md),
[14-dashboard-web.md](14-dashboard-web.md).

Aggiunte il 18 settembre 2026 dopo l'analisi di un allenamento monostrutturale reale: blocchi
ripetuti annidati (RF-04-D2b), zona cardiaca come intensità, test multipli per esercizio con
distanza (RF-05-D2b), quantità in minuti e ritmo (RF-04-D2).

Restano aperte: multi-tenant (1), visibilità score (2), n-RM oltre 3RM/5RM (6), offline (11),
timer in background (13), scelta Flutter Web vs frontend separato per la dashboard (doc 14).

## Pacchetti Flutter previsti per le nuove aree

- BLE fascia cardiaca: `flutter_blue_plus` (o `flutter_reactive_ble`).
- HealthKit / Health Connect: `health`.
- Notifiche push: `firebase_messaging`; notifiche locali per il timer: `flutter_local_notifications`.
- Storage sicuro token: `flutter_secure_storage`.
- Deep link (inviti, reset password): `app_links` con Universal Links iOS e App Links Android.
- Grafici: `fl_chart`.
- Web: stesso progetto con target web, layout adattivo.

## Priorità suggerita per l'MVP Flutter

1. Auth (login, registrazione, abilitazione) + profilo.
2. Dashboard giorno/settimana con workout e percentuali calcolate.
3. Massimali: inserimento con unità/formati, lista, storico con grafico.
4. Pagina workout: score personale, lista score, timer completo con salvataggio.
5. Coach: creazione/modifica/elimina/ordina workout, import settimanale con anteprima, catalogo esercizi.
6. Coach: gestione utenti, log, cancellazione per giorno, export/import.

## Dati da migrare

Tabelle: user, workout, range, performance, workout_performance, user_statistic, exercise_catalog, log.
Gli hash password sono Werkzeug (`pbkdf2:sha256` o `scrypt`): il nuovo backend deve saperli verificare oppure forzare un reset password al primo accesso.
