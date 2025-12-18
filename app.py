# -*- coding: utf-8 -*-
# Importazioni standard della libreria Python
import click
import locale
import os
import random
import string
from datetime import datetime, timedelta, timezone
from functools import wraps
import hmac
import hashlib

# Importazioni di librerie esterne
from flask import Flask, Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask.cli import with_appcontext
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap5
from sqlalchemy.exc import SQLAlchemyError

# Importazioni del progetto locale
from forms import (AddWorkoutForm, AddWeeklyWorkoutForm, BulkDeleteStatsForm, EditPerformanceForm, LoginForm, PerformanceForm,
                   RegistrationForm, UpdateProfileForm, UpdateWorkoutForm, UserStatisticForm)
from utils import (allowed_file, 
                   random_motivational_phrase, random_rest_message, parse_week_text)


from markupsafe import Markup, escape


app = Flask(__name__)


locale.setlocale(locale.LC_ALL, 'it_IT')      

# Configurazione Flask App
app = Flask(__name__)

app.config['SECRET_KEY'] = '2c6d5c22597e8bb44dcd60f94c9d76508da64e88b550b0e215b581590ed382bb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
app.config['UPLOAD_FOLDER'] = 'uploads'


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bootstrap = Bootstrap5(app)

@app.template_filter('nl2br')
def nl2br(value):
    if value is None:
        return ""
    return Markup('<br>'.join(escape(value).splitlines()))

@app.context_processor
def inject_utils():
    return dict(
        random_motivational_phrase=random_motivational_phrase,
        random_rest_message=random_rest_message
    )

# Modelli Utente ed Esercizio
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_superuser = db.Column(db.Boolean, default=False)
    is_enabled = db.Column(db.Boolean, default=False)
    unlock_code = db.Column(db.String(10), nullable=True)  # Nuovo campo
    unlock_attempt = db.Column(db.Integer, default=0)
    demo_mode = db.Column(db.Boolean, default=False)
    total_workouts_added = db.Column(db.Integer, default=0)
    workouts = db.relationship('Workout', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_super_access(self):
        return self.is_superuser
    
    def get_statistics(self):
        return UserStatistic.query.filter_by(user_id=self.id).all()

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=True)
    name = db.Column(db.String(50), nullable=False)  
    description = db.Column(db.String(150), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String(150), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class WorkoutPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    performance_id = db.Column(db.Integer, db.ForeignKey('performance.id'), nullable=False)

    def get_performance(self):
        return Performance.query.get(self.performance_id)
    
    def get_workout(self):
        return Workout.query.get(self.workout_id)
    
    def get_user(self):
        return User.query.get(self.get_performance().user_id)

class UserStatistic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    exercise = db.Column(db.String(150), nullable=True)
    weight = db.Column(db.Float, nullable=True)
    reps = db.Column(db.Integer, nullable=True)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=True)
    action = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def logger(user_id, action):
    if user_id != None:
        u = User.query.get(int(user_id))
        l = Log(
            user = u.username,
            action = action
        )
    else:
        l = Log(
            user = '---',
            action = action
        )
    db.session.add(l)
    db.session.commit()

def superuser_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superuser:
            abort(403)  # Forbidden access
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def create_tables():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    # Controlla se il file esiste
    db_path = os.path.join(os.path.abspath('.'), db_path)
    if not os.path.exists(db_path):
        db.create_all()
   
    if current_user.is_authenticated:
        current_user.last_login = datetime.now(timezone.utc)
        if current_user.total_workouts_added >= 30 and current_user.demo_mode:
            current_user.is_enabled = False
        db.session.commit()

# Gestione login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_superuser(username, email, password):
    existing_user = User.query.filter_by(username=username).first()
    existing_superuser = User.query.filter_by(is_superuser=True).first()
    if existing_user or existing_superuser:
        return False
    su = User(
        username=username, 
        email=email, 
        is_superuser=True,
        is_enabled = True,
        demo_mode = False
    )
    su.set_password(password)
    db.session.add(su)
    db.session.commit()
    return True


