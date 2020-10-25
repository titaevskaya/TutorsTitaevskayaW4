import os
import json
import random
from flask import Flask, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired, AnyOf, Length
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, RadioField
from flask_migrate import Migrate
from sqlalchemy.exc import ProgrammingError

app = Flask(__name__)
# Настраиваем приложение
app.config["DEBUG"] = True
# - URL доступа к БД берем из переменной окружения DATABASE_URL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'my-super-secret-phrase-I-dont-tell-this-to-nobody'

# Создаем подключение к БД
db = SQLAlchemy(app)
# Создаем объект поддержки миграций
migrate = Migrate(app, db)


class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    about = db.Column(db.String(2000), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    picture = db.Column(db.String())
    price = db.Column(db.Float, nullable=False)
    goals = db.Column(db.String, nullable=False)
    free = db.Column(db.String, nullable=False)
    bookings = db.relationship("Booking", back_populates="profile")


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'))
    profile = db.relationship("Profile", back_populates="bookings")
    weekday = db.Column(db.String(3), nullable=False)
    time = db.Column(db.String(5), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String(15), nullable=False)
    time = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)


def fill_data():
    with open("profiles.json", encoding="utf-8") as f:
        profiles = json.load(f)

    for profile in profiles:
        profile_db = Profile(name=profile['name'], about=profile['about'],
                             rating=profile['rating'], picture=profile['picture'],
                             price=profile['price'], goals=json.dumps(profile['goals']),
                             free=json.dumps(profile['free']))
        db.session.add(profile_db)
    db.session.commit()


try:
    if not db.session.query(Profile).all():
        fill_data()
except ProgrammingError:
    # для гладкой миграции
    pass

goals = {"travel": "Для путешествий", "study": "Для учебы", "work": "Для работы", "relocate": "Для переезда"}

days_of_week = {"mon": "Понедельник", "tue": "Вторник", "wed": "Среда",
                "thu": "Четверг", "fri": "Пятница", "sat": "Суббота",
                "sun": "Воскресенье"}


class BookingForm(FlaskForm):
    name = StringField('clientName', [InputRequired(), Length(min=1, max=50)])
    phone = StringField('clientPhone', [InputRequired(), Length(min=5, max=20)])
    weekday = HiddenField('clientWeekday', [InputRequired(), AnyOf(list(days_of_week.keys()))])
    time = HiddenField('clientTime', [InputRequired()])
    teacher = HiddenField('clientTeacher', [InputRequired()])


class RequestForm(FlaskForm):
    name = StringField('clientName', [InputRequired(), Length(min=1, max=50)])
    phone = StringField('clientPhone', [InputRequired(), Length(min=5, max=20)])
    time = RadioField('clientTime', choices=["1-2 часа в неделю", "3-5 часов в неделю",
                                             "5-7 часов в неделю", "7-10 часов в неделю"],
                      default="1-2 часа в неделю")
    goal = RadioField('clientGoal', choices=["travel", "study", "work", "relocate"],
                      default="travel")


@app.route('/')
def render_main():
    profiles = db.session.query(Profile).all()
    return render_template('index.html', teachers=random.sample(profiles, 6), goals=goals)


@app.route('/goals/<goal>/')
def render_goal(goal):
    looking_goal = '%{0}%'.format(goal)
    profiles = db.session.query(Profile).filter(Profile.goals.ilike(looking_goal)).order_by(Profile.rating)
    return render_template('goal.html', goal=goal, goals=goals, teachers=profiles)


@app.route('/profiles/<id>/')
def render_profile(id):
    profile = db.session.query(Profile).get_or_404(int(id))
    profile.free = json.loads(profile.free)
    profile.goals = json.loads(profile.goals)
    return render_template('profile.html', teacher=profile, goals=goals,
                           days_of_week=days_of_week, id=id)


@app.route('/request/', methods=['POST', 'GET'])
def render_request():
    form = RequestForm()
    if request.method == 'POST':
        name = form.name.data
        phone = form.phone.data
        goal = form.goal.data
        time = form.time.data
        if form.validate_on_submit():
            request_db = Request(name=name, phone=phone, goal=goal, time=time)
            db.session.add(request_db)
            db.session.commit()
            return render_template('request_done.html', name=name,
                                   phone=phone, goal=goal, time=time)
        else:
            return render_template('request.html', form=form, goals=goals)
    else:
        return render_template('request.html', form=form, goals=goals)


@app.route('/booking/<id>/<day_week>/<time>/', methods=['POST', 'GET'])
def render_booking(id, day_week, time):
    # обработка несущ. репетитора
    ids = [id[0] for id in db.session.query(Profile.id).all()]
    if int(id) not in ids:
        abort(404)

    # обработка несуществующего дня недели
    if day_week not in days_of_week.keys():
        abort(404)

    # гарантия, что время свободно
    free = json.loads((db.session.query(Profile).get(int(id))).free)
    if time not in free[day_week].keys() or not free[day_week][time]:
        abort(404)

    form = BookingForm(weekday=day_week, time=time, teacher=id)
    if request.method == 'POST':
        name = form.name.data
        phone = form.phone.data
        weekday = form.weekday.data
        time = form.time.data
        teacher = form.teacher.data
        profile = db.session.query(Profile).get_or_404(int(teacher))
        if form.validate_on_submit():
            booking = Booking(profile=profile, weekday=weekday, time=time, name=name,
                              phone=phone)
            db.session.add(booking)
            free[day_week][time] = False
            profile.free = json.dumps(free)
            db.session.commit()
            return render_template('booking_done.html', name=name, phone=phone,
                                   weekday=days_of_week[weekday], time=time, teacher=profile)
        else:
            return render_template('booking.html', id=id, teacher=profile,
                                   day_week=day_week, time=time, days_of_week=days_of_week,
                                   form=form)
    else:
        profile = db.session.query(Profile).get_or_404(int(id))
        return render_template('booking.html', id=id, teacher=profile,
                               day_week=day_week, time=time, days_of_week=days_of_week,
                               form=form)
