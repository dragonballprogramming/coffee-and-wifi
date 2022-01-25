from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

##WTForm
class CafeForm(FlaskForm):
    cafe = StringField('Cafe Name', validators=[DataRequired()])
    cafe_url = StringField('Cafe Image (URL)', validators=[DataRequired(), URL()])
    cafe_address = StringField('Cafe Address', validators=[DataRequired()])
    cafe_city = StringField('Cafe City', validators=[DataRequired()])
    cafe_state = StringField('Cafe State', validators=[DataRequired()])
    cafe_zip = StringField('Cafe Zip', validators=[DataRequired()])
    open_time = StringField('Opening Time e.g. 8AM', validators=[DataRequired()])
    closing_time = StringField('Closing Time e.g. 5:30PM', validators=[DataRequired()])
    coffee_rating = SelectField("Coffee Rating", choices=['☕', '☕☕', '☕☕☕', '☕☕☕☕', '☕☕☕☕☕'],
                                validate_choice=[DataRequired])
    wifi_rating = SelectField("Wifi Rating", choices=["✘", "💪", "💪💪", "💪💪💪", "💪💪💪💪", "💪💪💪💪💪"],
                              validate_choice=[DataRequired])
    power_outlet_rating = SelectField("Power Outlet Rating", choices=[ '🔌', '🔌🔌', '🔌🔌🔌', '🔌🔌🔌🔌', '🔌🔌🔌🔌🔌'],
                                      validate_choice=[DataRequired])
    submit = SubmitField('Submit')

class RegisterUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    name = StringField("User Name", validators=[DataRequired()])
    submit = SubmitField("Register New User")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Post")