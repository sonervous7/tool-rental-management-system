import streamlit as st
from pydantic import ValidationError


def show_registration_view(api):
    from app.backend.modules.users import schemas
    from app.frontend.utils import check_password_strength_live

    st.title("📝 Rejestracja nowego konta")

    field_labels = {
        "imie": "Imię", "nazwisko": "Nazwisko", "email": "Adres Email",
        "telefon": "Numer telefonu", "haslo": "Hasło",
        "haslo_powtorz": "Powtórz hasło", "odpowiedz_pomocnicza": "Odpowiedź na pytanie"
    }

    error_messages = {
        "value_error.missing": "To pole nie może być puste.",
        "string_too_short": "Wprowadzony tekst jest za krótki (min. {limit_value} znaków).",
        "value_error.email": "To nie jest poprawny adres e-mail.",
        "value_error.any_str.max_length": "Tekst jest za długi.",
        "value_error": "Wystąpił błąd: {msg}"
    }

    with st.container(border=True):
        col1, col2 = st.columns(2)
        imie = col1.text_input("Imię")
        nazwisko = col2.text_input("Nazwisko")
        email = col1.text_input("Email")
        tel = col2.text_input("Telefon")

        st.divider()
        pytanie = st.selectbox("Wybierz pytanie pomocnicze", [
            "Imię i nazwisko panieńskie matki?", "Imię Twojego pierwszego zwierzęcia?",
            "Miasto, w którym się urodziłeś/aś?", "Model Twojego pierwszego samochodu?"
        ])
        odpowiedz = st.text_input("Odpowiedź na pytanie pomocnicze*", type="password")

        st.divider()
        pwd1 = st.text_input("Hasło*", type="password", help="Minimum 8 znaków, wielka litera i cyfra.")

        if pwd1:
            score, label, color = check_password_strength_live(pwd1)
            st.progress(score / 4)
            st.markdown(f"Siła hasła: **:{color}[{label}]**")

        pwd2 = st.text_input("Powtórz hasło*", type="password")
        submit = st.button("Zarejestruj się", type="primary", use_container_width=True)

        if submit:
            try:
                new_user_data = schemas.CustomerCreate(
                    imie=imie, nazwisko=nazwisko, telefon=tel, email=email,
                    pytanie_pomocnicze=pytanie, odpowiedz_pomocnicza=odpowiedz,
                    haslo=pwd1, haslo_powtorz=pwd2
                )

                response = api.post("/users/register", data=new_user_data.model_dump())

                if response and response.status_code == 201:
                    st.success("🎉 Konto utworzone! Możesz się już zalogować.")
                    st.balloons()
                elif response:
                    detail = response.json().get('detail')
                    if "already registered" in str(detail).lower():
                        st.error("📧 Ten adres email jest już zajęty.")
                    else:
                        st.error(f"❌ Błąd serwera: {detail}")

            except ValidationError as e:
                for error in e.errors():
                    field_key = error['loc'][0]
                    friendly_field = field_labels.get(field_key, field_key)

                    err_type = error['type']
                    msg = error['msg']

                    if "at least" in msg:
                        limit = "".join(filter(str.isdigit, msg))
                        st.error(f"⚠️ **{friendly_field}**: Musi mieć co najmniej {limit} znaków.")
                    elif "not match" in msg.lower() or "identyczne" in msg.lower():
                        st.error(f"⚠️ **{friendly_field}**: Hasła muszą być identyczne.")
                    else:
                        st.error(f"⚠️ **{friendly_field}**: {msg}")


def show_login_view(api, navigate_to):
    st.title("🔑 Logowanie")
    with st.container(border=True):
        identifier = st.text_input("Login lub Email")
        password = st.text_input("Hasło", type="password")

        if st.button("Zaloguj się", type="primary", use_container_width=True):
            if not identifier or not password:
                st.warning("Uzupełnij login i hasło.")
            else:
                response = api.post("/users/login", data={"login": identifier, "haslo": password})

                if response and response.status_code == 200:
                    data = response.json()
                    st.session_state.user = data
                    st.session_state.role = data.get("rola") or data.get("role")

                    st.success(f"Witaj {data['imie']}! Przekierowuję...")
                    navigate_to("🏠 Start")
                else:
                    st.error("🚫 Niepoprawne dane logowania.")


def show_forgot_password_view(api, navigate_to):
    st.title("❓ Odzyskiwanie dostępu")

    with st.container(border=True):
        st.write("Wprowadź swój e-mail, aby odpowiedzieć na pytanie pomocnicze.")
        email = st.text_input("Podaj adres e-mail")

        if email:
            response = api.get(f"/users/security-question", params={"email": email})

            if response and response.status_code == 200:
                question = response.json().get("question")
                st.info(f"Pytanie pomocnicze: **{question}**")

                answer = st.text_input("Twoja odpowiedź", type="password")

                if st.button("Weryfikuj", type="primary", use_container_width=True):
                    resp_verify = api.post(
                        f"/users/verify-security-answer",
                        params={"email": email, "answer": answer}
                    )

                    if resp_verify and resp_verify.status_code == 200:
                        st.success("✅ Dane poprawne! Instrukcja resetowania hasła została wysłana na Twój e-mail.")
                        st.balloons()
                    else:
                        st.error("❌ Błędna odpowiedź na pytanie pomocnicze.")

            elif response and response.status_code == 404:
                st.error("Nie znaleziono użytkownika z takim adresem e-mail.")
            elif response:
                st.error("Błąd połączenia z serwerem.")

        st.divider()
        if st.button("⬅️ Powrót do logowania", use_container_width=True):
            navigate_to("🔑 Logowanie")