@click.command('create-superuser')
@click.option('--username', prompt=True)
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_superuser_command(username, email, password):
    """Create a new superuser"""
    if create_superuser(username, email, password):
        click.echo('Superuser created successfully!')
    else:
        click.echo('Error: Superuser creation failed.')

# Register the command with your Flask app
app.cli.add_command(create_superuser_command)


@app.route('/admin/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    # Check if user is a superuser
    if not current_user.is_superuser:
        abort(403)  # Forbidden access
    
    # User Statistics
    total_users = User.query.count()
    active_users = User.query.filter(User.last_login > datetime.utcnow() - timedelta(days=30)).count()
    new_users = User.query.filter(User.created_at > datetime.utcnow() - timedelta(days=30)).count()

    # Workout Statistics
    total_workouts = Workout.query.count()
    workouts_this_month = Workout.query.filter(
        Workout.date > datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Most active workout name
    most_active_workout_type = db.session.query(
        Workout.name, 
        db.func.count(Workout.id).label('type_count')
    ).group_by(Workout.name).order_by(
        db.text('type_count DESC')
    ).first()[0] if total_workouts > 0 else 'N/A'

    # Recent User Activities (hypothetical - you'll need to implement an ActivityLog model)
    recent_activities = Log.query.order_by(Log.timestamp.asc()).all()

    # System Status (these would be actual system metrics)
    db_connections = 10  # Example placeholder
    server_uptime = '3 days 4 hours'  # Example placeholder
    last_backup = datetime.utcnow() - timedelta(days=1)

  
    return render_template(
        'admin_dashboard.html', 
        title='Admin Dashboard',
        total_users=total_users,
        active_users=active_users,
        new_users=new_users,
        total_workouts=total_workouts,
        workouts_this_month=workouts_this_month,
        most_active_workout_type=most_active_workout_type,
        recent_activities=recent_activities,
        db_connections=db_connections,
        server_uptime=server_uptime,
        last_backup=last_backup
    )


@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    # Check if user is a superuser
    if not current_user.is_superuser:
        abort(403)  # Forbidden access
    
    users = User.query.all()

    # Prepara i dati per il template
    for user in users:
        user.toggle_icon = "bi bi-toggle-on text-primary" if user.is_enabled else "bi bi-toggle-off text-secondary"
        user.demo_toggle_icon = "bi bi-toggle-on text-primary" if user.demo_mode else "bi bi-toggle-off text-secondary"

    return render_template(
        'admin_users.html', 
        title='Admin Users List',
        users=users,
    )

@app.route('/admin/manage_user/<int:id>', methods=['POST'])
@login_required
@superuser_required
def manage_user(id):
    """Pagina HTML per abilitare un utente."""
    user = User.query.get_or_404(id)
    user.is_enabled = not user.is_enabled
    user.unlock_attempt = 0
    db.session.commit()
    flash(f"User {user.username} {'abilitato' if user.is_enabled else 'disabilitato' } con successo.", "success")
    logger(current_user.id, f"User: {user.username} {'enabled' if user.is_enabled else 'disabled' }")
    return redirect(url_for('admin_users'))

@app.route('/admin/demo_user/<int:id>', methods=['POST'])
@login_required
@superuser_required
def demo_mode_user(id):
    """Pagina HTML per abilitare un utente."""
    user = User.query.get_or_404(id)
    user.demo_mode = not user.demo_mode
    db.session.commit()
    flash(f"Demo mode user: {user.username} {'abilitata' if user.demo_mode else 'non abilitata' } ", "success")
    logger(current_user.id, f"User {user.username} {'enabled' if user.is_enabled else 'disabled' }")
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user/<int:id>', methods=['POST'])
@login_required
@superuser_required
def delete_user(id):
    """Admin route to delete a user."""
    user_to_delete = User.query.get_or_404(id)

    # Prevent admin from deleting their own account
    if user_to_delete.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for('admin_users'))

    try:
        # Delete the user and commit changes
        workouts = Workout.query.filter_by(user_id=user_to_delete.id).all()
        if workouts:
            for w in workouts:
                db.session.delete(w)
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"User {user_to_delete.username} has been successfully deleted.", "success")
        logger(current_user.id, f"Deleted user {user_to_delete.username}")
    except Exception as e:
        # Handle errors and rollback
        db.session.rollback()
        flash(f"An error occurred while deleting the user: {str(e)}", "danger")

    return redirect(url_for('admin_users'))


