# 09 – Rotte attuali e proposta API per Flutter

## Rotte attuali (Flask)

Legenda accesso: **P** = pubblico, **L** = login, **O** = proprietario o coach, **C** = coach (superuser). ★ = protetta solo da login ma pensata per il coach.

| Metodo | Rotta | Accesso | Funzione |
|--------|-------|---------|----------|
| GET/POST | `/register` | P | Registrazione atleta |
| GET/POST | `/register/admin` | P | Registrazione coach con codice |
| GET/POST | `/login` | P | Login |
| GET | `/logout` | L | Logout |
| GET/POST | `/profile` | L | Profilo |
| GET | `/menu` | L | Menu |
| GET | `/`, `/dashboard` | L | Dashboard giorno (query year/month/day) |
| GET | `/dashboard/date/<day>/<month>/<year>` | L | Dashboard giorno |
| GET/POST | `/workout/add` | L ★ | Nuovo workout |
| GET/POST | `/workout/week/add` | L ★ | Import settimanale |
| GET/POST | `/workout/edit/<id>` | O | Modifica workout |
| POST | `/workout/delete/<id>` | O | Elimina workout |
| GET | `/workouts/order` | C | Ordina workout del giorno |
| POST | `/workouts/order/move/<id>` | C | Sposta su/giù (`direction`) |
| GET/POST | `/performance/add/<workout_id>` | L | Dettaglio workout + score |
| POST | `/performance/quick-add/<workout_id>` | L | Score dal timer |
| GET/POST | `/performance/edit/<id>` | O | Modifica score |
| POST | `/performance/delete/<id>` | O (+ owner workout) | Elimina score |
| GET | `/workout/<id>/timer-setup` | L | Setup timer |
| GET | `/workout/<id>/timer` | L | Timer |
| GET/POST | `/stats` | L | Massimali |
| GET | `/stats/history/<exercise>` | L | Storico massimale |
| GET | `/api/stats/history/<exercise>` | L | JSON punti storico |
| GET/POST | `/stats/edit/<id>` | O | Modifica massimale |
| POST | `/stats/delete` | L | Elimina massimali (`selected_ids[]`) |
| GET/POST | `/admin/exercises` | C | Catalogo esercizi |
| GET/POST | `/admin/exercises/<id>/edit` | C | Modifica esercizio |
| POST | `/admin/exercises/<id>/toggle` | C | Attiva/disattiva |
| POST | `/admin/exercises/<id>/delete` | C | Elimina/disattiva |
| POST | `/admin/exercises/import` | C | Importa orfani |
| GET | `/admin/dashboard` | C | Dashboard admin (query `log_date`) |
| GET | `/admin/users` | C | Lista utenti |
| POST | `/admin/manage_user/<id>` | C | Toggle abilitato |
| POST | `/admin/delete_user/<id>` | C | Elimina utente |
| POST | `/admin/reset_password/<id>` | C | Reset password |
| GET/POST | `/admin/workouts/delete-by-day` | C | Cancellazione per giorno |
| GET | `/export/csv` | C | Export CSV |
| POST | `/import/csv` | C | Import CSV |
| – | 404 / 500 | – | Pagine errore con link a dashboard (500 fa rollback) |

L'unico endpoint JSON esistente è `/api/stats/history/<exercise>`. Tutto il resto è HTML con form e redirect + flash message.

## Proposta API REST (bozza per il backend del client Flutter)

Convenzioni: JSON, autenticazione **Bearer token** (JWT o opaque token con refresh), date `YYYY-MM-DD`, timestamp ISO 8601 UTC, errori `{ "error": "codice", "message": "testo" }` con HTTP status (400 validazione, 401 non autenticato, 403 non autorizzato, 404 non trovato, 409 conflitto). I messaggi flash attuali diventano `message` o vengono generati dal client.

### Auth
| Metodo | Endpoint | Note |
|--------|----------|------|
| POST | `/auth/register` | body: name, surname, username, email, password → 201 (utente non abilitato) |
| POST | `/auth/register-coach` | + `admin_code` → 201 (coach abilitato) |
| POST | `/auth/login` | username, password → `{access_token, refresh_token, user}` |
| POST | `/auth/refresh` | |
| POST | `/auth/logout` | invalida refresh token |
| GET | `/me` | profilo + `is_superuser`, `is_enabled` |
| PATCH | `/me` | name, surname, username, email, password |

