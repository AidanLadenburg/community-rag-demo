import streamlit as st
from auth import load_users, authenticate, user_exists, add_user

users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "view" not in st.session_state:
    st.session_state.view = "login"


def login_form():
    st.title("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        if authenticate(username, password, users):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.button(
        "Create New Account", on_click=lambda: st.session_state.update(view="signup")
    )


def signup_form():
    st.title("Create Account")
    username = st.text_input("New Username", key="signup_user")
    password = st.text_input("New Password", type="password", key="signup_pass")
    confirm_password = st.text_input(
        "Confirm Password", type="password", key="signup_confirm"
    )
    linkedin = st.text_input("LinkedIn URL (optional)", key="signup_linkedin")

    if st.button("Register"):
        if user_exists(username, users):
            st.error("Username already exists.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            add_user(username, password, linkedin, users)
            st.success("Account created.")
            st.session_state.view = "login"

    st.button("Back to Login", on_click=lambda: st.session_state.update(view="login"))


def main_app():
    st.title("Logged In")
    username = st.session_state.username
    st.write(f"Hello, **{username}**!")

    my_linkedin = users[username].get("linkedin", "")
    if my_linkedin:
        st.markdown(
            f'<a href="{my_linkedin}" target="_blank">'
            f'<button style="background-color:#0A66C2; color:white; padding:0.5em 1em; '
            f'border:none; border-radius:5px;">My LinkedIn</button></a>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("Other Users")

    for other_user, info in users.items():
        if other_user == username:
            continue

        col1, col2 = st.columns([1, 3])
        with col1:
            st.write(f"**{other_user}**")
        with col2:
            linkedin = info.get("linkedin", "")
            if linkedin:
                st.markdown(
                    f'<a href="{linkedin}" target="_blank">'
                    f'<button style="background-color:#0A66C2; color:white; padding:0.3em 0.8em; '
                    f'border:none; border-radius:4px; font-size:0.9em;">'
                    f"LinkedIn</button></a>",
                    unsafe_allow_html=True,
                )
            else:
                st.write("No LinkedIn provided")

    st.markdown("---")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.view = "login"


if st.session_state.logged_in:
    main_app()
elif st.session_state.view == "signup":
    signup_form()
else:
    login_form()