@app.route('/admin/generate_unlock_code/<int:id>', methods=['POST'])
@login_required
@superuser_required
def generate_unlock_code(id):
    """API per generare un codice di sblocco per un utente."""
    user = User.query.get_or_404(id)
    # Genera un codice di sblocco casuale
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*()-_=+[]{}<>"
    unlock_code = ''.join(random.choices(characters, k=8))

    user.unlock_code = unlock_code
    user.is_enabled = False
    user.unlock_attempt = 0
    db.session.commit()
    flash(f'Generated unlock key for {user.username}', "success")
    logger(current_user.id, f'Generated unlock key for {user.username}')
    return redirect(url_for('admin_users'))


# Rotte principali
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    # Redirect to dashboard if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if form.validate_on_submit():
        # Check for existing username or email
        existing_username = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()

        if existing_username:
            flash('Username is already taken. Please choose another one.', 'danger')
            return redirect(url_for('register'))

        if existing_email:
            flash('Email is already registered. Please use a different email.', 'danger')
            return redirect(url_for('register'))

        # Create and save the new user
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            is_superuser=False,
            is_enabled=True,
            demo_mode=True
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        logger(new_user.id, 'New user registered')
        return redirect(url_for('login'))

    # Render the registration template with the form
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    # Redirect authenticated users to their respective dashboards
    if current_user.is_authenticated:
        if current_user.is_superuser:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if form.validate_on_submit():
        # Fetch the user by username
        user = User.query.filter_by(username=form.username.data).first()

        # Validate user and password
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)

            # Log the successful login
            logger(user.id, 'Login successful')

            # Redirect based on user role
            if user.is_superuser:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))

        # Handle login failure
        flash('Login failed. Please check your username and password.', 'danger')
        if form.username.data:
            logger(None, f'Login failed for username: {form.username.data}')
        else:
            logger(None, 'Login failed for an unspecified username')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logger(current_user.id, f"User {current_user.username} logged out at {datetime.utcnow()}")
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    form = UpdateProfileForm()

    if form.validate_on_submit():
        # Gestione del codice di sblocco
        if form.unlock_code.data:
            if user.unlock_attempt >= 10:
                flash('Il tuo profilo è bloccato a causa di troppi tentativi.', 'danger')
            elif user.unlock_code == form.unlock_code.data:
                user.is_enabled = True
                user.unlock_code = None  # Resetta il codice dopo l'uso
                user.unlock_attempt = 0  # Resetta i tentativi
                user.demo_mode = False
                db.session.commit()
                flash('Il tuo profilo è stato sbloccato con successo!', 'success')
            else:
                user.unlock_attempt += 1
                db.session.commit()
                flash('Codice di sblocco non valido. Riprova.', 'warning')

        # Aggiornamento delle informazioni del profilo
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Il tuo profilo è stato aggiornato con successo.', 'success')

        return redirect(url_for('profile'))

    elif request.method == 'GET':
        # Precompila il form con i dati dell'utente
        form.username.data = user.username
        form.email.data = user.email

    return render_template('profile.html', form=form)


@app.route('/menu', methods=['GET'])
@login_required
def menu():
    return render_template('menu.html', title='Menu')

@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Riceve i dati dal client
    year = request.args.get('year', default=datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.now().month, type=int)
    day = request.args.get('day', default=datetime.now().day, type=int)
        
    try:
        start_date = datetime(year, month, day)
    except ValueError:
        start_date = datetime(year, month, 1)
    end_date = start_date + timedelta(days=1)

    owner = current_user
    workouts = Workout.query.filter_by(user_id=owner.id).filter(
        Workout.date >= start_date, Workout.date < end_date
    ).order_by(Workout.date.asc()).all()

    start_day_week = start_date - timedelta(days=start_date.weekday())
    
    prev_day = start_day_week - timedelta(days=7)
    next_day = start_day_week + timedelta(days=7)
    
    weekdays = [
        start_day_week + timedelta(days=i)
        for i in range(7)
    ]


    return render_template('dashboard.html', 
                           title=('LIFT OFF'),
                           workouts=workouts,
                           year=year,
                           month=month,
                           day=start_date.day,
                           date=start_date,
                           prev_day=prev_day,
                           next_day=next_day,
                           weekdays=weekdays,
                           user=current_user,
                           )

