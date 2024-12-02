import base64, os
import requests,json
from openai import OpenAI
from datetime import datetime, timedelta
import random
""" from fuzzywuzzy import fuzz, process """

OPENAI_APIKEY ='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'  
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

from pydantic import BaseModel

class Exercise(BaseModel):
    name: str
    description: str
    note: str

class Workout(BaseModel):
    name: str
    type: str
    duration: str
    exercises: list[Exercise]
    note: str

    def exercises_list(self):
       return ', '.join(self.exercises)

class WorkoutOfDay(BaseModel):
    date: str
    workouts: list[Workout]



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def get_month_start_end(month_number, year):
    # Construct the start and end dates
    start_date = datetime(year, month_number, 1)
    if month_number == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)  # Last day of December
    else:
        end_date = datetime(year, month_number + 1, 1) - timedelta(days=1)  # Last day of the month
    print(start_date, end_date)
    return start_date, end_date
 
def get_text_from_image_openai(image_path):
    # Getting the base64 string
    img_b64_str = encode_image(image_path)

    client = OpenAI( api_key=OPENAI_APIKEY)
    prompt = "In this image is described one or more workout. Extract from this image:\
              The date, the type of the workout for each workout. \
              For each workout extract the movement name of the exercise, the  description of the workout\
              If some fields are missing use None ad default value"

    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64_str}"}
                    }
                ],
            }
        ],
        response_format=WorkoutOfDay,
    )
    workoutofday = completion.choices[0].message.parsed
    
    for w in workoutofday.workouts:
        print(workoutofday.date)
        print(w.name)
        for ex in w.exercises:
            print(ex.name)
            print(ex.description)
    
    return workoutofday


def get_exercise_suggestion(exercise, history):
    client = OpenAI( api_key=OPENAI_APIKEY)
    
    if history !="":
        content = ("Basandoti sulla seguente cronologia di allenamento:\n\n" + history + 
                    "\n\nConsiglia il peso ideale da utilizzare per il seguente esercizio: " + exercise + 
                    ". Tieni conto della progressione passata e assicurati che il consiglio sia chiaro e preciso ed usa un lessico gasante come un gymbro. "
                    "Includi anche eventuali avvertenze per evitare infortuni. Usa come unità di misura i Kg se rischiesto per esercizi in cui è richiesto l'utilizzo di manubri o bilancieri")
    else:
        content = ("Non avendo una cronologia di allenamento, consiglia il peso ideale da utilizzare per il seguente esercizio: " + exercise + 
                    ". Assicurati che il consiglio sia chiaro e preciso ed usa un un lessico gasante come un gymbro. "
                    "Includi anche eventuali avvertenze per evitare infortuni. Usa come unità di misura i Kg se rischiesto per esercizi in cui è richiesto l'utilizzo di manubri o bilancieri")
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an experienced and professional CrossFit coach. Your goal is to analyze the user's workout history "
                    "and suggest the optimal weight for their exercise. Provide detailed but concise advice tailored to the user's progress, "
                    "ensuring safety and effective progression. Respond in Italian. Use max 90 words"
                )
            },
            {
                "role": "user",
                "content": content
            }
        ]
    )
    suggestion = completion.choices[0].message.content

    return suggestion


def get_exercise(exercises):

    client = OpenAI( api_key=OPENAI_APIKEY)
  
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful crossfit coach."},
            {
                "role": "user",
                "content": "Extract the list of exercises from the workout:"+exercises
            }
        ]
    )
    
    suggestion = completion.choices[0].message

    return suggestion


