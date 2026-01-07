# -*- coding: utf-8 -*-
# Importazioni standard della libreria Python
import click
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
import hmac
import hashlib

# Importazioni di librerie esterne
from flask import Flask, Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask.cli import with_appcontext
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
import requests, re
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap5
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

# Importazioni del progetto locale
from forms import (AddWorkoutForm, AddWeeklyWorkoutForm, AdminRegistrationForm, BulkDeleteStatsForm, EditPerformanceForm, LoginForm, PerformanceForm,
                   RegistrationForm, UpdateProfileForm, UpdateWorkoutForm, UserStatisticForm)
from utils import (allowed_file, 
                   random_motivational_phrase, random_rest_message, parse_week_text)


from markupsafe import Markup, escape
from flask_migrate import Migrate


app = Flask(__name__)

DEBUG_MODE = os.getenv("FLASK_DEBUG", "0") == "1"

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if DEBUG_MODE:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workout.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL non impostata")

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"sslmode": "require"}
    }
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Aggiungi questa riga
login_manager = LoginManager()
login_manager.init_app(app)
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
    name = db.Column(db.String(200), nullable=True, default='')
    surname = db.Column(db.String(200), nullable=True, default='')
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_superuser = db.Column(db.Boolean, default=False)
    is_enabled = db.Column(db.Boolean, default=False)
    total_workouts_added = db.Column(db.Integer, default=0)
    workouts = db.relationship(
        'Workout',
        backref=db.backref('user', lazy=True),
        lazy=True,
        cascade="all, delete-orphan",
    )
    performances = db.relationship(
        'Performance',
        backref=db.backref('user', lazy=True),
        lazy=True,
        cascade="all, delete-orphan",
    )
    statistics = db.relationship(
        'UserStatistic',
        backref=db.backref('user', lazy=True),
        lazy=True,
        cascade="all, delete-orphan",
    )
    
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
    name = db.Column(db.Text, nullable=False)  
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relazione con WorkoutPerformance
    links = db.relationship(
        'WorkoutPerformance',
        backref='workout',  # Rimuovi db.backref() da qui
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    # Relazione con Range 
    ranges = db.relationship(
        'Range',  # Usa stringa per evitare problemi di import
        back_populates='workout',  # NON backref qui
        lazy=True,
        cascade="all, delete-orphan",
        order_by='Range.order'  # Mantieni l'ordine automaticamente
    )

    def get_ranges_by_user(self):
        """Ritorna array di stringhe con i pesi calcolati."""
        ranges = Range.query\
            .filter_by(workout_id=self.id)\
            .order_by(Range.order.asc()).all()
        
        result = []
        
        for r in ranges:
            user_stat = UserStatistic.query\
                .filter(UserStatistic.user_id == self.user_id)\
                .filter(func.lower(UserStatistic.exercise) == func.lower(r.exercise))\
                .first()
            
            if user_stat and user_stat.weight:
                weight = round((user_stat.weight * r.value) / 100, 1)
                result.append(f"{r.value}% @{weight}kg")
            else:
                return "Massimale non trovato, quando cazzo ti decidi a registrarlo?"
        
        return result


class Range(db.Model):  # Usa db.Model, non Base
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    exercise = db.Column(db.String(200), nullable=False)  # Specifica lunghezza
    order = db.Column(db.Integer, nullable=False)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)  # Nome consistente
    
    # Relazione inversa
    workout = db.relationship('Workout', back_populates='ranges')


class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    links = db.relationship(
        'WorkoutPerformance',
        backref=db.backref('performance', lazy=True),
        lazy=True,
        cascade="all, delete-orphan",
    )


class WorkoutPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer, 
        db.ForeignKey('workout.id', ondelete='CASCADE'),
        nullable=False
    )
    performance_id = db.Column(
        db.Integer, 
        db.ForeignKey('performance.id', ondelete='CASCADE'),
        nullable=False
    )
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
    exercise = db.Column(db.Text, nullable=True)
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

def bootstrap_superuser_from_env():
    """Create a default superuser from env vars, idempotent."""
    if app.config.get('_BOOTSTRAP_SUPERUSER_RAN'):
        return
    app.config['_BOOTSTRAP_SUPERUSER_RAN'] = True

    username = os.getenv('ADMIN_USERNAME')
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')
    name = os.getenv('ADMIN_NAME')
    surname = os.getenv('ADMIN_SURNAME')
    if not username or not email or not password:
        return
    try:
        created = create_superuser(
            username=username,
            email=email,
            password=password,
            name=name,
            surname=surname,
        )
        if created:
            app.logger.warning("Bootstrapped superuser '%s' from env vars", username)
    except Exception:
        app.logger.exception('Failed to bootstrap superuser from env vars')


