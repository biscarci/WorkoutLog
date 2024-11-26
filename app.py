import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, current_user, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, UpdateWorkoutForm, AddWorkoutForm, AddExerciseForm, UpdateExerciseForm, AddExerciseForm
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap5
from utils import get_text_from_image_openai, allowed_file,get_exercise_suggestion, get_exercise, get_month_start_end, get_frasi_motivazionali

import locale

locale.setlocale(locale.LC_ALL, 'it_IT')      

# Configurazione Flask App
app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bootstrap = Bootstrap5(app)

# Modelli Utente ed Esercizio
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    workouts = db.relationship('Workout', backref='user', lazy=True)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=True)
    type = db.Column(db.String(50), nullable=False)  
    duration = db.Column(db.String(50), nullable=True)
    note = db.Column(db.String(150), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise = db.relationship('Exercise', backref='workout', lazy=True)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    weight_percentage = db.Column(db.Integer, nullable=True)
    rpe = db.Column(db.Integer, nullable=True)
    repetitions = db.Column(db.String(20), nullable=True)
    time = db.Column(db.String(20), nullable=True)
    note = db.Column(db.String(150), nullable=True)
    weight = db.Column(db.Float, nullable=True)
    score = db.Column(db.String(50), nullable=True)
    advice = db.Column(db.String(2000), nullable=True)
    equipment = db.Column(db.String(50), nullable=True)
    date = db.Column(db.DateTime, default=datetime.now)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)

    def get_workout(self):
        w = Workout.query.get_or_404(self.workout_id)
        return w
    
@app.before_request
def create_tables():
    # The following line will remove this handler, making it
    # only run on the first request
    app.before_request_funcs[None].remove(create_tables)
    db.create_all()
    
# Gestione login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotte principali
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registrazione avvenuta con successo!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Login non riuscito. Controlla username e password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Riceve i dati dal client
    year = request.args.get('year', default=datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.now().month, type=int)
        
    start_date, end_date = get_month_start_end(month, year)
    workouts = Workout.query.filter_by(user_id=current_user.id).filter(
        Workout.date.between(start_date, end_date)
    ).order_by(Workout.date.asc()).all()

    return render_template('dashboard.html', 
                           title=('Workout Log'),
                           workouts=workouts,
                           year=year,
                           month=month,
                           date=start_date,
                           quotes=get_frasi_motivazionali())

@app.route('/dashboard/date/<int:month>/<int:year>', methods=['GET'])
@login_required
def select_workout_date(month, year):
    # Riceve i dati dal client
    start_date, end_date = get_month_start_end(month, year)
    workouts = Workout.query.filter_by(user_id=current_user.id).filter(
        Workout.date.between(start_date, end_date)
    ).order_by(Workout.date.asc()).all()


    return render_template('dashboard.html', 
                           title=('Workout Log'),
                           workouts=workouts,
                           year=year,
                           month=month,
                           date=start_date,
                           quotes=get_frasi_motivazionali())

@app.route('/workout/upload', methods=['GET', 'POST'])
@login_required
def upload_workout():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
            file.save(filepath)
            wod = get_text_from_image_openai(filepath)
            os.remove(filepath)
    
        if wod:
            try:
                wod_date = datetime.strptime(wod.date, "%d-%m-%Y")
            except:
                wod_date = datetime.now()
            # Processamento e salvataggio degli esercizi estratti
            for w in wod.workouts:
                workout = Workout(
                    date = wod_date,
                    type = w.type,
                    duration = w.duration,
                    user_id = current_user.id
                )
                db.session.add(workout)
                db.session.commit()
                for e in w.exercises:
                    exercise = Exercise(
                        name = e.name,
                        repetitions = e.description,
                        note = e.note,
                        workout_id = workout.id
                    )
                    db.session.add(exercise)
                    db.session.commit()
            flash('Esercizi estratti e salvati con successo!')
        else:
            print('Qualcosa è andato storto')
        return redirect(url_for('dashboard'))
                            
    return render_template('upload.html', title=('Upload Workout'))

@app.route('/workout/add', methods=['GET', 'POST'])
@login_required
def add_workout():
    form = AddWorkoutForm()
    if form.validate_on_submit():
        w = Workout(
                    date = form.date.data,
                    type = form.type.data,
                    duration = form.duration.data,
                    note = form.note.data,
                    user_id = current_user.id
                )
        db.session.add(w)
        db.session.commit()
        flash('Workout inserito con successo!', 'success')
        return redirect(url_for('dashboard'))
    

    return render_template('add_workout.html',
                           title=('Add Workout'), 
                           form=form)

@app.route('/exercise/add/<int:id>', methods=['GET', 'POST'])
@login_required
def add_exercise(id):
    w = Workout.query.get_or_404(id)
    form = AddExerciseForm()
    if form.validate_on_submit():
        e = Exercise(
            name = form.name.data,
            repetitions = form.repetitions.data,
            note = form.note.data,
            weight = form.weight.data,
            score = form.score.data,
            equipment = form.equipment.data,
            workout_id = w.id
                )
        db.session.add(e)
        db.session.commit()
        flash('Esercizio inserito con successo!', 'success')
        return redirect(url_for('dashboard'))
    

    return render_template('add_exercise.html',
                           title=('Add Workout'), 
                           form=form,
                           workout=w)

