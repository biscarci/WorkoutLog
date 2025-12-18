import base64, os
import requests,json
from datetime import datetime, timedelta
import random
import re


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def random_motivational_phrase():
    array = [
        "Spingi e taci.",
        "Ancora. Non discutere.",
        "Non è abbastanza.",
        "Più peso.",
        "Respira dopo.",
        "Muoviti.",
        "Non mollare.",
        "Soffri meglio.",
        "Ancora uno.",
        "Zitto e spingi.",
        "Stringi i denti.",
        "Non fare il debole.",
        "Qui si spinge.",
        "Dai. Ora.",
        "Non sei finito.",
        "Peso serio.",
        "Lavora.",
        "Spacca.",
        "Forza bruta.",
        "Zero scuse.",
        "Oggi si soffre. Punto.",
        "Se sei stanco, funziona.",
        "Non è il momento di pensare.",
        "Il corpo mente.",
        "Spingi anche se fa schifo.",
        "Qui non c’è pietà.",
        "Ancora uno, stron*o.",
        "Non sei speciale.",
        "Finisci o collassa.",
        "La ghisa comanda.",
        "Nessuno ti salva.",
        "Il WOD ti odia.",
        "Rispondi col peso.",
        "Se respiri, lavori.",
        "Qui si paga.",
        "Non rallentare.",
        "Spingi e basta.",
        "Non cercare conforto.",
        "Oggi si rompe qualcosa.",
        "Fino in fondo.",
        "Il dolore è temporaneo.",
        "Il dolore passa, la gloria resta.",
        "Non è finita finché non smetti.",
        "La fatica è il tuo alleato.",
        "Ogni goccia di sudore conta.",
        "La forza nasce dal disagio.",
        "Il limite è nella tua testa.",
        "Non c’è crescita senza dolore.",
        "Oggi si entra interi, si esce rotti.",
        "Se non fa paura, non è abbastanza pesante.",
        "Qui non si viene per stare bene.",
        "Il riscaldamento è già una minaccia.",
        "Se stai comodo, stai sbagliando.",
        "Il corpo vuole fermarsi. Fottitene.",
        "La ghisa non ha pietà. Tu nemmeno.",
        "Ogni WOD è una scelta di vita sbagliata.",
        "Qui si soffre tutti uguali.",
        "Se non sputi un polmone, non è finito.",
        "Oggi si paga il conto dei giorni facili.",
        "Il dolore è il coach più onesto.",
        "Non cercare scuse, cerca ossigeno.",
        "Qui si cresce a forza.",
        "Se tremi stai funzionando.",
        "La fatica non uccide. Il divano sì.",
        "Ogni rep è una trattativa col diavolo.",
        "Non è stanchezza, è debolezza che esce.",
        "Il timer è il tuo nemico.",
        "Chi parla troppo non spinge abbastanza.",
        "Qui non si allena l’autostima.",
        "Se sorridi, manca peso.",
        "Il corpo urla. La testa decide.",
        "Ancora uno anche se non vuoi.",
        "Il WOD non si discute, si subisce.",
        "Qui non c’è controllo: c’è adattamento.",
        "Il box ti prende a schiaffi e ti migliora.",
        "Se sei vivo, puoi fare un altro rep.",
        "Allenarsi stanchi è il punto.",
        "Qui non vinci, sopravvivi.",
        "Il fiato corto è temporaneo.",
        "La forza arriva quando smetti di chiedere pietà.",
        "Ogni allenamento è una guerra civile.",
        "Se pensi di aver finito, sei all’inizio.",
        "Il ferro pesa uguale per tutti.",
        "Oggi non si migliora l’umore: si migliora il fisico.",
        "Chi entra convinto esce umile.",
        "Il box non consola, trasforma.",
        "Qui si soffre per scelta.",
        "Il dolore è il prezzo d’ingresso.",
        "Il WOD ti odia. Ricambia.",
        "Respira quando puoi. Spingi quando devi.",
        "Ogni stop è una sconfitta personale.",
        "Qui non esiste abbastanza forte.",
        "Il corpo molla dopo la testa. Sempre.",
        "Se non ti manca l’aria, manca impegno.",
        "La ghisa non fa sconti.",
        "Qui si diventa duri o si sparisce.",
        "Finisci. Poi collassa."
    ]

    index = random.randint(1, len(array)-1)
    return array[index]

 
