import streamlit as st
from pydantic import ValidationError
from app.frontend.utils import check_password_strength_live


def show_change_password_view(api):
    from app.backend.modules.users import schemas

    st.title("🔐 Zmiana hasła")
    st.write("Dla Twojego bezpieczeństwa zalecamy regularną zmianę hasła.")

    if "user" not in st.session_state or st.session_state.user is None:
        st.error("Błąd sesji. Zaloguj się ponownie.")
        return

    user = st.session_state.user

    with st.container(border=True):
        curr_pwd = st.text_input("Aktualne hasło", type="password", key="cp_curr")
        st.divider()

        new_pwd = st.text_input(
            "Nowe hasło",
            type="password",
            key="cp_new",
            help="Minimum 8 znaków, wielka litera, cyfra i znak specjalny"
        )

        if new_pwd:
            score, label, color = check_password_strength_live(new_pwd)
            st.progress(score / 4)
            st.markdown(f"Siła nowego hasła: **:{color}[{label}]**")

        confirm_pwd = st.text_input("Powtórz nowe hasło", type="password", key="cp_conf")

        if st.button("Zaktualizuj hasło", type="primary", use_container_width=True):
            if not curr_pwd or not new_pwd or not confirm_pwd:
                st.error("⚠️ Wszystkie pola są wymagane.")
                return

            try:
                data = schemas.PasswordChange(
                    current_password=curr_pwd,
                    new_password=new_pwd,
                    confirm_password=confirm_pwd
                )

                resp = api.patch(
                    "/users/change-password",
                    data=data.model_dump(),
                    params={"user_id": user['id']}
                )

                if resp and resp.status_code == 200:
                    st.success("✅ Hasło zostało pomyślnie zmienione!")
                    st.balloons()
                else:
                    error_detail = resp.json().get('detail', 'Wystąpił błąd')
                    st.error(f"❌ {error_detail}")

            except ValidationError as e:
                for error in e.errors():
                    msg = error['msg'].replace("Value error, ", "")
                    st.error(f"⚠️ {msg}")
            except Exception as ex:
                st.error(f"🚨 Problem techniczny: {ex}")