@app.route('/workout/menu', methods=['GET', 'POST'])
@login_required
def add_workout_menu():                           
    return render_template('add_workout_menu.html', title=('Menu'))

@app.route('/workout/delete/<int:id>', methods=['POST'])
@login_required
def delete_workout(id):
    # Trova l'allenamento da eliminare basato sull'id
    workout = Workout.query.get_or_404(id)
    
    # Verifica che l'allenamento appartenga all'utente corrente
    if workout.user_id != current_user.id:
        flash('Non sei autorizzato a eliminare questo allenamento.', 'danger')
        return redirect(url_for('dashboard'))

    # Se il metodo è POST, conferma l'eliminazione
    if request.method == 'POST':
        # Rimuovi tutti gli esercizi correlati al workout
        exercises = Exercise.query.filter_by(workout_id=workout.id).all()
        if exercises:
            for e in exercises:
                db.session.delete(e)
        db.session.commit()
        # Rimuovi l'allenamento dal database
        db.session.delete(workout)
        db.session.commit()
        flash('Allenamento eliminato con successo.', 'success')
        return redirect(url_for('dashboard'))

@app.route('/workout/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_workout(id):
    w = Workout.query.get_or_404(id)
    form = UpdateWorkoutForm()
    if form.validate_on_submit():
        w.date = form.date.data     
        w.type = form.type.data     
        w.duration = form.duration.data 
        db.session.commit()
        flash('Workout aggiornato con successo!', 'success')
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        form.date.data = w.date
        form.type.data = w.type
        form.duration.data = w.duration

    return render_template('edit_workout.html',
                           title=('Edit Workout'), 
                           form=form, 
                           workout=w)

@app.route('/exercise/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_exercise(id):
    e = Exercise.query.get_or_404(id)
    w = e.get_workout()
    form = UpdateExerciseForm()
    if form.validate_on_submit():        
        e.name = form.name.data     
        e.repetitions = form.repetitions.data     
        e.note = form.note.data 
        e.weight = form.weight.data
        e.equipment = form.equipment.data
        e.score = form.score.data
        db.session.commit()
        flash('Esercizio aggiornato con successo!', 'success')
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        form.name.data = e.name
        form.repetitions.data = e.repetitions
        form.note.data = e.note
        form.weight.data = e.weight
        form.equipment.data = e.equipment 
        form.score.data = e.score
    return render_template('edit_exercise.html',
                           title=('Edit Exercise'), 
                           form=form, 
                           exercise = e,
                           workout=w)

@app.route('/exercise/delete/<int:id>', methods=['POST'])
@login_required
def delete_exercise(id):
    # Trova l'allenamento da eliminare basato sull'id
    exercise = Exercise.query.get_or_404(id)
    
    # Verifica che l'allenamento appartenga all'utente corrente
    if exercise.get_workout().user_id != current_user.id:
        flash('Non sei autorizzato a eliminare questo esercizio.', 'danger')
        return redirect(url_for('dashboard'))

    # Se il metodo è POST, conferma l'eliminazione
    if request.method == 'POST':
        # Rimuovi l'allenamento dal database
        db.session.delete(exercise)
        db.session.commit()
        flash('Esercizio eliminato con successo.', 'success')
        return redirect(url_for('dashboard'))

@app.route('/exercise/info/<int:id>', methods=['GET'])
@login_required
def exercise_info(id): 
    exercise = Exercise.query.get_or_404(id)
    if 'back squat' in exercise.name: key = 'squat'
    elif 'front squat' in exercise.name: key = 'front squat'
    elif 'push press' in exercise.name: key = 'push press'
    elif 'push jerk' in exercise.name: key = 'push jerk'
    elif 'strict press' in exercise.name: key = 'strict press'
    elif 'split jerk' in exercise.name: key = 'split jerk'
    elif 'deadlift' in exercise.name: key = 'squat'
    elif 'bench press' in exercise.name: key = 'bench press'
    else: key = exercise.name
    exercises = Exercise.query.filter(Exercise.name.icontains(key), Exercise.id != id).order_by(Exercise.date.desc()).all()

    history = ''
    for e in exercises:
        if  e.weight != None:
            history += e.get_workout().date.strftime("%m/%d/%Y") + ' ' + \
                e.name + ' ' + e.repetitions + ' executed with ' + str(e.weight) + 'Kg' + ' ' + \
                e.score
        else:
            history += e.name + ' ' + e.repetitions
        history += '\n'

    if exercise.advice == None:
        exercise.advice = get_exercise_suggestion(exercise.name, history)    
        db.session.commit()    
   

    return render_template('exercise_info.html',
                        title=('Adivice'), 
                        advice = exercise.advice,
                        exercise = exercise,
                        exercises = exercises,
                        history = history,
                        workout = exercise.get_workout())

@app.route('/workout/history',  methods=['GET', 'POST'])
@login_required
def workout_history():
    
    
    return render_template('exercise_history.html',title=('Workout History'))


if __name__ == '__main__':
    app.run(debug=True)
