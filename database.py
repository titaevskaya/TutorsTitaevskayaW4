import os
import json
from app import Profile, Booking, Request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


# Создаем подключение к БД
db = SQLAlchemy(app)

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


if __name__ == "__main__":
    fill_data()