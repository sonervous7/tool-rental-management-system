# app/frontend/views/guest_view.py
import streamlit as st
from app.backend import crud, schemas
from pydantic import ValidationError


def check_password_strength_live(password: str):
    """Zwraca wynik (0-4), komunikat i kolor."""
    score = 0
    if len(password) >= 8: score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*(),.?\":{}|<>" for c in password): score += 1

    if score <= 2:
        return score, "🔴 Słabe hasło", "red"
    elif score == 3:
        return score, "🟡 Średnie hasło", "orange"
    else:
        return score, "🟢 Mocne hasło", "green"


def show_registration_view(db):
    st.title("📝 Rejestracja nowego konta")
    st.write("Dołącz do nas, aby rezerwować narzędzia online!")

    field_labels = {
        "imie": "Imię",
        "nazwisko": "Nazwisko",
        "email": "Adres Email",
        "telefon": "Numer telefonu",
        "haslo": "Hasło",
        "haslo_powtorz": "Powtórz hasło",
        "odpowiedz_pomocnicza": "Odpowiedź na pytanie"
    }

    questions = [
        "Imię i nazwisko panieńskie matki?",
        "Imię Twojego pierwszego zwierzęcia?",
        "Miasto, w którym się urodziłeś/aś?",
        "Model Twojego pierwszego samochodu?",
        "Nazwa Twojej szkoły podstawowej?",
        "Ulubiona książka z dzieciństwa?"
    ]

    # Używamy kontenera z obramowaniem zamiast st.form dla reaktywności hasła
    with st.container(border=True):
        col1, col2 = st.columns(2)
        imie = col1.text_input("Imię")
        nazwisko = col2.text_input("Nazwisko")
        email = col1.text_input("Email")
        tel = col2.text_input("Telefon")

        st.divider()
        # Używamy pełnej listy pytań, o którą prosiłeś
        pytanie = st.selectbox("Wybierz pytanie pomocnicze", questions)
        odpowiedz = st.text_input("Odpowiedź na pytanie pomocnicze*")

        st.divider()
        st.subheader("Zabezpieczenia")

        # POLE HASŁA (Reaktywne - odświeża się po wyjściu z pola lub Enterze)
        pwd1 = st.text_input("Hasło*", type="password",
                             help="Wymagane: 8 znaków, wielka litera, cyfra i znak specjalny")

        # Logika paska siły hasła
        score, label, color = check_password_strength_live(pwd1)
        if pwd1:
            st.progress(score / 4)
            st.markdown(f"Siła hasła: **:{color}[{label}]**")
            if score < 4:
                st.caption("Wskazówka: Hasło musi zawierać wielką literę, cyfrę oraz znak specjalny.")

        pwd2 = st.text_input("Powtórz hasło*", type="password")

        st.caption("* Pola obowiązkowe")

        # Zmieniamy na st.button (ponieważ st.container nie obsługuje form_submit_button)
        submit = st.button("Zarejestruj się", type="primary", use_container_width=True)

        if submit:
            try:
                # Walidacja Pydantic (korzysta z Twoich nowych reguł w schemas.py)
                new_user_data = schemas.CustomerCreate(
                    imie=imie,
                    nazwisko=nazwisko,
                    telefon=tel,
                    email=email,
                    pytanie_pomocnicze=pytanie,
                    odpowiedz_pomocnicza=odpowiedz,
                    haslo=pwd1,
                    haslo_powtorz=pwd2
                )

                # Zapis do bazy danych
                crud.create_customer(db, new_user_data)
                st.success("🎉 Konto zostało utworzone pomyślnie! Możesz się teraz zalogować.")

            except ValidationError as e:
                for error in e.errors():
                    field_key = error['loc'][0]
                    friendly_name = field_labels.get(field_key, field_key)
                    msg = error['msg']

                    # Twoje czyszczenie technicznych komunikatów
                    clean_msg = msg.replace("Value error, ", "").replace("Assertion failed, ", "")

                    if "pattern" in clean_msg:
                        clean_msg = "nieprawidłowy format (wpisz np. 123-456-789)"
                    elif "at least 8 characters" in clean_msg:
                        clean_msg = "musi mieć co najmniej 8 znaków"
                    elif "contains at least one uppercase" in clean_msg:
                        clean_msg = "musi zawierać co najmniej jedną wielką literę"
                    elif "contains at least one digit" in clean_msg:
                        clean_msg = "musi zawierać co najmniej jedną cyfrę"
                    elif "at least one special character" in clean_msg:
                        clean_msg = "musi zawierać co najmniej jeden znak specjalny"
                    elif "value is not a valid email" in clean_msg:
                        clean_msg = "musi być poprawnym adresem e-mail"

                    st.error(f"⚠️ Pole **{friendly_name}**: {clean_msg}")

            except ValueError as ve:
                # Obsługa błędu "Użytkownik już istnieje" bez tracebacku
                st.error(f"❌ {str(ve)}")
            except Exception as ex:
                st.error("🚨 Wystąpił nieoczekiwany problem techniczny.")