def get_frasi_motivazionali():
    array = [
        "Ciao Bestia! Sei pronto a spingere al massimo? Dimmi pure se hai bisogno di una mano per scegliere il peso perfetto!",
        "Super atleta in arrivo! 💪 Vuoi un consiglio per trovare il peso ideale e dominare l'allenamento? Sono qui per te!",
        "Oggi si fanno scintille! 🔥 Pronto a sollevare come mai prima? Chiedimi un suggerimento e spingiamo insieme!",
        "Forte oggi, invincibile domani! Vuoi che ti aiuti a scegliere il peso giusto per spingerti al massimo?",
        "Vedo che sei carico! 💥 Se hai dubbi sul peso perfetto, sono qui per darti il boost che ti serve!",
        "Ehi campione, vuoi un aiutino per schiacciare il workout di oggi? Facciamo insieme la scelta giusta!",
        "Ogni ripetizione conta! Vuoi un consiglio su quale peso usare per portare i tuoi muscoli al livello successivo?",
        "Non esiste troppo forte! Hai bisogno di un suggerimento per scegliere il carico giusto? Sono qui per te!",
        "Pronto a superare i tuoi limiti? 💪 Posso aiutarti a trovare il peso perfetto per dominare ogni esercizio!",
        "Un allenamento perfetto inizia con il peso giusto. Facciamo la scelta insieme e preparati a conquistare!",
        "Oggi è il giorno in cui superi te stesso! Hai bisogno di un consiglio sul peso giusto? Sono qui per te!",
        "Pronto a sentire i muscoli bruciare? 🔥 Chiedimi pure se vuoi un aiuto con il peso perfetto!",
        "L'energia è alle stelle! 🚀 Vuoi un suggerimento per spingere al massimo ogni ripetizione?",
        "Oggi si cresce! 💪 Dimmi cosa vuoi allenare e ti aiuto a trovare il peso giusto per farlo al meglio!",
        "Qui non si scherza! Pronto a fare sul serio? Chiedimi un consiglio e vediamo cosa sollevi oggi!",
        "Ogni giorno un passo in più verso il tuo obiettivo! Vuoi sapere con che peso fare il prossimo passo?",
        "Campione, non lasciare che il peso ti limiti: fammi una domanda e ti aiuto a scegliere quello ideale!",
        "Oggi è un buon giorno per sentirsi potenti! Vuoi sapere quale peso scegliere? Sono qui per supportarti!",
        "Il tuo prossimo traguardo è a portata di mano! Dimmi cosa vuoi sollevare e ti consiglio il peso perfetto!",
        "Pronto per il prossimo livello? 🚀 Chiedimi pure e troviamo il peso giusto per spingerti oltre!",
        "Ogni ripetizione ti avvicina al top! Vuoi che ti suggerisca il peso migliore per fare la differenza?",
        "Ehi, atleta! Un carico perfetto è quello che fa crescere: chiedimi un consiglio e scegliamo insieme!",
        "Oggi si alza l’asticella! ⚡ Vuoi che ti consigli il peso ideale per sfondare i tuoi limiti?",
        "Preparati a dominare il workout! Se hai dubbi su quale peso usare, sono qui per te!",
        "Chi solleva con la testa, cresce davvero! Vuoi un consiglio su quale peso puntare oggi?",
        "Alza il volume dell’energia! 🎶 Vuoi che ti aiuti a scegliere il peso per arrivare più lontano?",
        "Pronto a fare la differenza? Se hai bisogno di un consiglio sul peso, sono al tuo fianco!",
        "La potenza è nel dettaglio: fammi sapere se vuoi un suggerimento per scegliere il carico giusto!",
        "Se non sfidi il peso, non sfidi te stesso! Vuoi un aiuto per trovare il carico perfetto?",
        "La forza è una scelta. Sei pronto? Chiedimi un consiglio e scegliamo il peso per l’allenamento perfetto!",
        "Il sudore di oggi è la forza di domani! Vuoi un suggerimento sul carico per spingere al massimo?",
        "Ogni chilogrammo conta! Dimmi se hai bisogno di aiuto per trovare il peso ideale per i tuoi obiettivi.",
        "Spingi forte, vai lontano! Hai bisogno di un consiglio sul peso per superare il tuo limite?",
        "Dai tutto quello che hai! Vuoi un aiuto per scegliere il carico perfetto per oggi?",
        "Non si tratta solo di sollevare, ma di superare se stessi. Ti serve un consiglio sul peso?",
        "Ogni serie è una vittoria! Dimmi se hai bisogno di aiuto per il carico giusto.",
        "Il tuo potenziale non ha limiti! Vuoi che ti aiuti a scegliere il peso per portarti oltre?",
        "Non mollare, non oggi! Hai dubbi sul peso giusto? Sono qui per te.",
        "Oggi è il giorno giusto per essere straordinario! Vuoi un consiglio sul carico per spaccare tutto?",
        "Un passo in più verso la tua versione migliore! Posso aiutarti a trovare il peso perfetto.",
        "Ogni chilogrammo è un passo verso la tua forza interiore. Vuoi un suggerimento per scegliere il carico?"    
    ]
    return array

