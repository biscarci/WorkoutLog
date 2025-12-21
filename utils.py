import base64, os
import requests,json
from datetime import datetime, timedelta
import random
import re


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def random_motivational_phrase():
    common_phrases = [
        "SÌ VOLA",
        "LE COSE VANNO BENE ",
        "FAJ PAUR 🤌🏽",
        "PAZZESCO ! ",
        "TUTTO NELLA SERENITÀ",
        "NON SENTO NIENTE",
        "SIUUP",
        "STA SUCCENNDO"
    ]
    other_phrases = [
        "RESPIRA DOPO",
        "MUOVITI",
        "NON MOLLARE",
        "SOFFRI MEGLIO",
        "ANCORA UNO",
        "ZITTO E SPINGI",
        "STRINGI I DENTI",
        "NON FARE IL DEBOLE",
        "QUI SI SPINGE",
        "DAI. ORA",
        "NON SEI FINITO",
        "PESO SERIO",
        "LAVORA",
        "SPACCA",
        "FORZA BRUTA",
        "ZERO SCUSE",
        "OGGI SI SOFFRE. PUNTO",
        "SE SEI STANCO, FUNZIONA",
        "NON È IL MOMENTO DI PENSARE",
        "IL CORPO MENTE",
        "SPINGI ANCHE SE FA SCHIFO",
        "NON SEI SPECIALE",
        "FINISCI O COLLASSA",
        "NESSUNO TI SALVA",
        "IL WOD TI ODIA",
        "SE RESPIRI, LAVORI",
        "NON RALLENTARE",
        "SPINGI E BASTA",
        "OGGI SI ROMPE QUALCOSA",
        "FINO IN FONDO",
        "IL DOLORE È TEMPORANEO",
        "IL DOLORE PASSA, LA GLORIA RESTA",
        "NON È FINITA FINCHÉ NON SMETTI",
        "IL LIMITE È NELLA TUA TESTA",
        "NON C'È CRESCITA SENZA DOLORE",
        "OGGI SI ENTRA INTERI, SI ESCE ROTTI",
        "SE NON FA PAURA, NON È ABBASTANZA PESANTE",
        "QUI NON SI VIENE PER STARE BENE",
        "IL RISCALDAMENTO È GIÀ UNA MINACCIA",
        "SE STAI COMODO, STAI SBAGLIANDO",
        "IL CORPO VUOLE FERMARSI. FOTTITENE",
        "LA GHISA NON HA PIETÀ. TU NEMMENO",
        "OGNI WOD È UNA SCELTA DI VITA SBAGLIATA",
        "QUI SI SOFFRE TUTTI UGUALI",
        "SE NON SPUTI UN POLMONE, NON È FINITO",
        "OGGI SI PAGA IL CONTO DEI GIORNI FACILI",
        "IL DOLORE È IL COACH PIÙ ONESTO",
        "NON CERCARE SCUSE, CERCA OSSIGENO",
        "QUI SI CRESCE A FORZA",
        "SE TREMI STAI FUNZIONANDO",
        "LA FATICA NON UCCIDE. IL DIVANO SÌ",
        "OGNI REP È UNA TRATTATIVA COL DIAVOLO",
        "NON È STANCHEZZA, È DEBOLEZZA CHE ESCE",
        "IL TIMER È IL TUO NEMICO",
        "CHI PARLA TROPPO NON SPINGE ABBASTANZA",
        "QUI NON SI ALLENA L'AUTOSTIMA",
        "SE SORRIDI, MANCA PESO",
        "IL CORPO URLA. LA TESTA DECIDE",
        "ANCORA UNO ANCHE SE NON VUOI",
        "IL WOD NON SI DISCUTE, SI SUBISCE",
        "QUI NON C'È CONTROLLO: C'È ADATTAMENTO",
        "IL BOX TI PRENDE A SCHIAFFI E TI MIGLIORA",
        "SE SEI VIVO, PUOI FARE UN ALTRO REP",
        "ALLENARSI STANCHI È IL PUNTO",
        "QUI NON VINCI, SOPRAVVIVI",
        "IL FIATO CORTO È TEMPORANEO",
        "LA FORZA ARRIVA QUANDO SMETTI DI CHIEDERE PIETÀ",
        "OGNI ALLENAMENTO È UNA GUERRA CIVILE",
        "SE PENSI DI AVER FINITO, SEI ALL'INIZIO",
        "IL FERRO PESA UGUALE PER TUTTI",
        "OGGI NON SI MIGLIORA L'UMORE: SI MIGLIORA IL FISICO",
        "CHI ENTRA CONVINTO ESCE UMILE",
        "IL BOX NON CONSOLA, TRASFORMA",
        "QUI SI SOFFRE PER SCELTA",
        "IL DOLORE È IL PREZZO D'INGRESSO",
        "IL WOD TI ODIA. RICAMBIA",
        "RESPIRA QUANDO PUOI. SPINGI QUANDO DEVI",
        "OGNI STOP È UNA SCONFITTA PERSONALE",
        "QUI NON ESISTE ABBASTANZA FORTE",
        "IL CORPO MOLLA DOPO LA TESTA. SEMPRE",
        "SE NON TI MANCA L'ARIA, MANCA IMPEGNO",
        "LA GHISA NON FA SCONTI",
        "QUI SI DIVENTA DURI O SI SPARISCE",
        "FINISCI. POI COLLASSA"
    ]

    index = random.randint(0, len(other_phrases)-1)
    common_phrases_index = random.randint(0, len(common_phrases)-1)

    phrase = common_phrases[common_phrases_index] if random.randint(0, 1) else other_phrases[index]

    return phrase

 
