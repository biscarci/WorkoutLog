# -*- coding: utf-8 -*-
# Importazioni standard della libreria Python
import click
import csv
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
import hmac
import hashlib
from io import StringIO

# Importazioni di librerie esterne
from flask import Flask, Blueprint, Response, abort, flash, jsonify, redirect, render_template, request, url_for
from flask.cli import with_appcontext
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
import requests, re
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap5
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_
from collections import defaultdict

# Importazioni del progetto locale
from forms import (AddWorkoutForm, AddWeeklyWorkoutForm, AdminRegistrationForm, BulkDeleteStatsForm, DeleteWorkoutsByDayForm, EditPerformanceForm, LoginForm, PerformanceForm,
                   RegistrationForm, UpdateProfileForm, UpdateWorkoutForm, UserStatisticForm)
from utils import (allowed_file, 
                   random_motivational_phrase, random_rest_message, parse_week_text)


from markupsafe import Markup, escape
from flask_migrate import Migrate


app = Flask(__name__)
APP_START_TIME = datetime.now(timezone.utc)

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
    display_order = db.Column(db.Integer, nullable=False, default=0)
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
        """Restituisce i ranges raggruppati per esercizio con i pesi calcolati."""
        ex_ranges = (
            Range.query
            .filter_by(workout_id=self.id)
            .order_by(Range.order.asc(), Range.id.asc())
            .all()
        )
        if not ex_ranges:
            return None

        grouped = {}
        exercise_order = []
        for r in ex_ranges:
            key = r.exercise
            if key not in grouped:
                grouped[key] = []
                exercise_order.append(key)
            grouped[key].append(r)

        groups = []
        for exercise_name in exercise_order:
            ranges_for_ex = grouped[exercise_name]
            specified_exercise = exercise_name.lower().strip()
            user_stat = (
                UserStatistic.query
                .filter(UserStatistic.user_id == current_user.id)
                .filter(func.lower(UserStatistic.exercise) == specified_exercise)
                .order_by(UserStatistic.date.desc(), UserStatistic.id.desc())
                .first()
            )

            formatted_ranges = []
            if user_stat and user_stat.weight:
                for r in ranges_for_ex:
                    weight = round(user_stat.weight * (r.value / 100), 1)
                    formatted_ranges.append(f"{r.value}% @{weight}")

            groups.append({
                'user_exercise': user_stat.exercise if user_stat else None,
                'user_weight': user_stat.weight if user_stat else None,
                'exercise': exercise_name,
                'ranges': formatted_ranges
            })

        return groups

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

def _csv_value(value):
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.isoformat()
    return value

def _format_uptime(start_time, now):
    delta = now - start_time
    total_seconds = max(0, int(delta.total_seconds()))
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

def _get_db_connection_count():
    try:
        pool = db.engine.pool
        if hasattr(pool, "checkedout") and callable(pool.checkedout):
            return pool.checkedout()
        if hasattr(pool, "checkedout"):
            return pool.checkedout
        if hasattr(pool, "status") and callable(pool.status):
            status = pool.status()
            match = re.search(r"Checked out connections: (\\d+)", status)
            if match:
                return int(match.group(1))
    except Exception:
        return None
    return None