def get_frasi_motivazionali_home():
    array = [
        "Spingi sempre al massimo 💪",
        "Sconfiggi i tuoi demoni 👻",
        "Il dolore passa, la gloria resta 🏆",
        "Atleta, oggi si vola! 💪 Sei pronto a dominare ogni WOD? 🏋️‍♂️"
        "Bestia, nessun peso può fermarti! Facciamo tremare il box! 🦁",
        "Roccia, oggi niente ti spezza! Let's crush it! 🪨",
        "Macchina, sei programmato per vincere! Spingiamo al massimo! 🤖",
        "Mostro, fai vedere chi comanda! Oggi è il tuo giorno! 👹",
        "Atleta, il sudore di oggi è il sorriso di domani. Daje! 💦",
        "Bestia, nessuno può fermarti! Sei una forza della natura! 🌪️",
        "Roccia, la tua forza è inarrestabile! Let's lift heavy! 💪",
        "Macchina, ogni rep è un passo verso la perfezione. Andiamo! 🔧",
        "Mostro, ogni WOD è una nuova sfida. Sei pronto a vincere? 🏆",
        "Atleta, il bilanciere non si solleverà da solo. Facciamolo insieme! 🏋️‍♀️",
        "Bestia, spingi oltre i tuoi limiti! Sei una macchina da guerra! 🚀",
        "Roccia, la tua determinazione è il tuo superpotere. Never give up! 🦸‍♂️",
        "Macchina, non esiste il troppo difficile, solo il non ancora. Let's go! ⚙️",
        "Mostro, ogni drop è un trionfo! Oggi fai la storia! 📜",
        "Atleta, se fosse facile, si chiamerebbe yoga. Ready to beast it? 🧘‍♂️",
        "Bestia, nessuno riesce a stare al tuo passo! Sei una leggenda! 🌟",
        "Roccia, ogni peso è solo un’altra pietra nella tua fortezza. Let's shape them! 🪨",
        "Macchina, il tuo motore è il più potente. Fuel it up! 🏎️",
        "Mostro, pronto a spaventare i pesi? Let's make them tremble! 👻",
        "Atleta, ogni burpee è un passo verso la grandezza. Keep going! 🔝",
        "Bestia, nessuno può competere con la tua energia! Let’s dominate! ⚡",
        "Roccia, ogni WOD è un test e tu sei il supereroe. Conquer it! 🦸‍♀️",
        "Macchina, nessuna sosta fino al successo! Let's grind! 💪",
        "Mostro, ogni kettlebell è un trofeo in attesa di essere sollevato. Go get it! 🏋️",
        "Atleta, se i WOD fossero facili, li chiamerebbero 'passeggiate'. Ready for battle? ,🥾",
        "Bestia, la tua potenza è senza pari! Sei pronto a esplodere? 💥",
        "Roccia, i pesi sono solo rocce in attesa di essere scolpite. Let's shape them! 🪨",
        "Macchina, ogni rep conta. Non fermarti fino alla vittoria! 🎯",
        "Mostro, sei il terrore di ogni bilanciere. Make them fear you! 👿",
        "Atleta, se c'è un limite, oggi lo supererai. Sei pronto a sfidarlo? 🚀",
        "Bestia, il tuo nome è sinonimo di potenza. Let's show them why! 🌟",
        "Roccia, oggi si scalano montagne! Ready to climb higher? 🏔️",
        "Macchina, sei il prototipo della perfezione. Let's work it out! 🔧",
        "Mostro, ogni rep è un'opera d'arte. Sei pronto a creare il tuo capolavoro? 🎨",
        "Atleta, oggi si vince! Ogni sforzo conta. Let’s do it together! 🤝",
        "Bestia, il box è il tuo regno. Sei pronto a governare? 👑",
        "Roccia, la tua determinazione è la tua arma segreta. Let’s unleash it! 🔥",
        "Macchina, non c'è sfida troppo grande. Sei programmato per vincere! ⚙️",
        "Mostro, i pesi non sanno cosa li aspetta. Sei pronto a distruggerli? 💥",
        "Atleta, il sudore di oggi è la forza di domani. Let's make it count! 💦",
        "Bestia, ogni WOD è un nuovo campo di battaglia. Sei pronto a combattere? ⚔️",
        "Roccia, la tua forza è un'esplosione. Let's ignite it! 💥",
        "Macchina, ogni rep è un passo verso la perfezione. Sei pronto a raggiungerla? 🎯",
        "Mostro, ogni giorno è un’opportunità per superare te stesso. Let’s do it! 🚀",
        "Atleta, ogni bilanciere è una sfida da conquistare. Sei pronto? 🏋️",
        "Bestia, oggi si fa sul serio. Ogni rep è un segno della tua grandezza! 💪",
        "Roccia, i pesi tremano al tuo arrivo. Sei pronto a dominare? 🌪️",
        "Macchina, ogni minuto conta. Sei pronto a renderli indimenticabili? ⏳",
        "Mostro, ogni goccia di sudore è un passo verso la leggenda. Let’s make history! 📜",
        "Se i burpees fossero facili, si chiamerebbero yoga! Sei pronto a dominare ogni rep? 💥",
        "Smetti di contare i minuti, fai contare ogni minuto. Nel WOD di oggi, tu sei il campione! 💥",
        "Dimentica il divano, il tuo nuovo migliore amico è il bilanciere! 💪",
        "Oggi niente scuse, solo sudore! 💥 Pronto per essere una bestia?",
        "Rendi ogni rep memorabile: spingi, suda, ripeti. CrossFit non è un gioco, è uno stile di vita! 💥",
        "Il dolore è temporaneo, il PR è per sempre! Oggi è il giorno giusto per battere i tuoi record? 💥",
        "Chi ha bisogno di capezzali quando puoi avere calli alle mani? Ready to grip and rip? 💪",
        "Pronto a trasformare il dolore in guadagno? Facciamolo con stile CrossFit! 💪",
        "Sorridi! Gli squat sono solo il modo del tuo corpo per abbracciarti! Pronto a sollevare? 💪",
        "Oggi si lavora duro, perché domani si riposa a letto... con i muscoli a pezzi! 😂",
        "L'unica cosa che deve essere leggera in palestra è il tuo atteggiamento! Let's go heavy or go home! 💪",
        "Fare CrossFit è come montare un mobile IKEA: sembra impossibile, ma poi ce la fai! 🙌",
        "Ogni burpee è un passo verso la leggenda. Sei pronto per lasciare il segno nel WOD di oggi? 💪",
        "Più sudore, meno problemi! Vuoi un consiglio su come far bruciare ogni rep? 💪",
        "Il CrossFit non ti rende solo forte, ti rende inarrestabile! Facciamo insieme la scelta giusta per il tuo workout 💪",
        "Dai tutto, anche l'ultimo respiro: il bilanciere non si solleverà da solo! 💪",
        "Non mollare mai! Ogni WOD ti avvicina al tuo meglio, ogni rep conta. Pronto a dare tutto? 💪",
        "Le chiacchiere stanno a zero, oggi si alza il mondo! 💪 Vuoi un suggerimento per spingere al massimo? 🏋️",
        "Gli amici non lasciano fare gli amici sollevamenti da soli! Vuoi che ti aiuti a trovare il peso giusto? 🏋️",
        "La fatica di oggi è la vittoria di domani. Preparati a fare scintille nel box! 💪",
        "Quando la vita ti dà i pesi, tu sollevali! Oggi è il giorno di fare la differenza! 🏋️",
        "Ogni rep è una storia di successo. Pronto a scrivere la tua? 🏋️",
        "Non si tratta di essere il più forte, ma di essere più forte di ieri. Let's crush it! 🏋️",
        "I limiti esistono solo nella tua mente. Sei pronto a superarli tutti oggi? 🏋️",
        "La fatica di oggi è la forza di domani. Scopri quanto puoi andare lontano! 🏋️",
        "Chi ha bisogno di un caffè quando hai il CrossFit? Ready to lift? 🏋️",
        "Quando senti la fatica, sappi che stai crescendo. Un altro set? 🏋️",
        "Il CrossFit non ti rende perfetto, ti rende potente! Let's go! 🏋️",
        "Non si tratta di quanto sei forte, ma di quanto tempo resisti. Fight on! 🏋️",
        "Ogni allenamento è una nuova opportunità di migliorare. Let's make it count! 🏋️",
        "Oggi è il giorno perfetto per fare il massimo. Are you in? 🏋️",
        "Non importa quanto lentamente vai, l'importante è non fermarsi mai. Move it! 🏋️",
        "Ogni caduta è un'occasione per rialzarsi più forte. Let's bounce back! 🏋️",
        "Non smettere quando sei stanco, smetti quando hai finito. Push through! 🏋️",
        "Oggi è il giorno di spingere oltre i tuoi limiti. Ready, set, lift! 🏋️",
        "La determinazione batte tutto. Sei pronto a dimostrarlo? 🏋️",
        "Le scuse non bruciano calorie. Ready to burn? 🏋️",
        "Un corpo sano è il risultato di una mente forte. Train your mind and body! 🏋️",
        "La felicità non si misura in chilogrammi, ma in PR. Let's set new records! 🏋️",
        "Ogni allenamento è un passo verso il tuo obiettivo. Let's step up 🏋️!"
    ]
    index = random.randint(1, 43)
    return array[index]



