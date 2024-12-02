# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, FloatField, SubmitField, DateField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, Email
from flask_wtf.file import FileAllowed
from datetime import datetime


# Form di registrazione
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Length(min=2, max=200)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Conferma Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrati')



# Form di login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Form per il caricamento dell'immagine
class UploadForm(FlaskForm):
    image = FileField('Carica un\'immagine', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Solo immagini!')])
    submit = SubmitField('Carica e Processa')

# Form per Workout
class WorkoutForm(FlaskForm):
    date       = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    type       = StringField(('Type'), validators=[Optional()])
    duration   = StringField(('Duration'), validators=[Optional()])
    note       = StringField(('Note'), validators=[Optional()])
   
# Form per l'aggiornamento dell'esercizio
class UpdateWorkoutForm(WorkoutForm):
    submit     = SubmitField('Update')


# Form per l'aggiornamento dell'esercizio
class AddWorkoutForm(WorkoutForm):
    submit     = SubmitField('Add')

class ExerciseForm(FlaskForm):
    choicesOptions =['', 'Barbell', 'Bumbell', 'Kettlebell', 'Sandbag', 'Row', 'Skyerg', 'Bike']

    name = StringField(('Name'), validators=[Optional()])
    repetitions = StringField(('Repetitions'), default=None, validators=[Optional()])
    note = StringField(('Note'), validators=[Optional()])
    weight     = FloatField(('Weight'), default=0, validators=[Optional()])
    equipment  = SelectField(('Equipment'), choices=choicesOptions, validators=[Optional()])
    score      = StringField(('Score'), validators=[Optional()])


# Form per l'aggiornamento dell'esercizio
class UpdateExerciseForm(ExerciseForm):
    submit     = SubmitField('Update')


# Form per l'aggiornamento dell'esercizio
class AddExerciseForm(ExerciseForm):
    submit     = SubmitField('Add')


class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Nuova Password', validators=[Optional()])
    confirm_password = PasswordField('Conferma Password', validators=[Optional(), EqualTo('password')])
    unlock_code = StringField('Unlock Profile', validators=[Optional()])

    submit = SubmitField('Aggiorna Profilo')