def random_rest_message():
    array = [
        "REST IND' O' LIET",
        "OGGI WORKOUT? NO. REST",
        "REST DAY: NON FACCIO UN CAZZO PER DIVENTARE PIÙ GROSSO",
        "ALLENAMENTO DI OGGI: DORMIRE COME UN ANIMALE E MANGIARE COME UNA MERDA",
        "OGGI NIENTE PALESTRA, I MUSCOLI STANNO URLANDO BASTA",
        "WORKOUT SALTATO: RECUPERO IGNORANTE, ZERO SENSI DI COLPA",
        "OGGI NON SPINGO PESI, SPINGO IL RECUPERO COME SI DEVE",
        "REST DAY: SE MI ALLENO OGGI, DOMANI FACCIO CAGARE",
        "ALLENAMENTO ANNULLATO: I MUSCOLI HANNO DETTO BASTA",
        "OGGI ZERO WORKOUT. CRESCITA PASSIVA ATTIVATA",
        "RIPOSO STRATEGICO: ALLENARSI STANCHI È DA COGLIONI",
        "WORKOUT OFF. MANGIA, DORMI, STAI ZITTO",
        "OGGI NON SI FA UN CAZZO. DOMANI SI SPACCA TUTTO",
        "REST DAY VIOLENTO: RECUPERO PRIMA DI FARE DANNI SERI",
        "PESI FERMI. BESTIA IN RICARICA",
        "ALLENAMENTO MENTALE: CONVINCERMI CHE RIPOSARE NON È DA DEBOLI",
        "OGGI IL WORKOUT MI GUARDA. IO LO IGNORO",
        "REST DAY: CRESCO ANCHE SENZA FARE UN CAZZO. MIRACOLO",
        "ALLENAMENTO FANTASMA. RECUPERO REALE",
        "OGGI RIPOSO PERCHÉ SONO GROSSO, NON SCEMO",
        "OGGI RIPOSO HARDCORE: DIVANO, CIBO E ZERO RIMORSI",
        "WORKOUT SPENTO. CERVELLO SPENTO. RECUPERO ACCESO",
        "OGGI NON SI VA IN PALESTRA PERCHÉ SIAMO STANCHI SUL SERIO",
        "REST DAY IGNORANTE: I MUSCOLI RINGRAZIANO, IO PURE",
        "ALLENAMENTO RIMANDATO: OGGI VINCONO SONNO E FAME",
        "OGGI NIENTE GHISA, SOLO RECUPERO SELVAGGIO",
        "RIPOSO TOTALE: MODALITÀ BESTIA OFF, MODALITÀ UMANO ON",
        "WORKOUT CANCELLATO PER CAUSE DI FORZA MAGGIORE: IO",
        "OGGI RECUPERO COME SE DOMANI DOVESSI SPACCARE TUTTO",
        "REST DAY SACRO: CHI ALLENA SEMPRE È UN PAZZO"
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
