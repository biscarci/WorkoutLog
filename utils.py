import base64, os
import requests,json
from openai import OpenAI
from datetime import datetime, timedelta
import random

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
    prompt = "Extract from this image date, type, duration, exercises for each the workouts"

    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an experienced and helpful CrossFit coach, providing advice tailored to the user's workout history."},
        {
            "role": "user",
            "content": (
                "In Italian, suggest the optimal weight for the exercise: " + exercise + 
                ", based on the following workout history: " + history + 
                ". Provide a concise yet precise recommendation."
            )
        }
    ]
)


    suggestion = completion.choices[0].message

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
    array = ["Ciao Bestia! Sei pronto a spingere al massimo? Dimmi pure se hai bisogno di una mano per scegliere il peso perfetto!",
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
    "La forza è una scelta. Sei pronto? Chiedimi un consiglio e scegliamo il peso per l’allenamento perfetto!"]

    # Trova il numero massimo dell'array
    # max_value = max(array)
    # Genera un numero casuale tra 1 e max_value
    # random_number = random.randint(1, max_value)

    return array