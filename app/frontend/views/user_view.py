# app/frontend/views/user_view.py
import streamlit as st
from app.backend import crud, schemas
from pydantic import ValidationError
from app.frontend.utils import check_password_strength_live # ZMIANA IMPORTU

def show_change_password_view(db):
    # DEBUG - usuń po teście
    # st.write("DEBUG: Funkcja show_change_password_view wystartowała")

    st.title("🔐 Zmiana hasła")
    st.write("Dla Twojego bezpieczeństwa zalecamy regularną zmianę hasła.")

    # Sprawdźmy czy sesja nie wygasła
    if "user" not in st.session_state or st.session_state.user is None:
        st.error("Błąd sesji. Zaloguj się ponownie.")
        return

    user = st.session_state.user
    role = st.session_state.role

    with st.container(border=True):
        curr_pwd = st.text_input("Aktualne hasło", type="password", key="cp_curr")
        st.divider()

        new_pwd = st.text_input("Nowe hasło", type="password", key="cp_new",
                                help="Minimum 8 znaków, wielka litera, cyfra i znak specjalny")

        if new_pwd:
            score, label, color = check_password_strength_live(new_pwd)
            st.progress(score / 4)
            st.markdown(f"Siła nowego hasła: **:{color}[{label}]**")

        confirm_pwd = st.text_input("Powtórz nowe hasło", type="password", key="cp_conf")

        if st.button("Zaktualizuj hasło", type="primary", use_container_width=True):
            try:
                # Walidacja Pydantic
                data = schemas.PasswordChange(
                    current_password=curr_pwd,
                    new_password=new_pwd,
                    confirm_password=confirm_pwd
                )

                # Próba aktualizacji w bazie
                # PRZYPISUJEMY WYNIK DO SESJI TUTAJ:
                updated_user = crud.update_user_password(db, user, role, data)
                st.session_state.user = updated_user

                st.success("✅ Hasło zostało pomyślnie zmienione!")
                st.balloons()

            except ValidationError as e:
                for error in e.errors():
                    msg = error['msg'].replace("Value error, ", "")
                    if "at least 8 characters" in msg: msg = "musi mieć min. 8 znaków"
                    st.error(f"⚠️ {msg}")
            except ValueError as ve:
                st.error(f"❌ {str(ve)}")
            except Exception as ex:
                st.error(f"🚨 Błąd bazy danych: {ex}")