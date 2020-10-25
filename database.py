import json
from app import Profile, app
from flask_sqlalchemy import SQLAlchemy

# Создаем подключение к БД
db = SQLAlchemy(app)


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
