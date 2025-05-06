import json
import os

USERS_FILE = "users.json"


def load_users(filepath=USERS_FILE):
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump({}, f)
    with open(filepath, "r") as file:
        return json.load(file)


def save_users(users, filepath=USERS_FILE):
    with open(filepath, "w") as file:
        json.dump(users, file, indent=4)


def authenticate(username, password, users):
    return username in users and users[username]["password"] == password


def user_exists(username, users):
    return username in users


def add_user(username, password, linkedin, users, filepath=USERS_FILE):
    users[username] = {"password": password, "linkedin": linkedin}
    save_users(users, filepath)