@app.before_request
def create_tables():
    if current_user.is_authenticated:
        current_user.last_login = datetime.now(timezone.utc)
        db.session.commit()

# Gestione login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_superuser(username, email, password, name=None, surname=None):
    existing_user = User.query.filter_by(username=username).first()
    existing_superuser = User.query.filter_by(is_superuser=True).first()
    if existing_user or existing_superuser:
        return False
    su = User(
        name=name or username,
        surname=surname or '',
        username=username, 
        email=email, 
        is_superuser=True,
        is_enabled = True,
    )
    su.set_password(password)
    db.session.add(su)
    db.session.commit()
    return True


@click.command('create-superuser')
@click.option('--username', prompt=True)
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--name', prompt=False, required=False, default=None)
@click.option('--surname', prompt=False, required=False, default=None)
@with_appcontext
def create_superuser_command(username, email, password, name, surname):
    """Create a new superuser"""
    if create_superuser(username, email, password, name=name, surname=surname):
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

    log_date_str = request.args.get('log_date', '') or ''
    
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

    # Recent User Activities filtered by selected day if provided
    log_query = Log.query
    if log_date_str:
        try:
            selected_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()
            start_dt = datetime.combine(selected_date, datetime.min.time())
            end_dt = start_dt + timedelta(days=1)
            log_query = log_query.filter(Log.timestamp >= start_dt, Log.timestamp < end_dt)
        except ValueError:
            log_date_str = ''

    recent_activities = log_query.order_by(Log.timestamp.asc()).all()

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
        last_backup=last_backup,
        log_date=log_date_str,
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
    db.session.commit()
    flash(f"User {user.username} {'abilitato' if user.is_enabled else 'disabilitato' } con successo.", "success")
    logger(current_user.id, f"User: {user.username} {'enabled' if user.is_enabled else 'disabled' }")
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
        # 1. Delete WorkoutPerformance records (junction table)
        workouts = Workout.query.filter_by(user_id=user_to_delete.id).all()
        workout_ids = [w.id for w in workouts]
        if workout_ids:
            WorkoutPerformance.query.filter(
                WorkoutPerformance.workout_id.in_(workout_ids)
            ).delete(synchronize_session=False)
        
        # Delete Performance records
        Performance.query.filter_by(user_id=user_to_delete.id).delete()
        
        # Delete Workout records
        Workout.query.filter_by(user_id=user_to_delete.id).delete()
        
        # Delete UserStatistic records
        UserStatistic.query.filter_by(user_id=user_to_delete.id).delete()
    
        # Finally, delete the user
        db.session.delete(user_to_delete)
        db.session.commit()
        
        flash(f"User {user_to_delete.username} has been successfully deleted.", "success")
        logger(current_user.username, f"Deleted user {user_to_delete.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the user: {str(e)}", "danger")
        
    return redirect(url_for('admin_users'))



@app.route('/admin/reset_password/<int:id>', methods=['POST'])
@login_required
@superuser_required
def reset_user_password(id):
    """Reset user password to default for admin use."""
    user = User.query.get_or_404(id)
    """  if user.is_superuser:
        flash("Non puoi resettare la password di un admin.", "warning")
        return redirect(url_for('admin_users')) """

    user.password = generate_password_hash('seiunpollo')
    db.session.commit()
    flash(f"Password resettata per {user.username}.", "info")
    logger(current_user.id, f"Reset password for {user.username}")
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
            name=form.name.data,
            surname=form.surname.data,
            username=form.username.data,
            email=form.email.data,
            is_superuser=False,
            is_enabled=False,
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        logger(new_user.id, 'New user registered')
        return redirect(url_for('login'))

    # Render the registration template with the form
    return render_template('register.html', form=form)