def show_login_view(db, navigate_to):
    st.title("🔑 Logowanie")
    st.write("Witaj ponownie! Zaloguj się do swojego konta.")

    with st.container(border=True):
        identifier = st.text_input("Login lub Email", placeholder="Wpisz swój login lub adres email...")
        password = st.text_input("Hasło", type="password", placeholder="********")

        remember_me = st.checkbox("Zapamiętaj mnie")

        if st.button("Zaloguj się", type="primary", use_container_width=True):
            if not identifier or not password:
                st.warning("Proszę podać login i hasło.")
            else:
                user, role = crud.authenticate_user(db, identifier, password)
                if user:
                    st.session_state.user = user
                    st.session_state.role = role
                    st.success(f"Zalogowano pomyślnie jako {role}!")
                    navigate_to("🏠 Start")
                else:
                    st.error("Błędny login lub hasło.")

        st.markdown("---")

        # Sekcja nawigacyjna
        col1, col2 = st.columns(2)

        with col1:
            st.write("Nie masz konta?")
            # TYLKO JEDEN PRZYCISK - przenosi do rejestracji
            if st.button("Stwórz konto", type="secondary", use_container_width=True):
                navigate_to("📝 Rejestracja")

        with col2:
            st.write("Problem z hasłem?")
            if st.button("Przypomnij hasło", type="secondary", use_container_width=True):
                navigate_to("❓ Przypomnij hasło")


def show_forgot_password_view(db, navigate_to):
    st.title("❓ Odzyskiwanie dostępu")
    st.write("Zapomniałeś hasła? Odpowiedz na pytanie pomocnicze, aby odzyskać dostęp.")

    with st.container(border=True):
        email = st.text_input("Podaj e-mail podany przy rejestracji", placeholder="przyklad@email.pl")

        if email:
            # Próbujemy pobrać pytanie z bazy
            question = crud.get_security_question_by_email(db, email)

            if question:
                st.info(f"Twoje pytanie pomocnicze:\n\n**{question}**")
                answer = st.text_input("Twoja odpowiedź", placeholder="Wpisz odpowiedź...", type="password")

                st.divider()
                if st.button("Wyślij e-mail z hasłem", type="primary", use_container_width=True):
                    if not answer:
                        st.warning("Proszę podać odpowiedź.")
                    else:
                        # Weryfikacja odpowiedzi
                        is_correct = crud.verify_security_answer(db, email, answer)
                        if is_correct:
                            # Tutaj w przyszłości wyzwalacz dla n8n / SMTP
                            st.success("✅ Dane poprawne! Instrukcja odzyskiwania hasła została wysłana na Twój e-mail.")
                            st.info("ℹ️ (Na tym etapie system symuluje wysyłkę e-maila)")
                        else:
                            st.error("❌ Błędna odpowiedź na pytanie pomocnicze.")
            else:
                st.error("Nie znaleziono użytkownika o podanym adresie e-mail.")

        st.divider()
        if st.button("⬅️ Powrót do logowania", use_container_width=True):
            navigate_to("🔑 Logowanie")
