# 01 – Panoramica e ruoli

## Scopo

L'applicazione è una piattaforma di gestione dell'allenamento per box di CrossFit / functional
training, sviluppata in **Flutter** e distribuita su **Android** e **iOS**.

Il coach programma gli allenamenti; gli atleti li consultano dal proprio dispositivo, vedono i
carichi personalizzati calcolati sui propri massimali, eseguono il workout con il timer
integrato e registrano il risultato. Un superuser supervisiona l'intero sistema.

Non è un'app multi-palestra: esiste un'unica programmazione condivisa da tutti gli utenti.

> Nota: la modalità di inserimento dei workout (oggi basata su incolla di testo settimanale,
> vedi [04-workout.md](04-workout.md)) verrà ridefinita in una fase successiva. Questo documento
> descrive solo *chi* può inserirli, non *come*.

## Ruoli

Il sistema prevede tre ruoli, ordinati per livello di privilegio crescente. Ogni ruolo include
tutte le funzionalità del ruolo inferiore.

| Ruolo | Descrizione | Funzionalità |
|-------|-------------|--------------|
| **Atleta** | Utente finale, iscritto al box | Consultare gli allenamenti (se abilitato), registrare e modificare i propri score, gestire i propri massimali (RM) e consultarne lo storico, usare il timer, modificare il proprio profilo |
| **Coach** | Responsabile della programmazione | Tutto quello dell'atleta, più: inserire, modificare, eliminare e ordinare gli allenamenti; gestire il catalogo esercizi; invitare atleti via email; abilitare o disabilitare gli atleti; consultare gli score di tutti gli atleti |
| **superuser** | Amministratore del sistema | Visibilità completa su tutti i dati e piena operatività sia come coach sia come atleta, più: gestione di tutti gli account (invito di atleti e coach, modifica ruolo, disabilitazione, eliminazione, reset password), log attività, export/import dei dati |

Oltre ai tre ruoli esiste lo stato di **visitatore** (utente non autenticato), che può solo
registrarsi o effettuare l'accesso.

### Stato di abilitazione

Ogni account ha un flag di abilitazione, indipendente dal ruolo.

- Un atleta che entra tramite **invito** del coach è abilitato dal primo accesso.
- Un atleta che si registra **autonomamente** è non abilitato: può accedere ma non vede gli
  allenamenti finché un coach o un superuser non lo abilita.
- Un atleta non abilitato può comunque accedere al profilo, ai propri massimali e ai propri
  score storici.
- Coach e superuser sono abilitati alla creazione.

## Requisiti funzionali

RF-01-01 – Il sistema distingue tre ruoli: atleta, coach, superuser. Ogni ruolo eredita
integralmente i permessi del ruolo inferiore.

RF-01-02 – Il canale principale di ingresso è l'**invito via email** inviato da un coach o da un
superuser: l'atleta che accetta l'invito è abilitato dal primo accesso. La registrazione
autonoma resta disponibile come canale secondario e produce un atleta non abilitato.
L'abilitazione può essere concessa o revocata in qualsiasi momento da un coach o da un superuser.

RF-01-03 – Un account coach può essere creato solo da un superuser, oppure promuovendo un
atleta esistente (vedi [03-autenticazione-e-profilo.md](03-autenticazione-e-profilo.md)).
Un account superuser può essere creato solo da un altro superuser o in fase di provisioning
iniziale del sistema. Non esiste una registrazione pubblica per coach o superuser.

RF-01-04 – Gli allenamenti sono **globali**: ogni utente abilitato vede la programmazione del
giorno, indipendentemente da chi l'ha inserita.

RF-01-05 – Solo coach e superuser possono inserire, modificare o eliminare allenamenti.

RF-01-06 – Massimali e score sono **personali**: ogni atleta vede e modifica solo i propri.
Coach e superuser vedono gli score di tutti gli atleti su ogni allenamento e possono
correggerli o eliminarli.

RF-01-07 – Il controllo dei permessi è applicato **lato server** su ogni endpoint, non solo
nascondendo elementi dell'interfaccia. Un atleta non abilitato non può recuperare gli
allenamenti tramite API.

RF-01-08 – Il superuser può operare sull'applicazione con le stesse viste di un coach o di un
atleta, senza necessità di account separati.

RF-01-09 – Il superuser **vede tutto**: ogni workout (pubblico, dedicato o personale di
qualsiasi atleta), ogni score, massimale, sessione cardio, messaggio, invito e ogni riga del
log attività. Nessun dato è nascosto al superuser.

RF-01-10 – **Ogni azione rilevante è tracciata** in un log attività consultabile dal
superuser (e in parte dal coach), con chi, cosa, quando e su quale oggetto
(vedi [08-amministrazione.md](08-amministrazione.md), sezione Log attività).

## Flusso tipico

1. Il coach invita l'atleta via email; l'atleta installa l'app, accetta l'invito e completa
   il proprio profilo.
2. Il coach inserisce la programmazione della settimana (modalità da definire).
3. L'atleta apre l'app, vede la data odierna e gli allenamenti del giorno.
4. Per ogni esercizio con carico in percentuale, l'atleta vede il peso calcolato sul proprio
   massimale. Se il massimale non è registrato, viene invitato a inserirlo.
5. L'atleta apre il dettaglio dell'allenamento, avvia il timer oppure inserisce manualmente
   il risultato.
6. Al termine del timer il risultato viene proposto precompilato e salvato.
7. Nella sezione risultati l'atleta vede la classifica degli score di tutti gli atleti su quel
   allenamento.
8. Il coach consulta i risultati per monitorare la progressione degli atleti.

## Lingua e tono

L'interfaccia è interamente in **italiano**, con terminologia tecnica del settore in inglese
dove è lo standard (WOD, AMRAP, EMOM, RM, Back Squat, ecc.).

Il prodotto è **serio nella sostanza e simpatico nella personalità**. I due registri hanno
spazi distinti:

- **Testi di sistema** (errori, conferme, validazioni, stati vuoti, schermate di attesa,
  email, notifiche): chiari, neutri, orientati all'azione, senza volgarità. Es. "Massimale di
  Back Squat non registrato. Inseriscilo per vedere i carichi calcolati."
- **Testi di personalità** (frasi motivazionali a fondo pagina, frasi da rest day, messaggio
  di fine timer, complimenti per un PR): mantengono lo spirito irriverente del box originale,
  con lo slang e le frasi storiche che gli atleti riconoscono. Sono **una lista curata,
  modificabile dal coach** dalle impostazioni, mai cablate nel codice, e non contengono
  insulti rivolti all'utente. Il coach può disattivarle.

Regola pratica: la simpatia sta dove l'utente si aspetta un incoraggiamento; dove l'utente
sta cercando di capire cosa fare o cosa è andato storto, il testo è professionale.

Vedi [10-ui-navigazione.md](10-ui-navigazione.md) per identità visiva, testi e frasi.
