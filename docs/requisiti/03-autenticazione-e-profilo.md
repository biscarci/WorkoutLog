# 03 – Autenticazione, registrazione e profilo

Requisiti per l'autenticazione dell'app Flutter contro il nuovo backend. Il meccanismo è a
**token** (access token JWT a breve durata + refresh token persistito, vedi entità
`RefreshToken` in [02-modello-dati.md](02-modello-dati.md)). Non esistono sessioni a cookie.

Tutti i messaggi mostrati all'utente sono in italiano, con tono neutro e informativo.

## Registrazione autonoma (canale secondario)

Disponibile per chi non ha ricevuto un invito. Produce un atleta **non abilitato**.

RF-03-01 – Campi obbligatori: nome (2–100), cognome (2–100), username (3–50, solo lettere,
numeri, punto, trattino e underscore), email (formato validato), password, conferma password.

RF-03-02 – Requisiti password: minimo 8 caratteri, almeno una lettera e un numero. La
conferma deve coincidere. Il requisito è indicato nel form prima dell'invio.

RF-03-03 – Username ed email sono confrontati case-insensitive. Se già in uso:
"Username già in uso." / "Indirizzo email già registrato."

RF-03-04 – L'account creato ha `role = athlete`, `is_enabled = false`. Al termine l'utente vede
"Registrazione completata. Il tuo account sarà attivato dal coach." e viene autenticato
automaticamente (token emessi), senza dover rifare il login.

RF-03-05 – La registrazione autonoma crea **solo atleti**. Non esiste una registrazione
pubblica per coach o superuser. Il coach riceve una notifica del nuovo atleta da attivare
(vedi [08-amministrazione.md](08-amministrazione.md)).

RF-03-06 – Evento `user_registered` nel log attività.

## Invito via email

È il canale principale di ingresso degli atleti (RF-01-02).

RF-03-07 – Un coach o un superuser invita un nuovo utente indicando l'email e, facoltativamente,
nome e cognome. Un coach può invitare solo atleti; un superuser anche coach.

RF-03-08 – Non è possibile invitare un'email già associata a un account o con un invito
pendente. Messaggi: "Esiste già un account con questa email." / "Invito già inviato a questo
indirizzo."

RF-03-09 – Il sistema invia un'email con oggetto "Sei stato invitato su <nome app>" contenente
il nome del box, chi ha inviato l'invito e un pulsante con link monouso valido **7 giorni**.
Il link apre l'app se installata (deep link universale), altrimenti una pagina web del backend
con i link agli store che conserva il token e lo riapre dopo l'installazione. Evento
`invitation_sent`.

RF-03-10 – Aprendo il link, l'app mostra la schermata di accettazione con email precompilata e
non modificabile, nome e cognome precompilati se indicati, e chiede username, password e
conferma (regole RF-03-01 e RF-03-02).

RF-03-11 – Alla conferma viene creato l'account con il ruolo dell'invito e `is_enabled = true`.
L'invito passa a "accettato" e l'utente è autenticato immediatamente. Evento
`invitation_accepted`.

RF-03-12 – Un invito scaduto, revocato o già accettato mostra "Questo invito non è più valido.
Chiedi al tuo coach di inviartene uno nuovo."

RF-03-13 – Chi ha inviato l'invito, e qualsiasi superuser, vede l'elenco degli inviti con stato
(pendente, accettato, scaduto, revocato) e può **reinviare** l'email (nuovo token, nuova
scadenza) o **revocare** l'invito. Eventi `invitation_resent`, `invitation_revoked`.

RF-03-14 – Se l'utente invitato apre la registrazione autonoma con la stessa email, il sistema
lo indirizza al flusso di accettazione dell'invito.

## Creazione coach e superuser

RF-03-15 – Un account coach è creato esclusivamente da un superuser tramite invito con ruolo
`coach` (RF-03-07). L'account nasce con `role = coach`, `is_enabled = true`.

RF-03-16 – Un superuser può promuovere un atleta esistente a coach, o un coach a superuser,
modificandone il ruolo. Può anche retrocedere un ruolo. Non può modificare il proprio ruolo.

RF-03-17 – Il primo superuser è creato in fase di provisioning del backend (comando di
seed o variabili d'ambiente al primo avvio), mai tramite l'app.

## Login

RF-03-18 – Campi: identificativo (username **o** email, riconosciuto automaticamente) e
password.

RF-03-19 – Login riuscito: il server restituisce access token (durata 15 minuti), refresh
token (durata 30 giorni, rotazione a ogni uso) e il profilo dell'utente (id, nome, cognome,
username, email, ruolo, stato abilitazione). Evento `login_ok`.

RF-03-20 – Login fallito: messaggio unico "Credenziali non valide." senza distinguere tra
utente inesistente e password errata. Evento `login_failed` con lo username tentato.

RF-03-21 – Rate limiting: massimo 5 tentativi falliti per identificativo in 15 minuti; oltre,
risposta 429 e messaggio "Troppi tentativi. Riprova tra qualche minuto."