def _parse_str(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text != '' else None

def _parse_int(value):
    text = _parse_str(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None

def _parse_float(value):
    text = _parse_str(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None

def _parse_bool(value):
    text = _parse_str(value)
    if text is None:
        return None
    if text.lower() in ('1', 'true', 't', 'yes', 'y'):
        return True
    if text.lower() in ('0', 'false', 'f', 'no', 'n'):
        return False
    return None

def _parse_datetime(value):
    text = _parse_str(value)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None

def _parse_ranges_input(value):
    text = _parse_str(value)
    if text is None:
        return None
    if '@' not in text:
        raise ValueError('Formato ranges non valido. Usa 20@Back Squat oppure 20,30,40@Back Squat.')
    ranges_part, exercise = text.split('@', 1)
    exercise = exercise.strip()
    if not exercise:
        raise ValueError('Formato ranges non valido: esercizio mancante.')
    ranges = []
    for raw_item in ranges_part.split(','):
        raw_item = raw_item.strip()
        if not raw_item:
            continue
        parsed = _parse_int(raw_item)
        if parsed is None:
            raise ValueError(f'Valore range non valido: {raw_item}')
        ranges.append(parsed)
    if not ranges:
        raise ValueError('Nessun range valido trovato.')
    return {"exercise": exercise, "ranges": ranges}


def _get_day_bounds(value):
    target_date = value.date() if isinstance(value, datetime) else value
    start_dt = datetime.combine(target_date, datetime.min.time())
    return start_dt, start_dt + timedelta(days=1)


def _get_next_workout_display_order(workout_date):
    if workout_date is None:
        return 0
    day_start, day_end = _get_day_bounds(workout_date)
    current_max = (
        db.session.query(func.max(Workout.display_order))
        .filter(Workout.date.isnot(None), Workout.date >= day_start, Workout.date < day_end)
        .scalar()
    )
    return (current_max or 0) + 1


def _normalize_workout_display_order_for_day(workout_date):
    if workout_date is None:
        return []
    day_start, day_end = _get_day_bounds(workout_date)
    workouts = (
        Workout.query
        .filter(Workout.date.isnot(None), Workout.date >= day_start, Workout.date < day_end)
        .order_by(Workout.display_order.asc(), Workout.id.asc())
        .all()
    )
    changed = False
    for index, workout in enumerate(workouts, start=1):
        if workout.display_order != index:
            workout.display_order = index
            changed = True
    if changed:
        db.session.commit()
    return workouts

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

    # System Status
    db_connections = _get_db_connection_count()
    if db_connections is None:
        db_connections = 'N/A'
    server_uptime = _format_uptime(APP_START_TIME, datetime.now(timezone.utc))
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
        user=current_user
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


@app.route('/admin/workouts/delete-by-day', methods=['GET', 'POST'])
@login_required
@superuser_required
def admin_delete_workouts_by_day():
    form = DeleteWorkoutsByDayForm()
    day_options = [
        {'code': 'mon', 'short': 'L', 'label': 'Lunedi', 'weekday': 0},
        {'code': 'tue', 'short': 'M', 'label': 'Martedi', 'weekday': 1},
        {'code': 'wed', 'short': 'M', 'label': 'Mercoledi', 'weekday': 2},
        {'code': 'thu', 'short': 'G', 'label': 'Giovedi', 'weekday': 3},
        {'code': 'fri', 'short': 'V', 'label': 'Venerdi', 'weekday': 4},
        {'code': 'sat', 'short': 'S', 'label': 'Sabato', 'weekday': 5},
        {'code': 'sun', 'short': 'D', 'label': 'Domenica', 'weekday': 6},
        {'code': 'all', 'short': 'TUTTI', 'label': 'Tutti i giorni', 'weekday': None},
    ]

    week_date_raw = (request.args.get('week_date') or '').strip()
    if week_date_raw:
        try:
            selected_week_date = datetime.strptime(week_date_raw, '%Y-%m-%d').date()
        except ValueError:
            selected_week_date = datetime.utcnow().date()
    else:
        selected_week_date = datetime.utcnow().date()

    if request.method == 'POST' and form.week_date.data:
        selected_week_date = form.week_date.data

    week_start_date = selected_week_date - timedelta(days=selected_week_date.weekday())
    week_start = datetime.combine(week_start_date, datetime.min.time())
    week_end = week_start + timedelta(days=7)
    form.week_date.data = week_start_date

    week_workouts = (
        Workout.query
        .filter(Workout.date.isnot(None), Workout.date >= week_start, Workout.date < week_end)
        .all()
    )

    if form.validate_on_submit():
        selected_codes = set(request.form.getlist('days'))
        if 'all' in selected_codes:
            selected_codes = {option['code'] for option in day_options if option['weekday'] is not None}

        selected_days = [option for option in day_options if option['weekday'] is not None and option['code'] in selected_codes]
        if not selected_days:
            flash('Seleziona almeno un giorno.', 'warning')
            return redirect(url_for('admin_delete_workouts_by_day', week_date=week_start_date.isoformat()))

        selected_weekdays = {option['weekday'] for option in selected_days}
        workout_ids = [
            workout.id
            for workout in week_workouts
            if workout.date.weekday() in selected_weekdays
        ]

        if not workout_ids:
            flash('Nessun allenamento trovato per i giorni selezionati.', 'info')
            return redirect(url_for('admin_delete_workouts_by_day', week_date=week_start_date.isoformat()))

        try:
            WorkoutPerformance.query.filter(WorkoutPerformance.workout_id.in_(workout_ids)).delete(synchronize_session=False)
            Range.query.filter(Range.workout_id.in_(workout_ids)).delete(synchronize_session=False)
            Workout.query.filter(Workout.id.in_(workout_ids)).delete(synchronize_session=False)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('Errore durante la cancellazione degli allenamenti.', 'danger')
            return redirect(url_for('admin_delete_workouts_by_day', week_date=week_start_date.isoformat()))

        selected_labels = ', '.join(option['label'] for option in selected_days)
        flash(f'{len(workout_ids)} allenamenti eliminati con successo.', 'success')
        logger(current_user.id, f'Bulk deleted workouts for week {week_start_date.isoformat()} and days: {selected_labels}')
        return redirect(url_for('admin_delete_workouts_by_day', week_date=week_start_date.isoformat()))

    if request.method == 'POST':
        flash('Seleziona una data valida.', 'warning')
        return redirect(url_for('admin_delete_workouts_by_day', week_date=week_start_date.isoformat()))

    return render_template(
        'admin_delete_workouts_by_day.html',
        title='Delete Workouts By Day',
        form=form,
        day_options=day_options,
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
    ).order_by(Workout.date.asc(), Workout.display_order.asc(), Workout.id.asc()).all()

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
    ).order_by(Workout.date.asc(), Workout.display_order.asc(), Workout.id.asc()).all()

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


@app.route('/workouts/order', methods=['GET'])
@login_required
@superuser_required
def order_workouts():
    year = request.args.get('year', default=datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.now().month, type=int)
    day = request.args.get('day', default=datetime.now().day, type=int)

    try:
        selected_date = datetime(year, month, day)
    except ValueError:
        selected_date = datetime(year, month, 1)

    workouts = _normalize_workout_display_order_for_day(selected_date.date())

    return render_template(
        'order_workouts.html',
        title='Ordina Workouts',
        workouts=workouts,
        selected_date=selected_date,
    )


@app.route('/workouts/order/move/<int:id>', methods=['POST'])
@login_required
@superuser_required
def move_workout_order(id):
    workout = Workout.query.get_or_404(id)
    if workout.date is None:
        abort(400)

    direction = (_parse_str(request.form.get('direction')) or '').lower()
    workout_date = workout.date.date() if isinstance(workout.date, datetime) else workout.date
    workouts = _normalize_workout_display_order_for_day(workout_date)

    current_index = next((index for index, item in enumerate(workouts) if item.id == workout.id), None)
    if current_index is None:
        abort(404)

    swap_index = None
    if direction == 'up' and current_index > 0:
        swap_index = current_index - 1
    elif direction == 'down' and current_index < len(workouts) - 1:
        swap_index = current_index + 1

    if swap_index is not None:
        other_workout = workouts[swap_index]
        workout.display_order, other_workout.display_order = other_workout.display_order, workout.display_order
        db.session.commit()

    return redirect(
        url_for(
            'order_workouts',
            day=workout_date.day,
            month=workout_date.month,
            year=workout_date.year,
        )
    )

@app.route('/export/csv', methods=['GET'])
@login_required
@superuser_required
def export_csv():
    fieldnames = [
        'table',
        'id',
        'user_id',
        'username',
        'password',
        'email',
        'name',
        'surname',
        'created_at',
        'last_login',
        'is_superuser',
        'is_enabled',
        'total_workouts_added',
        'date',
        'display_order',
        'description',
        'workout_id',
        'performance_id',
        'value',
        'exercise',
        'range_order',
        'weight',
        'reps',
        'action',
        'timestamp',
        'log_user',
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()

    def write_row(table, **data):
        row = {name: '' for name in fieldnames}
        row['table'] = table
        for key, value in data.items():
            row[key] = _csv_value(value)
        writer.writerow(row)

    for user in User.query.order_by(User.id.asc()).all():
        write_row(
            'user',
            id=user.id,
            user_id=user.id,
            username=user.username,
            password=user.password,
            email=user.email,
            name=user.name,
            surname=user.surname,
            created_at=user.created_at,
            last_login=user.last_login,
            is_superuser=user.is_superuser,
            is_enabled=user.is_enabled,
            total_workouts_added=user.total_workouts_added,
        )

    for workout in Workout.query.order_by(Workout.id.asc()).all():
        write_row(
            'workout',
            id=workout.id,
            user_id=workout.user_id,
            date=workout.date,
            display_order=workout.display_order,
            name=workout.name,
            description=workout.description,
        )

    for r in Range.query.order_by(Range.id.asc()).all():
        write_row(
            'range',
            id=r.id,
            user_id=r.workout.user_id if r.workout else None,
            workout_id=r.workout_id,
            value=r.value,
            exercise=r.exercise,
            range_order=r.order,
        )

    for performance in Performance.query.order_by(Performance.id.asc()).all():
        write_row(
            'performance',
            id=performance.id,
            user_id=performance.user_id,
            date=performance.date,
            description=performance.description,
        )

    for link in WorkoutPerformance.query.order_by(WorkoutPerformance.id.asc()).all():
        workout_user_id = link.workout.user_id if link.workout else None
        write_row(
            'workout_performance',
            id=link.id,
            user_id=workout_user_id,
            workout_id=link.workout_id,
            performance_id=link.performance_id,
        )

    for stat in UserStatistic.query.order_by(UserStatistic.id.asc()).all():
        write_row(
            'user_statistic',
            id=stat.id,
            user_id=stat.user_id,
            date=stat.date,
            exercise=stat.exercise,
            weight=stat.weight,
            reps=stat.reps,
        )

    logger(current_user.id, 'CSV export')
    filename = f"workoutlog_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@app.route('/import/csv', methods=['POST'])
@login_required
@superuser_required
def import_csv():
    file = request.files.get('csv_file')
    if not file or not file.filename:
        flash('Seleziona un file CSV da importare.', 'warning')
        return redirect(url_for('dashboard'))

    try:
        content = file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        flash('Impossibile leggere il CSV: encoding non supportato.', 'danger')
        return redirect(url_for('dashboard'))

    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames or 'table' not in reader.fieldnames:
        flash('CSV non valido: manca la colonna "table".', 'danger')
        return redirect(url_for('dashboard'))

    rows_by_table = {}
    for row in reader:
        table = _parse_str(row.get('table'))
        if not table:
            continue
        rows_by_table.setdefault(table.lower(), []).append(row)

    counts = {
        'user': 0,
        'workout': 0,
        'range': 0,
        'performance': 0,
        'workout_performance': 0,
        'user_statistic': 0,
        'log': 0,
    }
    skipped = 0
    user_id_map = {}
    workout_id_map = {}
    performance_id_map = {}

    try:
        # Import order matters for foreign keys.
        for row in rows_by_table.get('user', []):
            user_id = _parse_int(row.get('id'))
            if user_id is None:
                skipped += 1
                continue

            username = _parse_str(row.get('username'))
            email = _parse_str(row.get('email'))
            password = _parse_str(row.get('password'))

            existing_by_username = None
            if username is not None:
                existing_by_username = User.query.filter(User.username == username).first()
            existing_by_email = None
            if email is not None:
                existing_by_email = User.query.filter(User.email == email).first()

            if existing_by_username and existing_by_email and existing_by_username.id != existing_by_email.id:
                skipped += 1
                continue

            existing_user = existing_by_username or existing_by_email
            if existing_user and existing_user.id != user_id:
                user_id_map[user_id] = existing_user.id
                skipped += 1
                continue

            user = db.session.get(User, user_id)
            is_new = user is None
            if user is None:
                user = User(id=user_id)
            if is_new and (not username or not email or not password):
                skipped += 1
                continue

            name = _parse_str(row.get('name'))
            surname = _parse_str(row.get('surname'))
            created_at = _parse_datetime(row.get('created_at'))
            last_login = _parse_datetime(row.get('last_login'))
            is_superuser = _parse_bool(row.get('is_superuser'))
            is_enabled = _parse_bool(row.get('is_enabled'))
            total_workouts_added = _parse_int(row.get('total_workouts_added'))

            if (
                not is_new
                and (username is None or user.username == username)
                and (email is None or user.email == email)
                and (password is None or user.password == password)
                and (name is None or user.name == name)
                and (surname is None or user.surname == surname)
                and (created_at is None or user.created_at == created_at)
                and (last_login is None or user.last_login == last_login)
                and (is_superuser is None or user.is_superuser == is_superuser)
                and (is_enabled is None or user.is_enabled == is_enabled)
                and (total_workouts_added is None or user.total_workouts_added == total_workouts_added)
            ):
                user_id_map[user_id] = user.id
                skipped += 1
                continue

            if username is not None:
                user.username = username
            if email is not None:
                user.email = email
            if password is not None:
                user.password = password
            if name is not None:
                user.name = name
            if surname is not None:
                user.surname = surname
            if created_at is not None:
                user.created_at = created_at
            if last_login is not None:
                user.last_login = last_login
            if is_superuser is not None:
                user.is_superuser = is_superuser
            if is_enabled is not None:
                user.is_enabled = is_enabled
            if total_workouts_added is not None:
                user.total_workouts_added = total_workouts_added

            db.session.add(user)
            user_id_map[user_id] = user.id
            counts['user'] += 1

        for row in rows_by_table.get('workout', []):
            workout_id = _parse_int(row.get('id'))
            user_id = _parse_int(row.get('user_id'))
            if user_id is not None:
                user_id = user_id_map.get(user_id, user_id)
            name = _parse_str(row.get('name'))
            workout_date = _parse_datetime(row.get('date'))
            display_order = _parse_int(row.get('display_order'))
            workout_description = _parse_str(row.get('description'))
            if workout_id is None or user_id is None or not name:
                skipped += 1
                continue
            existing_duplicate = (
                Workout.query
                .filter(
                    Workout.user_id == user_id,
                    Workout.date == workout_date,
                    Workout.name == name,
                    Workout.description == workout_description,
                )
                .first()
            )
            if existing_duplicate is not None:
                workout_id_map[workout_id] = existing_duplicate.id
                skipped += 1
                continue
            workout = db.session.get(Workout, workout_id)
            if workout is None:
                workout = Workout(id=workout_id)
            workout.user_id = user_id
            workout.name = name
            workout.date = workout_date
            workout.display_order = display_order if display_order is not None else workout.display_order or 0
            workout.description = workout_description
            db.session.add(workout)
            workout_id_map[workout_id] = workout.id
            counts['workout'] += 1

        for row in rows_by_table.get('range', []):
            range_id = _parse_int(row.get('id'))
            workout_id = _parse_int(row.get('workout_id'))
            if workout_id is not None:
                workout_id = workout_id_map.get(workout_id, workout_id)
            value = _parse_int(row.get('value'))
            exercise = _parse_str(row.get('exercise'))
            range_order = _parse_int(row.get('range_order'))
            if range_id is None or workout_id is None or value is None or not exercise or range_order is None:
                skipped += 1
                continue
            existing_duplicate = (
                Range.query
                .filter(
                    Range.workout_id == workout_id,
                    Range.value == value,
                    Range.exercise == exercise,
                    Range.order == range_order,
                )
                .first()
            )
            if existing_duplicate is not None:
                skipped += 1
                continue
            r = db.session.get(Range, range_id)
            if r is None:
                r = Range(id=range_id)
            r.workout_id = workout_id
            r.value = value
            r.exercise = exercise
            r.order = range_order
            db.session.add(r)
            counts['range'] += 1

        for row in rows_by_table.get('performance', []):
            performance_id = _parse_int(row.get('id'))
            user_id = _parse_int(row.get('user_id'))
            if user_id is not None:
                user_id = user_id_map.get(user_id, user_id)
            performance_date = _parse_datetime(row.get('date'))
            performance_description = _parse_str(row.get('description'))
            if performance_id is None or user_id is None:
                skipped += 1
                continue
            existing_duplicate = (
                Performance.query
                .filter(
                    Performance.user_id == user_id,
                    Performance.date == performance_date,
                    Performance.description == performance_description,
                )
                .first()
            )
            if existing_duplicate is not None:
                performance_id_map[performance_id] = existing_duplicate.id
                skipped += 1
                continue
            performance = db.session.get(Performance, performance_id)
            if performance is None:
                performance = Performance(id=performance_id)
            performance.user_id = user_id
            performance.date = performance_date
            performance.description = performance_description
            db.session.add(performance)
            performance_id_map[performance_id] = performance.id
            counts['performance'] += 1

        for row in rows_by_table.get('workout_performance', []):
            link_id = _parse_int(row.get('id'))
            workout_id = _parse_int(row.get('workout_id'))
            if workout_id is not None:
                workout_id = workout_id_map.get(workout_id, workout_id)
            performance_id = _parse_int(row.get('performance_id'))
            if performance_id is not None:
                performance_id = performance_id_map.get(performance_id, performance_id)
            if link_id is None or workout_id is None or performance_id is None:
                skipped += 1
                continue
            existing_duplicate = (
                WorkoutPerformance.query
                .filter(
                    WorkoutPerformance.workout_id == workout_id,
                    WorkoutPerformance.performance_id == performance_id,
                )
                .first()
            )
            if existing_duplicate is not None:
                skipped += 1
                continue
            link = db.session.get(WorkoutPerformance, link_id)
            if link is None:
                link = WorkoutPerformance(id=link_id)
            link.workout_id = workout_id
            link.performance_id = performance_id
            db.session.add(link)
            counts['workout_performance'] += 1

        for row in rows_by_table.get('user_statistic', []):
            stat_id = _parse_int(row.get('id'))
            user_id = _parse_int(row.get('user_id'))
            if user_id is not None:
                user_id = user_id_map.get(user_id, user_id)
            stat_date = _parse_datetime(row.get('date'))
            stat_exercise = _parse_str(row.get('exercise'))
            stat_weight = _parse_float(row.get('weight'))
            stat_reps = _parse_int(row.get('reps'))
            if stat_id is None or user_id is None:
                skipped += 1
                continue
            existing_duplicate = (
                UserStatistic.query
                .filter(
                    UserStatistic.user_id == user_id,
                    UserStatistic.date == stat_date,
                    UserStatistic.exercise == stat_exercise,
                    UserStatistic.weight == stat_weight,
                    UserStatistic.reps == stat_reps,
                )
                .first()
            )
            if existing_duplicate is not None:
                skipped += 1
                continue
            stat = db.session.get(UserStatistic, stat_id)
            if stat is None:
                stat = UserStatistic(id=stat_id)
            stat.user_id = user_id
            stat.date = stat_date
            stat.exercise = stat_exercise
            stat.weight = stat_weight
            stat.reps = stat_reps
            db.session.add(stat)
            counts['user_statistic'] += 1

        for row in rows_by_table.get('log', []):
            log_id = _parse_int(row.get('id'))
            if log_id is None:
                skipped += 1
                continue
            log_user = _parse_str(row.get('log_user')) or _parse_str(row.get('username'))
            log_action = _parse_str(row.get('action'))
            log_timestamp = _parse_datetime(row.get('timestamp'))
            existing_duplicate = (
                Log.query
                .filter(
                    Log.user == log_user,
                    Log.action == log_action,
                    Log.timestamp == log_timestamp,
                )
                .first()
            )
            if existing_duplicate is not None:
                skipped += 1
                continue
            log_entry = db.session.get(Log, log_id)
            if log_entry is None:
                log_entry = Log(id=log_id)
            log_entry.user = log_user
            log_entry.action = log_action
            log_entry.timestamp = log_timestamp
            db.session.add(log_entry)
            counts['log'] += 1

        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        flash(f'Errore durante import CSV: {exc}', 'danger')
        return redirect(url_for('dashboard'))

    logger(current_user.id, 'CSV import')
    flash(
        'Import CSV completato '
        f"(user {counts['user']}, workout {counts['workout']}, range {counts['range']}, "
        f"performance {counts['performance']}, link {counts['workout_performance']}, "
        f"stats {counts['user_statistic']}, log {counts['log']}, skipped {skipped} tra duplicati o righe non valide).",
        'success'
    )
    return redirect(url_for('dashboard'))


@app.route('/workout/add', methods=['GET', 'POST'])
@login_required
def add_workout():
    form = AddWorkoutForm()

    if form.validate_on_submit():

        payloads = []

        for field in (form.ranges1, form.ranges2, form.ranges3):
            raw = _parse_str(field.data)
            if raw:
                try:
                    payloads.append(_parse_ranges_input(raw))
                except ValueError as exc:
                    flash(str(exc), 'danger')
                    return render_template(
                        'add_workout.html',
                        title='Add Workout',
                        user=current_user,
                        form=form
                    )

        w = Workout(
            date=form.date.data,
            display_order=_get_next_workout_display_order(form.date.data),
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id
        )

        current_user.total_workouts_added += 1
        db.session.add(w)
        db.session.flush()  # serve per ottenere w.id

        order_index = 0
        for payload in payloads:
            for value in payload["ranges"]:
                db.session.add(Range(
                    value=value,
                    exercise=payload["exercise"],
                    order=order_index,
                    workout_id=w.id
                ))
                order_index += 1

        db.session.commit()

        flash('Workout inserito con successo!', 'success')
        logger(current_user.id, 'New workout created')
        return redirect(url_for('dashboard'))

    return render_template(
        'add_workout.html',
        title='Add Workout',
        user=current_user,
        form=form
    )

@app.route('/workout/week/add', methods=['GET', 'POST'])
@login_required
def add_weekly_workouts():
    form = AddWeeklyWorkoutForm()


    if form.validate_on_submit():
        try:
            parsed = parse_week_text(form.week_text.data)
            next_orders = {}
            for w_data in parsed["workouts"]:
                workout_date = w_data["date"]
                date_key = workout_date.isoformat() if workout_date else None
                if date_key not in next_orders:
                    next_orders[date_key] = _get_next_workout_display_order(workout_date)
                w = Workout(
                    date=workout_date,
                    display_order=next_orders[date_key],
                    name=w_data['name'],
                    description="\n".join(w_data["description"]),
                    user_id=current_user.id
                )
                next_orders[date_key] += 1
                db.session.add(w)
                # Aggiungi i ranges se presenti
                range_groups = w_data.get("range_groups") or []
                if range_groups:
                    db.session.flush()  # Ottieni l'ID del workout appena creato
                    for group_index, group in enumerate(range_groups):
                        exercise_name = group.get("exercise")
                        ranges_values = group.get("ranges") or []
                        if not exercise_name or not ranges_values:
                            continue
                        for order_index, range_value in enumerate(ranges_values):
                            r = Range(
                                value=range_value,
                                exercise=exercise_name,
                                order=group_index * 100 + order_index,  # mantieni l'ordine tra gruppi
                                workout_id=w.id
                            )
                            db.session.add(r)
                elif w_data.get("exercise_range") and w_data.get("ranges"):
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
            logger(current_user.id, 'Weekly workouts created'+'\n---'+ form.week_text.data +'\n---')
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

        payloads = []

        for field in (form.ranges1, form.ranges2, form.ranges3):
            raw = _parse_str(field.data)
            if raw:
                try:
                    payloads.append(_parse_ranges_input(raw))
                except ValueError as exc:
                    flash(str(exc), 'danger')
                    return render_template(
                        'edit_workout.html',
                        title='Edit Workout',
                        form=form,
                        workout=w
                    )

        # aggiorna campi base
        previous_date = w.date.date() if isinstance(w.date, datetime) else w.date
        new_date = form.date.data
        if previous_date != new_date:
            w.display_order = _get_next_workout_display_order(new_date)
        w.date = new_date
        w.name = form.name.data
        w.description = form.description.data

        # cancella tutti i range esistenti
        Range.query.filter_by(workout_id=w.id).delete(
            synchronize_session=False
        )

        # reinserisci i range
        order_index = 0
        for payload in payloads:
            for value in payload["ranges"]:
                db.session.add(Range(
                    value=value,
                    exercise=payload["exercise"],
                    order=order_index,
                    workout_id=w.id
                ))
                order_index += 1

        db.session.commit()

        flash('Workout aggiornato con successo!', 'success')
        logger(current_user.id, f'Modified workout {w.date:%d-%m-%Y}')
        return redirect(url_for('dashboard'))

    elif request.method == 'GET':

        form.date.data = w.date
        form.name.data = w.name
        form.description.data = w.description

        # ricostruisci i campi ranges
        grouped = defaultdict(list)
        for r in w.ranges:
            grouped[r.exercise].append((r.order, r.value))

        reconstructed = []
        for exercise, items in grouped.items():
            items.sort(key=lambda x: x[0])
            values = [str(v) for _, v in items]
            reconstructed.append(f"{','.join(values)}@{exercise}")

        form.ranges1.data = reconstructed[0] if len(reconstructed) > 0 else ''
        form.ranges2.data = reconstructed[1] if len(reconstructed) > 1 else ''
        form.ranges3.data = reconstructed[2] if len(reconstructed) > 2 else ''

    return render_template(
        'edit_workout.html',
        title='Edit Workout',
        form=form,
        workout=w
    )
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

    subquery = (
        db.session.query(
            UserStatistic.exercise,
            func.max(UserStatistic.date).label('max_date')
        )
        .filter(UserStatistic.user_id == current_user.id)
        .group_by(UserStatistic.exercise)
        .subquery()
    )

    stats = (
        UserStatistic.query
        .join(
            subquery,
            and_(
                UserStatistic.exercise == subquery.c.exercise,
                UserStatistic.date == subquery.c.max_date
            )
        )
        .filter(UserStatistic.user_id == current_user.id)
        .order_by(UserStatistic.date.desc())
        .all()
    )

    exercises = [s.exercise for s in stats if s.exercise is not None]
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
        max_weight=max_weight,
        max_reps=max_reps,
    )


@app.route('/stats/history/<path:exercise>', methods=['GET'])
@login_required
def stat_history(exercise):
    specified_exercise = (exercise or '').strip().lower()
    if not specified_exercise:
        abort(404)

    delete_form = BulkDeleteStatsForm()

    stats = (
        UserStatistic.query.filter_by(user_id=current_user.id)
        .filter(func.lower(UserStatistic.exercise) == specified_exercise)
        .order_by(UserStatistic.date.asc())
        .all()
    )

    valid_stats = [s for s in stats if s.date is not None and s.weight is not None]
    display_exercise = stats[0].exercise if stats else exercise

    first_entry = valid_stats[0] if valid_stats else None
    last_entry = valid_stats[-1] if valid_stats else None
    best_entry = max(valid_stats, key=lambda s: s.weight) if valid_stats else None
    delta = None
    if first_entry and last_entry:
        try:
            delta = round(last_entry.weight - first_entry.weight, 2)
        except TypeError:
            delta = None

    return render_template(
        'stat_history.html',
        title='Stat History',
        exercise=display_exercise,
        stats=list(reversed(valid_stats)),
        delete_form=delete_form,
        first_entry=first_entry,
        last_entry=last_entry,
        best_entry=best_entry,
        delta=delta,
    )


@app.route('/api/stats/history/<path:exercise>', methods=['GET'])
@login_required
def stat_history_api(exercise):
    specified_exercise = (exercise or '').strip().lower()
    if not specified_exercise:
        abort(404)

    stats = (
        UserStatistic.query.filter_by(user_id=current_user.id)
        .filter(func.lower(UserStatistic.exercise) == specified_exercise)
        .order_by(UserStatistic.date.asc())
        .all()
    )

    points = []
    for s in stats:
        if s.date is None or s.weight is None:
            continue
        points.append(
            {
                "date": s.date.isoformat(),
                "label": s.date.strftime('%d/%m/%y'),
                "weight": s.weight,
                "reps": s.reps,
            }
        )

    display_exercise = stats[0].exercise if stats else exercise
    return jsonify({"exercise": display_exercise, "points": points})


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
        db.session.commit()
        flash('Statistica aggiornata', 'success')
        logger(current_user.id, 'User stats updated')
        return redirect(url_for('user_stats'))

    if request.method == 'GET':
        form.date.data = stat.date
        form.exercise.data = stat.exercise
        form.weight.data = stat.weight
        

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
