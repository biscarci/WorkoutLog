import base64, os
import requests,json
from datetime import datetime, timedelta
import random
import re
from typing import List, Dict, Optional


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
        "STA SUCCENNDO",
        "NELLA SIUP LIFE"
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

""" 
Utilities per il parsing del testo degli allenamenti 
week:05/01/2026

day:monday

work 1:
Ev. 1.30’ X 6 Sets 
ex:
Set (1-2) 2 Squat Snatch 70%
Set (3-4) 2 Squat Snatch 75%
Set (5-6) 2 Squat Snatch 80%
ranges:70,75,80@Squat Snatch
"""
def extract_workouts(day: str, text: str) -> List[Dict]:
    """
    Estrae le informazioni sugli allenamenti per un giorno specifico.
    
    Args:
        day: Il giorno da cercare (es. "monday")
        text: Il testo completo da parsare
        
    Returns:
        Lista di dizionari contenenti work, name, exercises e ranges
    """
    result = []
    
    # Trova il blocco del giorno richiesto
    day_pattern = rf"day:\s*{day}\s*([\s\S]*?)(?=\n\s*day:|$)"
    day_match = re.search(day_pattern, text, re.IGNORECASE)
    
    if not day_match:
        return result
    
    day_content = day_match.group(1)
    
    # Estrai tutti i work block
    work_pattern = r"work\s+(\d+):([\s\S]*?)(?=\n\s*work\s+\d+:|$)"
    work_matches = re.findall(work_pattern, day_content, re.IGNORECASE)
    for work_number, work_content in work_matches:
        work_data = _parse_work_block(int(work_number), work_content.strip())
        result.append(work_data)
    
    return result


def _parse_work_block(work_number: int, content: str) -> Dict:
    """
    Parsa il contenuto di un singolo work block.
    
    Args:
        work_number: Il numero del work
        content: Il contenuto completo del work block
        
    Returns:
        Dizionario con work, name, exercises e ranges
    """
    work_data = {
        "work": work_number,
        "name": "",
        "exercises": [],
        "ranges": []
    }
    
    # Se non c'è "ex:", tutto il contenuto è il nome
    if "ex:" not in content:
        work_data["name"] = content
        return work_data
    
    # Separa nome e sezione esercizi
    name_part, exercises_part = content.split("ex:", 1)
    work_data["name"] = name_part.strip()
    
    # Gestisci ranges se presenti
    if "ranges:" in exercises_part:
        # Separa esercizi e ranges e recupera l'esercizio su cui fare i ranges
        # es. (...)ranges:45,80@Muscle Snatch
        exercises_part, ranges_part = exercises_part.split("ranges:", 1)
        ranges_part, exercise_range = ranges_part.split("@", 1)
        work_data["exercise_range"] = exercise_range.strip()
        work_data["ranges"] = _parse_list_items(ranges_part)
    
    # Parsa gli esercizi
    work_data["exercises"] = _parse_list_items(exercises_part)
    
    return work_data


def _parse_list_items(text: str) -> List[str]:
    """
    Estrae elementi da una lista multi-linea o CSV.
    Supporta sia formato con newline che formato CSV.
    
    Args:
        text: Testo contenente gli elementi
        
    Returns:
        Lista di stringhe ripulite
    """
    text = text.strip()
    
    # Se contiene virgole, tratta come CSV
    if ',' in text:
        items = [item.strip() for item in text.split(',') if item.strip()]
    else:
        # Altrimenti tratta come lista multi-linea
        items = [line.strip() for line in text.splitlines() if line.strip()]
    
    return items


# Versione con validazione più robusta
def extract_works_with_validation(day: str, text: str) -> Dict:
    """
    Versione con validazione e gestione errori migliorata.
    
    Returns:
        Dizionario con 'success', 'data' ed eventualmente 'errors'
    """
    errors = []
    
    # Validazione input
    if not text or not text.strip():
        return {"success": False, "errors": ["Testo vuoto"], "data": []}
    
    if not day or not day.strip():
        return {"success": False, "errors": ["Giorno non specificato"], "data": []}
    
    # Verifica presenza del giorno
    if not re.search(rf"day:\s*{day}", text, re.IGNORECASE):
        errors.append(f"Giorno '{day}' non trovato nel testo")
    
    try:
        data = extract_works_with_ex(day, text)
        
        # Validazione risultati
        if not data and not errors:
            errors.append("Nessun work trovato per questo giorno")
        
        return {
            "success": len(errors) == 0,
            "data": data,
            "errors": errors if errors else None
        }
    
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "errors": [f"Errore durante il parsing: {str(e)}"]
        }

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
        workout_blocks = extract_workouts(day_name, raw_text)
        


        for workout in workout_blocks:
            workouts.append({
                "date": workout_date,
                "name": workout.get("name"),
                "description": workout.get("exercises"),
                "ranges": workout.get("ranges", []),
                "exercise_range": workout.get("exercise_range", None),
            })


    return {
        "week_date": week_date,
        "workouts": workouts
    }
