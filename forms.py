# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, FloatField, SubmitField, DateField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, Email
from flask_wtf.file import FileAllowed
from datetime import datetime


# Form di registrazione
class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    surname = StringField('Surname', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Length(min=2, max=200)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Conferma Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class AdminRegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    surname = StringField('Surname', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=2, max=200)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Conferma Password', validators=[DataRequired(), EqualTo('password')])
    admin_code = StringField('Codice Admin', validators=[DataRequired(), Length(min=1, max=50)])
    submit = SubmitField('Register')



# Form di login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Form per Workout
class WorkoutForm(FlaskForm):
    date       = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    name       = StringField(('Name'), validators=[DataRequired(), Length(min=2, max=150)])
    ranges1     = StringField(('Ranges1 (e.g., 50,60,70@Back Squat)'), validators=[Optional(), Length(min=2, max=100)])
    ranges2     = StringField(('Ranges2 (e.g., 50,60,70@Front Squat)'), validators=[Optional(), Length(min=2, max=100)])
    ranges3     = StringField(('Ranges3 (e.g., 50,60,70@Bench Press)'), validators=[Optional(), Length(min=2, max=100)])
    description= TextAreaField(('Description'), validators=[Optional()])
   
# Form per l'aggiornamento dell'esercizio
class UpdateWorkoutForm(WorkoutForm):
    submit     = SubmitField('Update')


# Form per l'aggiornamento dell'esercizio
class AddWorkoutForm(WorkoutForm):
    submit     = SubmitField('Add')


class AddWeeklyWorkoutForm(FlaskForm):
    week_text = TextAreaField(('Write Weekly Workouts'), validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Import')

class PerformanceForm(FlaskForm):
    date = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    description = TextAreaField(('Description'), validators=[DataRequired(), Length(min=2, max=200)])
    submit = SubmitField('Add')

class EditPerformanceForm(FlaskForm):
    date = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    description = TextAreaField(('Description'), validators=[DataRequired(), Length(min=2, max=200)])
    submit = SubmitField('Edit')

movement_choices = [
    ('Back Squat', 'Back Squat'),
    ('Front Squat', 'Front Squat'),
    ('Deadlift', 'Deadlift'),
    ('Bench Press', 'Bench Press'),
    ('Dips', 'Dips'),
    ('Clean & Jerk', 'Clean & Jerk'),
    ('Power Clean', 'Power Clean'),
    ('Squat Clean', 'Squat Clean'),
    ('Power Snatch', 'Power Snatch'),
    ('Squat Snatch', 'Squat Snatch'),
    ('Thruster', 'Thruster'),
    ('Push Press', 'Push Press'),
    ('Push Jerk', 'Push Jerk'),
    ('Split Jerk', 'Split Jerk'),
    # ('Pull-Up Strict', 'Pull-Up Strict'),
    # ('Chest To Bar', 'Chest To Bar'),
    # ('Ring Muscle-Up', 'Ring Muscle-Up'),
    # ('Bar Muscle-Up', 'Bar Muscle-Up'),
    # ('Handstand Push-Up Strict', 'Handstand Push-Up Strict'),
    # ('Handstand Walk', 'Handstand Walk'),
    # ('Ring Dip Strict', 'Ring Dip Strict'),
    # ('Toes To Bar', 'Toes To Bar'),
]

class ExerciseCatalogForm(FlaskForm):
    name = StringField('Nome esercizio', validators=[DataRequired(), Length(min=2, max=100)])
    unit = SelectField(
        'Unita',
        choices=[
            ('kg', 'Kg - massimale di forza'),
            ('reps', 'Reps - ripetizioni'),
            ('min', 'Tempo - test a cronometro'),
            ('pace', 'Pace - min per distanza'),
            ('distance', 'Distanza - metri'),
            ('cal', 'Calorie'),
        ],
        default='kg', validators=[DataRequired()])
    ref_distance = IntegerField('Distanza di riferimento (m)', validators=[Optional()])
    pct_mode = SelectField(
        'Lettura della percentuale',
        choices=[
            ('intensity', 'Intensita: 85% = piu lento / piu facile'),
            ('literal', 'Letterale: 85% = valore x 0,85'),
        ],
        default='literal', validators=[DataRequired()])
    submit = SubmitField('Salva')

    def validate_ref_distance(self, field):
        if self.unit.data == 'pace' and not field.data:
            raise ValidationError('Per il pace serve la distanza di riferimento (es. 500).')
        if field.data is not None and field.data <= 0:
            raise ValidationError('La distanza deve essere positiva.')


class DeleteExerciseForm(FlaskForm):
    submit = SubmitField('Elimina')


class UserStatisticForm(FlaskForm):
    date = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    exercise = SelectField("Exercise", choices=movement_choices, validators=[DataRequired()])
    weight = StringField('Weight (Kg) / Reps / Minuti', validators=[Optional()])
    #reps = IntegerField('Reps', validators=[Optional()], default=1)
    submit = SubmitField('Save')

    # Unita' dell'esercizio selezionato: la imposta la vista prima di validare
    unit = 'kg'

    def set_unit(self, unit):
        self.unit = unit or 'kg'

    def validate_weight(self, field):
        """Interpreta il valore secondo l'unita' dell'esercizio.

        Per i tempi accetta 8:30 e 8.5 (entrambi 8 minuti e mezzo), ma rifiuta
        8.30: somiglia troppo a un orario e verrebbe salvato come 8'18",
        sbagliando in silenzio tutte le percentuali.
        """
        raw = (field.data or '').strip().replace(',', '.')
        if not raw:
            field.data = None
            return

        if self.unit in ('min', 'pace'):
            if ':' in raw:
                minutes, _, seconds = raw.partition(':')
                if not minutes.strip().isdigit() or not seconds.strip().isdigit():
                    raise ValidationError("Formato non valido. Usa mm:ss (es. 1:45) oppure i minuti decimali.")
                seconds_value = int(seconds.strip())
                if seconds_value >= 60:
                    raise ValidationError('I secondi devono essere inferiori a 60.')
                field.data = int(minutes.strip()) + seconds_value / 60
                return

            try:
                value = float(raw)
            except ValueError:
                raise ValidationError("Formato non valido. Usa mm:ss (es. 1:45) oppure i minuti decimali.")

            # La parte decimale oltre .59 non puo' essere una lettura oraria,
            # quindi e' sicuramente gia' un decimale valido.
            decimals = raw.split('.')[1] if '.' in raw else ''
            if len(decimals) == 2 and int(decimals) < 60:
                raise ValidationError(
                    f"Ambiguo: per {raw.split('.')[0]} minuti e {decimals} secondi scrivi "
                    f"{raw.replace('.', ':')}, per i decimali usa un solo decimale."
                )
            if value < 0:
                raise ValidationError("Il valore non puo' essere negativo.")
            field.data = value
            return

        try:
            value = float(raw)
        except ValueError:
            raise ValidationError('Inserisci un numero valido.')
        if value < 0:
            raise ValidationError("Il valore non puo' essere negativo.")
        field.data = value

    def set_exercise_choices(self, choices):
        """Popola la tendina con il catalogo esercizi gestito dal coach.

        Mantiene il valore gia' selezionato anche se l'esercizio e' stato nel
        frattempo disattivato, per non invalidare la modifica di uno storico.
        """
        choices = list(choices) if choices else list(movement_choices)
        current = self.exercise.data
        if current and current not in [c[0] for c in choices]:
            choices.append((current, current))
        self.exercise.choices = choices


class BulkDeleteStatsForm(FlaskForm):
    submit = SubmitField('Delete Selected')


class DeleteWorkoutsByDayForm(FlaskForm):
    week_date = DateField('Picker selezione data', validators=[DataRequired()], default=datetime.utcnow)
    submit = SubmitField('Elimina')


class UpdateProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    surname = StringField('Surname', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password')])

    submit = SubmitField('Update')