@app.route('/register/admin', methods=['GET', 'POST'])
def register_admin():
    form = AdminRegistrationForm()

    if current_user.is_authenticated:
        if current_user.is_superuser:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if form.validate_on_submit():
        admin_reg_code = os.getenv('ADMIN_REG_CODE', 'PAZZESCO')
        if (form.admin_code.data or '').strip() != admin_reg_code:
            flash('Codice admin non valido.', 'danger')
            return redirect(url_for('register_admin'))

        existing_username = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()

        if existing_username:
            flash('Username is already taken. Please choose another one.', 'danger')
            return redirect(url_for('register_admin'))

        if existing_email:
            flash('Email is already registered. Please use a different email.', 'danger')
            return redirect(url_for('register_admin'))

        new_admin = User(
            name=form.name.data,
            surname=form.surname.data,
            username=form.username.data,
            email=form.email.data,
            is_superuser=True,
            is_enabled=True,
        )
        new_admin.set_password(form.password.data)
        db.session.add(new_admin)
        db.session.commit()
        logger(new_admin.id, 'New admin registered')
        flash('Admin registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('admin_register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    # Redirect authenticated users to their respective dashboards
    if current_user.is_authenticated:
        if current_user.is_superuser:
            return redirect(url_for('dashboard'))
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
                return redirect(url_for('dashboard'))
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
        # Aggiornamento delle informazioni del profilo
        user.name = form.name.data
        user.surname = form.surname.data
        
        user.username = form.username.data
        if User.query.filter(User.username == form.username.data, User.id != user.id).first():
            flash('Username already taken by another account.', 'danger')
            return redirect(url_for('profile'))
        
        user.email = form.email.data
        if User.query.filter(User.email == form.email.data, User.id != user.id).first():
            flash('Email already in use by another account.', 'danger')
            return redirect(url_for('profile'))

        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Il tuo profilo è stato aggiornato con successo.', 'success')

        return redirect(url_for('profile'))

    elif request.method == 'GET':
        # Precompila il form con i dati dell'utente
        form.name.data = user.name
        form.surname.data = user.surname
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
    workouts = Workout.query.filter(
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

    workouts = Workout.query.filter(
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
            print(parsed)
            for w_data in parsed["workouts"]:
                w = Workout(
                    date=w_data["date"],
                    name=w_data['name'],
                    description="\n".join(w_data["description"]),
                    user_id=current_user.id
                )
                db.session.add(w)
                # Aggiungi i ranges se presenti
                if w_data.get("exercise_range") and w_data.get("ranges"):
                    db.session.flush()  # Ottieni l'ID del workout appena creato
                    for order_index, range_value in enumerate(w_data.get("ranges", [])):
                        r = Range(
                            value=range_value,
                            exercise=w_data.get("exercise_range", ""),
                            order=order_index,
                            workout_id=w.id
                        )
                        db.session.add(r)
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
    WorkoutPerformance.query.filter_by(workout_id=workout.id).delete()
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

    exercises = sorted(
        {
            row[0]
            for row in db.session.query(UserStatistic.exercise)
            .filter_by(user_id=current_user.id)
            .filter(UserStatistic.exercise.isnot(None))
            .distinct()
            .all()
        }
    )

    stats_by_exercise = {}
    user_stats_all = (
        UserStatistic.query.filter_by(user_id=current_user.id)
        .filter(UserStatistic.exercise.isnot(None))
        .order_by(UserStatistic.date.desc())
        .all()
    )
    for s in user_stats_all:
        stats_by_exercise.setdefault(s.exercise, []).append(
            {
                "date": s.date.isoformat() if isinstance(s.date, datetime) else None,
                "weight": s.weight,
                "reps": s.reps,
            }
        )

    workout_performances = (
        WorkoutPerformance.query.filter_by(workout_id=id)
        .order_by(WorkoutPerformance.id.desc())
        .all()
    )

    if form.validate_on_submit():
        perf_date = datetime.combine(form.date.data, datetime.min.time()) if form.date.data else datetime.now()
        perf = Performance(
            date=perf_date,
            description=form.description.data.capitalize(),
            user_id=current_user.id,
        )
        db.session.add(perf)
        db.session.flush()

        link = WorkoutPerformance(workout_id=id, performance_id=perf.id)
        db.session.add(link)
        db.session.commit()
        flash('Performance salvata con successo', 'success')
        logger(current_user.id, 'New performance added')
        return redirect(url_for('add_performance', id=w.id))

    return render_template(
        'add_performance.html',
        title='Add Performance',
        workout=w,
        form=form,
        workout_performances=workout_performances,
        exercises=exercises,
        stats_by_exercise=stats_by_exercise,
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

    links = WorkoutPerformance.query.filter_by(performance_id=id).all()
    workout_id = links[0].workout_id if links else None

    # Allow delete if owner of the performance, superuser, or owner of the linked workout
    workout_owner_id = None
    if workout_id:
        linked_workout = Workout.query.get(workout_id)
        workout_owner_id = linked_workout.user_id if linked_workout else None

    if not (
        perf.user_id == current_user.id
        or current_user.is_superuser
        or (workout_owner_id is not None and workout_owner_id == current_user.id)
    ):
        abort(403)

    for link in links:
        db.session.delete(link)
    db.session.flush() 
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
            reps=1
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
    app.run(debug=DEBUG_MODE)