### Workout
| Metodo | Endpoint | Note |
|--------|----------|------|
| GET | `/workouts?date=YYYY-MM-DD` | lista del giorno ordinata per display_order, con `ranges` raggruppati e **già calcolati** per l'utente (vedi payload sotto). Se `is_enabled=false` → 403 con messaggio dedicato o lista vuota + flag |
| GET | `/workouts?from=&to=` | opzionale: settimana intera per il calendario |
| GET | `/workouts/{id}` | dettaglio con ranges calcolati |
| POST | `/workouts` | coach: date, name, description, `range_groups: [{exercise, items:[{value, kind}]}]` |
| PUT | `/workouts/{id}` | coach |
| DELETE | `/workouts/{id}` | coach |
| POST | `/workouts/week-import` | coach: `{text}` → `{created: N, workouts:[…]}`; stesso parser testuale (RF-04-12) o, meglio, JSON strutturato + parser lato client |
| PUT | `/workouts/order` | coach: `{date, ordered_ids:[…]}` (sostituisce up/down) |
| DELETE | `/workouts/by-week` | coach: `{week_start, weekdays:[0..6]}` |

Payload workout (esempio):
```json
{
  "id": 42,
  "date": "2026-09-14",
  "display_order": 1,
  "name": "Ev. 1.30' x 6 Sets",
  "description": "Set (1-2) 2 Squat Snatch 70%\nSet (3-4) …",
  "range_groups": [
    {
      "exercise": "Squat Snatch",
      "unit": "kg",
      "unit_label": "Kg",
      "user_max": 80.0,
      "user_max_label": "80.0",
      "items": [
        {"value": 70, "kind": "pct", "computed": 56.0, "computed_label": "56.0"},
        {"value": 75, "kind": "pct", "computed": 60.0, "computed_label": "60.0"}
      ]
    },
    {"exercise": "Row", "unit": "pace", "unit_label": "/500m", "user_max": null, "items": [ … ]}
  ],
  "performances_count": 3
}
```

### Performance
| Metodo | Endpoint | Note |
|--------|----------|------|
| GET | `/workouts/{id}/performances` | tutti gli score del workout (username, date, description, `can_edit`) |
| POST | `/workouts/{id}/performances` | date, description |
| PATCH | `/performances/{id}` | owner/coach |
| DELETE | `/performances/{id}` | owner/coach/owner workout |

### Massimali
| Metodo | Endpoint | Note |
|--------|----------|------|
| GET | `/exercises` | catalogo **attivo** (name, unit, ref_distance, pct_mode, unit_label, input_hint) – per la tendina |
| GET | `/stats` | ultimo record per esercizio, con `value_label`, `unit_label` |
| POST | `/stats` | date, exercise (o exercise_id), value (stringa: `102.5`, `8:30`, `1:45`; la validazione RF-05-13 può stare sia lato client sia server) |
| PATCH | `/stats/{id}` | |
| DELETE | `/stats` | `{ids:[…]}` |
| GET | `/stats/history?exercise=` | punti ordinati per data + best/first/latest/delta |

### Admin (coach)
| Metodo | Endpoint | Note |
|--------|----------|------|
| GET | `/admin/summary` | contatori dashboard |
| GET | `/admin/logs?date=` | log attività |
| GET | `/admin/users` | |
| PATCH | `/admin/users/{id}` | `is_enabled`, (opz.) `is_superuser` |
| POST | `/admin/users/{id}/reset-password` | ritorna password temporanea generata |
| DELETE | `/admin/users/{id}` | |
| GET/POST | `/admin/exercises` | catalogo completo (anche inattivi) + conteggi + orfani |
| PATCH | `/admin/exercises/{id}` | name, unit, ref_distance, pct_mode, is_active |
| DELETE | `/admin/exercises/{id}` | 200 con `{deleted:false, deactivated:true}` se in uso |
| POST | `/admin/exercises/import-orphans` | |
| GET | `/admin/export` | CSV/JSON |
| POST | `/admin/import` | multipart |

## Logica che deve restare sul server

- Calcolo delle percentuali (RF-05-21) e formattazione: il client può replicarli, ma per coerenza il server ritorna i valori già calcolati e le etichette.
- Normalizzazione dei nomi esercizio e riallineamento al rename (RF-05-06).
- Regole di visibilità/permessi (owner vs coach).
- Parser dell'import settimanale (o in alternativa validazione del JSON strutturato prodotto dal client).

## Logica che può stare sul client Flutter

- Timer completo (RF-07), audio, wake lock, vibrazione.
- Calcolatore RM (legacy, vedi [11](11-note-migrazione-flutter.md)) se si vuole ripristinarlo.
- Frasi motivazionali / rest day (lista statica, [10](10-ui-navigazione.md)).
- Hint dinamico dell'unità nel form massimali.