@app.route('/dashboard/date/<int:day>/<int:month>/<int:year>', methods=['GET'])
@login_required
def select_workout_date(day, month, year):
    try:
        start_date = datetime(year, month, day)
    except ValueError:
        start_date = datetime(year, month, 1)
    end_date = start_date + timedelta(days=1)

    owner = current_user
    workouts = Workout.query.filter_by(user_id=owner.id).filter(
        Workout.date >= start_date, Workout.date < end_date
    ).order_by(Workout.date.asc()).all()

    start_day_week = start_date - timedelta(days=start_date.weekday())

    prev_day = start_day_week - timedelta(days=7)
    next_day = start_day_week + timedelta(days=7)
        
    weekdays = [
        start_day_week + timedelta(days=i)
        for i in range(7)
    ]

    return render_template('dashboard.html', 
                           title=('LIFT OFF'),
                           workouts=workouts,
                           year=year,
                           month=month,
                           day=start_date.day,
                           date=start_date,
                           prev_day=prev_day,
                           next_day=next_day,
                           weekdays=weekdays,
                           user=current_user)


@app.route('/workout/add', methods=['GET', 'POST'])
@login_required
def add_workout():
    form = AddWorkoutForm()

    if form.validate_on_submit():
        w = Workout(
            date=form.date.data,
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id
        )
        current_user.total_workouts_added += 1
        db.session.add(w)
        db.session.commit()
        flash('Workout inserito con successo!', 'success')
        logger(current_user.id, 'New workout created')
        return redirect(url_for('dashboard'))

    return render_template('add_workout.html',
                           title=('Add Workout'),
                           user=current_user,
                           form=form)



@app.route('/workout/week/add', methods=['GET', 'POST'])
@login_required
def add_weekly_workouts():
    form = AddWeeklyWorkoutForm()


    if form.validate_on_submit():
        try:
            parsed = parse_week_text(form.week_text.data)
            #print(parsed)
            for w_data in parsed["workouts"]:
                w = Workout(
                    date=w_data["date"],
                    name=w_data['name'],
                    description="\n".join(w_data["description"]),
                    user_id=current_user.id
                )
                db.session.add(w)
                current_user.total_workouts_added += 1

            db.session.commit()
            flash('Workout settimanali inseriti con successo!', 'success')
            logger(current_user.id, 'Weekly workouts created')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore parsing workout: {str(e)}', 'danger')

    return render_template('add_weekly_workout.html',
                           title=('Add Weekly Workouts'),
                           user=current_user,
                           form=form)


@app.route('/workout/delete/<int:id>', methods=['POST'])
@login_required
def delete_workout(id):
    workout = Workout.query.get_or_404(id)
    if workout.user_id != current_user.id and not current_user.is_superuser:
        abort(403)
    db.session.delete(workout)
    db.session.commit()
    flash('Allenamento eliminato con successo.', 'success')
    logger(current_user.id, 'Deleted workout '+workout.date.strftime('%d-%m-%Y'))
    return redirect(url_for('select_workout_date', day=workout.date.day, month=workout.date.month, year=workout.date.year))


