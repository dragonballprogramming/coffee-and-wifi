import os
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from functools import wraps
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from forms import CafeForm, RegisterUserForm, LoginForm , CommentForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
import requests
from flask_googlemaps import get_address, get_coordinates, GoogleMaps, Map

MY_API_KEY_GOOGLE_MAPS = os.environ.get("API_GOOGLE_MAPS")
app = Flask(__name__)
GoogleMaps(app, key=MY_API_KEY_GOOGLE_MAPS)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap(app)
ckeditor = CKEditor(app)


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

#Login manager
login_manager = LoginManager()
login_manager.init_app(app)

##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#loads a user when logged in
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

logged_in = False

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #if id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


# DB Tabls
#users db
class Users(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    posts = relationship("Cafe", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
db.create_all()

##Cafe TABLE Configuration
class Cafe(db.Model):
    __tablename__ = "cafe"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    author = db.relationship("Users")
    cafe = db.Column(db.String(250), unique=True, nullable=False)
    cafe_url = db.Column(db.String(500), nullable=False)
    cafe_city = db.Column(db.String(500), nullable=False)
    cafe_state = db.Column(db.String(500), nullable=False)
    cafe_zip = db.Column(db.String(500), nullable=False)
    cafe_address = db.Column(db.String(500), nullable=False)
    open_time = db.Column(db.String(500), nullable=False)
    closing_time = db.Column(db.String(500), nullable=False)
    coffee_rating = db.Column(db.String(500), nullable=False)
    wifi_rating = db.Column(db.String(500), nullable=False)
    power_outlet_rating = db.Column(db.String(500), nullable=False)

    # ********************Parent Relationship************************#
    comments = relationship("Comment", back_populates="parent_post")

db.create_all()

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    comment_author = relationship("Users", back_populates="comments")

    #******************Child Relationship*********************#
    post_id = db.Column(db.Integer, db.ForeignKey("cafe.id"))
    parent_post = relationship("Cafe", back_populates="comments")
    text = db.Column(db.Text, nullable=False)
db.create_all()


#uses dictoinary comprehension to create dictionary from random cafe
def to_dict(self):
    return {column.name: getattr(self, column.name) for column in self.__table__.columns}

# all Flask routes below
@app.route("/", methods=["GET", "POST"])
def home():
    all_cafes = Cafe.query.all()
    return render_template("index.html", cafes=all_cafes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterUserForm()
    if form.validate_on_submit():
        email = form.email.data
        user = Users.query.filter_by(email=email).first()
        if user:
            flash("You are already signed up with this email. Login In!")
        else:
            hash_salted_pw = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = Users(
                email=form.email.data,
                password=hash_salted_pw,
                name=form.name.data,
            )
            db.session.add(new_user)
            db.session.commit()
            user = Users.query.filter_by(password=hash_salted_pw).first()
            print(user)
            login_user(user)
            return redirect(url_for('home'))
    return render_template("register.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        user = Users.query.filter_by(email=email).first()
        if user:
            hashed_pw = check_password_hash(pwhash=user.password,
                                           password=form.password.data)
            if hashed_pw:
                print(user)
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash("incorrect password please try again")
        else:
            flash("This email is not in our data base please register or login with another email.")
    return render_template("login.html", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/cafe/<int:cafe_id>', methods=["GET", "POST"])
def cafe(cafe_id):
    form = CommentForm()
    requested_post = Cafe.query.get(cafe_id)
    author_name = Users.query.get(requested_post.author_id)
    post_comments = Comment.query.all()
    lat_lng = get_coordinates(MY_API_KEY_GOOGLE_MAPS, f"{requested_post.cafe} {requested_post.cafe_city} {requested_post.cafe_zip}")
    lat = lat_lng['lat']
    lng = lat_lng['lng']
    print(lat, lng)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You must be logged in to a valid account to make posts please register or login")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=form.comment.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()

        return render_template("cafe_page.html", post=requested_post, author=author_name.name, form=form,
                               post_comments=post_comments, post_id=cafe_id, YOUR_API_KEY=MY_API_KEY_GOOGLE_MAPS, lat_long=lat_lng)

    return render_template("cafe_page.html", post=requested_post, author=author_name.name, form=form,
                           post_comments=post_comments, post_id=cafe_id, YOUR_API_KEY=MY_API_KEY_GOOGLE_MAPS,  lat_long=lat_lng)

@app.route('/add', methods=["GET", "POST"])
@login_required
def add_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        print(current_user.id)
        #create new record
        new_cafe = Cafe(
            author_id=current_user.id,
            cafe=request.form.get('cafe'),
            cafe_url=request.form.get('cafe_url'),
            cafe_address=request.form.get('cafe_address'),
            cafe_state=request.form.get('cafe_state'),
            cafe_city=request.form.get('cafe_city'),
            cafe_zip=request.form.get('cafe_zip'),
            open_time=request.form.get('open_time'),
            closing_time=request.form.get('closing_time'),
            coffee_rating=request.form.get('coffee_rating'),
            wifi_rating=request.form.get('wifi_rating'),
            power_outlet_rating=request.form.get('power_outlet_rating'),
        )
        print(new_cafe)
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