array_exercise_link = [
    {'exercise': 'Deadlift (DL)', 'link': '1ZXobu7JvvE'},
    {'exercise': 'Air Squat (AS)', 'link': 'rMvwVtlqjTE'},
    {'exercise': 'Shoulder Press (SP)', 'link': '5yWaNOvgFCM'},
    {'exercise': 'GHD Hip & Back Extension (GHBE)', 'link': 'QdCzafAXJhY'},
    {'exercise': 'GHD Back Extension (GBE)', 'link': 'ivDB23Kcv-A'},
    {'exercise': 'GHD Hip Extension (GHE)', 'link': 'P0iuN0xygc0'},
    {'exercise': 'GHD Hip, Back, And Hip-Back Extensions (GHBE/HBE)', 'link': 'uha4orxDqSM'},
    {'exercise': 'Front Squat (FS)', 'link': 'uYumuL_G_V0'},
    {'exercise': 'Sumo Deadlift High Pull (SDHP)', 'link': 'gh55vVlwlQg'},
    {'exercise': 'Push-Up (PU)', 'link': '0pkjOk0EiAk'},
    {'exercise': 'Strict Handstand Push-Up (HSPU)', 'link': '0wDEO6shVjc'},
    {'exercise': 'Handstand (HS)', 'link': '_-9_46by2JI'},
    {'exercise': 'Push Press (PP)', 'link': 'iaBVSJm78ko'},
    {'exercise': 'Medicine-Ball Clean (MBC)', 'link': 'KVGhkHSrDJo'},
    {'exercise': 'Rowing Technique Tips (Row)', 'link': 'fxfhQMbATCw'},
    {'exercise': 'L Pull-Up (LPU)', 'link': 'qeGS55RHBUU'},
    {'exercise': 'Thruster (TH)', 'link': 'L219ltL15zk'},
    {'exercise': 'Dumbbell Turkish Get-Up (DTGU)', 'link': 'saYKvqSscuY'},
    {'exercise': 'L-Sit Rope Climb (LSRC)', 'link': 'Ewf8rqGRbrE'},
    {'exercise': 'Back Squat (BS)', 'link': 'QmZAiBqPvZw'},
    {'exercise': 'Ring Dip (RD)', 'link': 'EznLCDBAPIU'},
    {'exercise': 'Strict Muscle-Up (SMU)', 'link': 'vJTJFc2wmk4'},
    {'exercise': 'Walking Lunge (WL)', 'link': 'DlhojghkaQ0'},
    {'exercise': 'Bench Press (BP)', 'link': 'SCVCLChPQFY'},
    {'exercise': 'Clean (CL)', 'link': 'Ty14ogq_Vok'},
    {'exercise': 'Slam Ball (SB)', 'link': 'k9W6g9LvXDI'},
    {'exercise': 'Ring Row (RR)', 'link': 'sEAOZc77wk8'},
    {'exercise': 'Inverted Burpee (IB)', 'link': 'M6_nkTKhaFY'},
    {'exercise': 'Handstand Pirouettes (HP)', 'link': 'tTnvKzRLCUk'},
    {'exercise': 'GHD Sit-Up (GSU)', 'link': 'oFwt7WfnPcc'},
    {'exercise': 'Snatch (SN)', 'link': 'GhxhiehJcQY'},
    {'exercise': 'Power Snatch (PSN)', 'link': 'TL8SMp7RdXQ'},
    {'exercise': 'Dumbbell Overhead Squat (DBOS)', 'link': 'azumEfnk-GI'},
    {'exercise': 'Burpee (BU)', 'link': 'auBLPXO8Fww'},
    {'exercise': 'AbMat Sit-Up (ASU)', 'link': 'VIZX2Ru9qU8'},
    {'exercise': 'Modified Rope Climb: Pull to Stand (MRC)', 'link': 'BsDRv1fiXIY'},
    {'exercise': 'Bent Arm, Bent Hip, Straight Leg Press (BABHSLP)', 'link': 'KR6xWc2kZrM'},
    {'exercise': 'Bent Arm, Bent Hip, Bent Leg Press (BABHBLP)', 'link': 'LZkVY7OoTg8'},
    {'exercise': 'Stiff-Stiff Press (SSP)', 'link': 'uufr_sV9jY8'},
    {'exercise': 'Hollow Back Press (HBP)', 'link': 'ql8zA6sEq6U'},
    {'exercise': 'Planche Press (PP)', 'link': 'z8mC1DND2kI'},
    {'exercise': 'Box Jump (BJ)', 'link': 'NBY9-kTuHEk'},
    {'exercise': 'Hang Power Clean (HPC)', 'link': '0aP3tgKZcHQ'},
    {'exercise': 'Dumbbell Hang Clean (DHC)', 'link': '8r44xv_Aqbw'},
    {'exercise': 'Dumbbell Thruster (DT)', 'link': 'u3wKkZjE8QM'},
    {'exercise': 'Hang Power Snatch (HPS)', 'link': '-mLzQdVAwlw'},
    {'exercise': 'Wall Walk (WW)', 'link': 'NK_OcHEm8yM'},
    {'exercise': 'Kettlebell Snatch (KS)', 'link': 'Pm-b2XFeABA'},
    {'exercise': 'Double Under (DU)', 'link': '-tF3hUsPZAI'},
    {'exercise': 'Sigle Under (SU)', 'link': 'hCuXYrTOMxI'},
    {'exercise': 'Hand Stand Push-up (HSPU)', 'link': '9wIkPCS4Mbo'},
    {'exercise': 'Toes To Bar (TTB)', 'link': '6dHvTlsMvNY'},
    {'exercise': 'Overehead Squat (OVS)', 'link': 'pn8mqlG0nkE'},
    {'exercise': 'Push Jerk (PJ)', 'link': 'V-hKuAfWNUw'},
    {'exercise': 'Clean & Jerk (C&J)', 'link': 'PjY1rH4_MOA'},
    {'exercise': 'Hang Clean & Jerk (HC&J)', 'link': 'KBpys4KTG5Q'},
    {'exercise': 'Power Clean and Push Jerk', 'link': 'LtoksZKesMA'},
    {'exercise': 'Hang Power Clean and Push Jerk', 'link': '8IYt7AtP8BI'},
    {'exercise': 'Muscle Snatch', 'link': 'bJYzOo1cNqY'},
    {'exercise': 'Hang Clean', 'link': 'DaKC_BEN5bk'},
    {'exercise': 'Hang Snatch', 'link': 'IucshEToDyM'},
    {'exercise': 'Dumbbell Clean (DC)', 'link': 'SYxObzJ3gn0'},
    {'exercise': 'Dumbbell Power Snatch (DPS)', 'link': '3mlhF3dptAo'},
    {'exercise': 'Dumbbell Hang Power Clean (DHPC)', 'link': 'myc1taX-uBs'},
    {'exercise': 'Ring Row', 'link': 'xhlReCpAE9k&list=PLdWvFCOAvyr3kgRLWSqgMSQc2Mp9yhdaq'},
    {'exercise': 'Pistol', 'link': 'qDcniqddTeE'},
    {'exercise': 'Muscle Up (MU)', 'link': 'OCg3UXgzftc'},
    {'exercise': 'Chest To Bar (CTB)', 'link': 'AyPTCEXTjOo'},
    {'exercise': 'Butterfly Pull-Up', 'link': 'U_MhBXnlInE'},
    {'exercise': 'Rope Climb', 'link': 'zBoTgBpkn7o'},
    {'exercise': 'Dumbbell Press (Shoulder to overhead)', 'link': 'AqzDJHxynwo'},
    {'exercise': 'Dumbbell Push Jerk (Shoulder to overhead)', 'link': 'rnN3pYswScE'},
    
]
    


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