RF-03-22 – Un atleta **non abilitato può fare login**. L'app mostra lo stato "In attesa di
attivazione" e limita le funzionalità come descritto in RF-01-02. Il server rifiuta comunque
le richieste sugli allenamenti (RF-01-07).

RF-03-23 – L'app conserva i token nello storage sicuro del dispositivo (Keychain su iOS,
EncryptedSharedPreferences/Keystore su Android). All'avvio, se esiste un refresh token
valido, l'utente entra senza reinserire le credenziali.

## Refresh e scadenza

RF-03-24 – Quando l'access token scade, l'app ottiene un nuovo access token tramite il refresh
token, in modo trasparente per l'utente. Il refresh token usato viene revocato e sostituito.

RF-03-25 – Se il refresh token è scaduto, revocato o non valido, l'app cancella lo stato
locale e riporta l'utente alla schermata di login con il messaggio "Sessione scaduta.
Accedi di nuovo."

RF-03-26 – La disabilitazione, il cambio ruolo o l'eliminazione dell'account da parte di un
amministratore hanno effetto al successivo refresh (entro 15 minuti) o alla richiesta
successiva se il server verifica lo stato dell'utente per ogni chiamata.

## Logout

RF-03-27 – Il logout revoca il refresh token corrente sul server e cancella i token locali.
Evento `logout`.

RF-03-28 – Dal profilo l'utente può vedere i dispositivi con sessione attiva (nome dispositivo
e data ultimo uso) e revocarli singolarmente o tutti insieme.

## Recupero password

RF-03-29 – Dalla schermata di login, "Password dimenticata" chiede l'email. La risposta è
sempre "Se l'indirizzo è registrato riceverai un'email con le istruzioni.", anche se l'email
non esiste.

RF-03-30 – L'email contiene un link con token monouso valido 30 minuti. Il link apre l'app
(deep link) o, in fallback, una pagina web minimale del backend, dove l'utente imposta la
nuova password secondo RF-03-02.

RF-03-31 – Al completamento tutti i refresh token dell'utente vengono revocati. Evento
`password_reset`.

## Profilo

RF-03-32 – L'utente può modificare nome, cognome, username ed email. Le stesse regole di
validazione e unicità della registrazione. Messaggio "Profilo aggiornato."

RF-03-33 – Il cambio password è una funzione separata: richiede la password attuale, la nuova
e la conferma. Al completamento vengono revocati tutti gli altri refresh token (restano
autenticati solo il dispositivo corrente). Evento `password_changed`.

RF-03-34 – Il ruolo e lo stato di abilitazione sono visibili nel profilo ma non modificabili
dall'utente.

## Cancellazione account

RF-03-35 – L'utente può eliminare il proprio account dall'app (requisito degli store).
L'operazione richiede la password e una conferma esplicita. Gli effetti sono quelli di
RF-02-02. Evento `account_deleted`.

RF-03-36 – Un superuser non può eliminare il proprio account se è l'unico superuser attivo.

## Tracciamento attività

RF-03-37 – A ogni richiesta autenticata viene aggiornato `last_activity_at`.

RF-03-38 – Gli eventi di autenticazione e invito (`user_registered`, `invitation_sent`,
`invitation_accepted`, `invitation_resent`, `invitation_revoked`, `login_ok`, `login_failed`,
`logout`, `password_reset`, `password_changed`, `account_deleted`) generano una riga di
ActivityLog. Elenco completo in [08-amministrazione.md](08-amministrazione.md).

## Email transazionali

- Invio tramite provider esterno (es. Resend, Postmark o Amazon SES) con dominio verificato
  (SPF, DKIM, DMARC) e mittente dedicato, es. `noreply@<dominio del box>`.
- Template in italiano, con logo e nome del box, coerenti con lo stile dell'app.
- Email previste in questo documento: invito, recupero password. Altre email e notifiche
  push sono descritte in [08-amministrazione.md](08-amministrazione.md).
- L'invio è asincrono (coda) e ritentato in caso di errore; l'esito è registrato nel log.

## Sicurezza

- Password con hash Argon2id (o bcrypt), mai loggate né restituite.
- Tutte le chiamate su HTTPS; il backend rifiuta HTTP.
- Access token JWT firmato, contenente `user_id`, `role`, scadenza. Il ruolo nel token è
  usato solo come ottimizzazione: le operazioni sensibili rileggono il ruolo da DB.
- Refresh token generato casualmente (almeno 32 byte), salvato solo come hash.
- Rate limiting su login, registrazione, recupero password e invio inviti.
- Token di invito e di reset generati casualmente (almeno 32 byte), salvati solo come hash, monouso.
- Ogni endpoint verifica ruolo e stato di abilitazione lato server (RF-01-07).

## Migrazione dal sistema legacy

- Gli utenti esistenti con `is_superuser = true` diventano superuser; gli altri atleti.
  I coach vanno assegnati a mano dopo la migrazione.
- Gli hash Werkzeug non sono convertibili: al primo login il backend verifica con
  l'algoritmo legacy e, se corretto, ri-hasha con Argon2id. In alternativa, si invia a tutti
  un'email di reset password.
- La registrazione coach con codice segreto (`ADMIN_REG_CODE`) è **dismessa**.