def random_rest_message():
    array = [
        "Oggi workout? No. La bestia si fa i cazzi suoi.",
        "Rest day: non faccio un cazzo per diventare più grosso.",
        "Allenamento di oggi: dormire come un animale e mangiare come una merda.",
        "Oggi niente palestra, i muscoli stanno urlando basta.",
        "Workout saltato: recupero ignorante, zero sensi di colpa.",
        "Oggi non spingo pesi, spingo il recupero come si deve.",
        "Rest day: se mi alleno oggi, domani faccio cagare.",
        "Allenamento annullato: i muscoli hanno detto basta.",
        "Oggi zero workout. Crescita passiva attivata.",
        "Riposo strategico: allenarsi stanchi è da coglioni.",
        "Workout off. Mangia, dormi, stai zitto.",
        "Oggi non si fa un cazzo. Domani si spacca tutto.",
        "Rest day violento: recupero prima di fare danni seri.",
        "Pesi fermi. Bestia in ricarica.",
        "Allenamento mentale: convincermi che riposare non è da deboli.",
        "Oggi il workout mi guarda. Io lo ignoro.",
        "Riposo approvato: meglio fermarsi che fare il pirla.",
        "Rest day: cresco anche senza fare un cazzo. Miracolo.",
        "Allenamento fantasma. Recupero reale.",
        "Oggi riposo perché sono grosso, non scemo.",
        "Oggi riposo hardcore: divano, cibo e zero rimorsi.",
        "Workout spento. Cervello spento. Recupero acceso.",
        "Oggi non si va in palestra perché siamo stanchi sul serio.",
        "Rest day ignorante: i muscoli ringraziano, io pure.",
        "Allenamento rimandato: oggi vincono sonno e fame.",
        "Oggi niente ghisa, solo recupero selvaggio.",
        "Riposo totale: modalità bestia OFF, modalità umano ON.",
        "Workout cancellato per cause di forza maggiore: io.",
        "Oggi recupero come se domani dovessi spaccare tutto.",
        "Rest day sacro: chi allena sempre è un pazzo."
    ]
    index = random.randint(1, len(array)-1)
    return array[index]

def similarità_jaccard(s1, s2):
    set1 = set(s1.lower().split())
    set2 = set(s2.lower().split())
    return float(len(set1 & set2)) / len(set1 | set2)


def get_exercise_link(nome_exercise, soglia=0.2, limit=4):
    abbinamenti = []
    for entry in array_exercise_link:
        esercizio = entry['exercise']
        punteggio = similarità_jaccard(nome_exercise, esercizio)
        if punteggio >= soglia:
            abbinamenti.append((punteggio, entry))

    abbinamenti.sort(reverse=True, key=lambda x: x[0])
    
    return [entry for _, entry in abbinamenti[:limit]]


DAY_ORDER = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

def print_works(result):
    for work in result:
        print(f"\nWORK {work['work']}")
        print("-" * 30)
        print(f"Timing: {work['name']}")

        if work["exercises"]:
            print("Exercises:")
            for ex in work["exercises"]:
                print(f"  - {ex}")
        else:
            print("Exercises: none")

def extract_works_with_ex(day, text):
    result = []

    day_pattern = rf"day:{day}\s*([\s\S]*?)(?=\n\s*day:|$)"
    day_block = re.search(day_pattern, text, re.IGNORECASE)

    if not day_block:
        return result

    work_matches = re.findall(
        r"work\s+(\d+):([\s\S]*?)(?=\n\s*work\s+\d+:|$)",
        day_block.group(1),
        re.IGNORECASE
    )

    for work_num, content in work_matches:
        content = content.strip()

        if "ex:" in content:
            timing_part, ex_part = content.split("ex:", 1)
            timing = timing_part.strip()
            exercises = [
                line.strip()
                for line in ex_part.splitlines()
                if line.strip()
            ]
        else:
            timing = content
            exercises = []

        result.append({
            "work": int(work_num),
            "name": timing,
            "exercises": exercises
        })
        
    return result


def parse_week_text(raw_text):
    week_match = re.search(r"week:(\d{2}/\d{2}/\d{4})", raw_text)
        
    if not week_match:
        raise ValueError("Campo week non valido")

    week_date = datetime.strptime(week_match.group(1), "%d/%m/%Y")

    # --- split per day ---
    day_blocks = re.split(r"\nday:", raw_text)
    day_blocks = day_blocks[1:]  # rimuove header

    workouts = []

    for block in day_blocks:
        lines = block.strip().splitlines()
        day_name = lines[0].strip().lower()

        # estrai description
        description = "\n".join(lines[1:]).strip()

        # calcolo data reale (opzionale ma consigliato)
        day_offset = DAY_ORDER.get(day_name)
        workout_date = week_date + timedelta(days=day_offset) if day_offset is not None else week_date
        workout_blocks = extract_works_with_ex(day_name, raw_text)
        


        for workout in workout_blocks:
            workouts.append({
                "date": workout_date,
                "name": workout.get("name"),
                "description": workout.get("exercises")
            })


    return {
        "week_date": week_date,
        "workouts": workouts
    }