@app.route('/workout/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_workout(id):
    w = Workout.query.get_or_404(id)
    if w.user_id != current_user.id and not current_user.is_superuser:
        abort(403)
    form = UpdateWorkoutForm()
    if form.validate_on_submit():
        w.date = form.date.data
        w.name = form.name.data
        w.description = form.description.data
        db.session.commit()
        flash('Workout aggiornato con successo!', 'success')
        logger(current_user.id, 'Modified workout '+w.date.strftime('%d-%m-%Y'))
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        form.date.data = w.date
        form.name.data = w.name
        form.description.data = w.description

    return render_template('edit_workout.html',
                           title=('Edit Workout'),
                           form=form,
                           workout=w)


@app.route('/performance/add/<int:id>', methods=['GET', 'POST'])
@login_required
def add_performance(id):
    form = PerformanceForm()
    w = Workout.query.get_or_404(id)

    selected_exercise = (request.args.get('exercise') or '').strip()
    exercises = [
        row[0]
        for row in db.session.query(UserStatistic.exercise)
        .filter_by(user_id=current_user.id)
        .filter(UserStatistic.exercise.isnot(None))
        .distinct()
        .order_by(UserStatistic.exercise.asc())
        .all()
    ]

    stats_exercise = []
    max_weight = None
    max_reps = None
    best_1rm = None
    rm_percent_table = []
    if selected_exercise:
        stats_exercise = UserStatistic.query.filter_by(
            user_id=current_user.id,
            exercise=selected_exercise
        ).order_by(UserStatistic.date.desc()).limit(15).all()

        weights = [s.weight for s in stats_exercise if s.weight is not None]
        reps = [s.reps for s in stats_exercise if s.reps is not None]
        max_weight = max(weights) if weights else None
        max_reps = max(reps) if reps else None

        # Stima 1RM (formula tipo Brzycki) a partire dalle statistiche disponibili
        one_rm_estimates = []
        for s in stats_exercise:
            if s.weight is None or s.reps is None:
                continue
            if s.reps <= 0:
                continue
            # evita divisione per ~0 con reps troppo alte
            denom = 1.0278 - (0.0278 * float(s.reps))
            if denom <= 0:
                continue
            one_rm_estimates.append(float(s.weight) / denom)

        best_1rm = max(one_rm_estimates) if one_rm_estimates else None
        if best_1rm:
            for p in range(100, 39, -5):
                rm_percent_table.append(
                    {
                        "percent": p,
                        # arrotonda a 0.5kg per una tabella più “da palestra”
                        "kg": round((best_1rm * (p / 100.0)) * 2) / 2,
                    }
                )

    workout_performances = WorkoutPerformance.query.filter_by(workout_id=id).order_by(WorkoutPerformance.id.desc()).all()


    if form.validate_on_submit():
        perf_date = datetime.combine(form.date.data, datetime.min.time()) if form.date.data else datetime.now()
        perf = Performance(
            date=perf_date,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(perf)
        db.session.flush()  # Ottieni l'ID prima del commit
        
        link = WorkoutPerformance(workout_id=id, performance_id=perf.id)
        db.session.add(link)
        db.session.commit()
        flash('Performance salvata con successo', 'success')
        logger(current_user.id, 'New performance added')
        return redirect(url_for('add_performance', id=w.id, exercise=selected_exercise or None))

    return render_template(
        'add_performance.html', 
        title='Add Performance', 
        workout=w, 
        form=form, 
        workout_performances=workout_performances,
        exercises=exercises,
        selected_exercise=selected_exercise,
        stats_exercise=stats_exercise,
        max_weight=max_weight,
        max_reps=max_reps,
        best_1rm=best_1rm,
        rm_percent_table=rm_percent_table,
        )


@app.route('/performance/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_performance(id):
    perf = Performance.query.get_or_404(id)
    if perf.user_id != current_user.id and not current_user.is_superuser:
        abort(403)

    link = WorkoutPerformance.query.filter_by(performance_id=id).first()
    workout_id = link.workout_id if link else None

    form = EditPerformanceForm()
    if form.validate_on_submit():
        if form.date.data:
            perf.date = datetime.combine(form.date.data, datetime.min.time())
        perf.description = form.description.data
        db.session.commit()
        flash('Performance aggiornata', 'success')
        logger(current_user.id, 'Performance updated')
        if workout_id:
            return redirect(url_for('add_performance', id=workout_id))
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        form.date.data = perf.date.date() if isinstance(perf.date, datetime) else perf.date
        form.description.data = perf.description

    return render_template('edit_performance.html', title='Edit Performance', form=form, workout_id=workout_id, perf_id=perf.id)


@app.route('/performance/delete/<int:id>', methods=['POST'])
@login_required
def delete_performance(id):
    perf = Performance.query.get_or_404(id)
    if perf.user_id != current_user.id and not current_user.is_superuser:
        abort(403)

    links = WorkoutPerformance.query.filter_by(performance_id=id).all()
    workout_id = links[0].workout_id if links else None
    for link in links:
        db.session.delete(link)
    db.session.delete(perf)
    db.session.commit()
    flash('Performance eliminata', 'success')
    logger(current_user.id, 'Performance deleted')

    if workout_id:
        return redirect(url_for('add_performance', id=workout_id))
    return redirect(url_for('dashboard'))


@app.route('/stats', methods=['GET', 'POST'])
@login_required
def user_stats():
    form = UserStatisticForm()
    delete_form = BulkDeleteStatsForm()
    selected_exercise = (request.args.get('exercise') or '').strip()
    if form.validate_on_submit():
        stat = UserStatistic(
            user_id=current_user.id,
            date=form.date.data,
            exercise=form.exercise.data,
            weight=form.weight.data,
            reps=form.reps.data
        )
        db.session.add(stat)
        db.session.commit()
        flash('Statistiche salvate', 'success')
        logger(current_user.id, 'User stats added')
        return redirect(url_for('user_stats'))

    exercises = [
        row[0]
        for row in db.session.query(UserStatistic.exercise)
        .filter_by(user_id=current_user.id)
        .filter(UserStatistic.exercise.isnot(None))
        .distinct()
        .order_by(UserStatistic.exercise.asc())
        .all()
    ]

    stats_query = UserStatistic.query.filter_by(user_id=current_user.id)
    if selected_exercise:
        stats_query = stats_query.filter(UserStatistic.exercise == selected_exercise)
    stats = stats_query.order_by(UserStatistic.date.desc()).all()

    weights = [s.weight for s in stats if s.weight is not None]
    reps = [s.reps for s in stats if s.reps is not None]
    max_weight = max(weights) if weights else None
    max_reps = max(reps) if reps else None

    return render_template(
        'stats.html',
        title='Statistiche',
        form=form,
        delete_form=delete_form,
        stats=stats,
        exercises=exercises,
        selected_exercise=selected_exercise,
        max_weight=max_weight,
        max_reps=max_reps,
    )


@app.route('/stats/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_stat(id):
    stat = UserStatistic.query.get_or_404(id)
    if stat.user_id != current_user.id and not current_user.is_superuser:
        abort(403)

    form = UserStatisticForm()
    if form.validate_on_submit():
        stat.date = form.date.data
        stat.exercise = form.exercise.data
        stat.weight = form.weight.data
        stat.reps = form.reps.data
        db.session.commit()
        flash('Statistica aggiornata', 'success')
        logger(current_user.id, 'User stats updated')
        return redirect(url_for('user_stats'))

    if request.method == 'GET':
        form.date.data = stat.date
        form.exercise.data = stat.exercise
        form.weight.data = stat.weight
        form.reps.data = stat.reps

    return render_template('edit_stat.html', title='Edit Stat', form=form, stat_id=stat.id)


@app.route('/stats/delete', methods=['POST'])
@login_required
def delete_stats():
    delete_form = BulkDeleteStatsForm()
    if not delete_form.validate_on_submit():
        abort(400)

    ids = request.form.getlist('selected_ids')
    ids = [int(i) for i in ids if str(i).isdigit()]
    if not ids:
        flash('Nessuna statistica selezionata', 'info')
        return redirect(url_for('user_stats'))

    query = UserStatistic.query.filter(UserStatistic.id.in_(ids))
    if not current_user.is_superuser:
        query = query.filter_by(user_id=current_user.id)

    deleted = query.delete(synchronize_session=False)
    db.session.commit()
    flash(f'Eliminate {deleted} statistiche', 'success')
    logger(current_user.id, f'User stats deleted: {deleted}')
    return redirect(url_for('user_stats'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', error=error), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html', error=error), 500


if __name__ == '__main__':
    app.run(debug=True)
