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

class UserStatisticForm(FlaskForm):
    date = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    exercise = SelectField("Exercise", choices= movement_choices, validators=[DataRequired()])
    weight = FloatField('Weight (Kg) / Reps', validators=[Optional()])
    #reps = IntegerField('Reps', validators=[Optional()], default=1)
    submit = SubmitField('Save')


class BulkDeleteStatsForm(FlaskForm):
    submit = SubmitField('Delete Selected')


class UpdateProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    surname = StringField('Surname', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password')])

    submit = SubmitField('Update')
