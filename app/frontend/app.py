import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# app/frontend/app.py
import streamlit as st
from app.backend.database import SessionLocal
from app.backend import models
from views.manager_view import show_manager_ui
from views.technician_view import show_technician_ui
# from views.technician_view import show_technician_ui # to zrobimy za chwilę

st.set_page_config(page_title="System Wypożyczalni Narzędzi", layout="wide")
# --- SESJA I SYMULACJA ROLI ---
if "role" not in st.session_state:
    # Możesz tu zmienić na "KIEROWNIK", "MAGAZYNIER", "KLIENT" lub None (Gość)
    st.session_state.role = "KLIENT"

db = SessionLocal()

# --- MOCKOWANIE UŻYTKOWNIKA DLA TESTÓW ---
if "user" not in st.session_state:
    if st.session_state.role:
        # Próbujemy pobrać z DB lub robimy Mock
        test_user = db.query(models.Pracownik).first()  # Na potrzeby testu dowolny
        if test_user:
            st.session_state.user = test_user
        else:
            from types import SimpleNamespace

            st.session_state.user = SimpleNamespace(id=999, imie="Tester", nazwisko="Serwisowy")
    else:
        st.session_state.user = None


if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Start"

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# --- DEFINICJA MENU BOCZNEGO (Mapowanie ról) ---
def get_menu_options(role):
    if role == "KIEROWNIK":
        return ["🏠 Start", "🔐 Zmiana hasła", "🧰 Zarządzaj modelami", "👥 Zarządzaj kontami", "📊 Analiza danych",
                "💾 Eksport danych"]
    elif role == "SERWISANT":
        return ["🏠 Start", "🔧 Zarządzanie narzędziami", "🔐 Zmiana hasła"]
    elif role == "MAGAZYNIER":
        return ["🏠 Start", "🔐 Zmiana hasła", "🔍 Przeglądaj narzędzia", "📦 Wypożyczenia", "📥 Przyjmij zasoby"]
    elif role == "KLIENT":
        return ["🏠 Start", "🔐 Zmiana hasła", "🛠 Dostępne narzędzia", "📜 Historia Wypożyczeń", "⚠️ Zgłoś usterkę"]
    else:  # Gość (None)
        return ["🏠 Start", "📝 Rejestracja", "🔑 Logowanie", "❓ Przypomnij hasło", "🛠 Dostępne narzędzia"]


menu_options = get_menu_options(st.session_state.role)


# --- SIDEBAR ---
with st.sidebar:
    st.title("📂 System Rental")

    try:
        current_index = menu_options.index(st.session_state.current_page)
    except ValueError:
        current_index = 0

    # Teraz radio korzysta z key="sidebar_nav", a navigate_to go modyfikuje
    choice = st.radio(
        "Nawigacja",
        menu_options,
        index=current_index
    )

    # Jeśli użytkownik kliknął w radio (zmienił wybór ręcznie), aktualizujemy stan
    if choice != st.session_state.current_page:
        st.session_state.current_page = choice
        st.rerun()

    # --- UNIWERSALNA STOPKA UŻYTKOWNIKA ---
    # Pojawi się tylko, jeśli użytkownik jest zalogowany [cite: 381]
    if st.session_state.user:
        st.sidebar.markdown("---")
        # Wykorzystujemy atrybuty z encji Pracownik [cite: 185, 189]
        st.sidebar.markdown(f"👤 **{st.session_state.user.imie} {st.session_state.user.nazwisko}**")
        st.sidebar.markdown(f"🏷️ Rola: `{st.session_state.role}`")

        # Przycisk wylogowania (zgodnie z PU 19 i 40) [cite: 968, 1498]
        if st.sidebar.button("Wyloguj się", use_container_width=True):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()

# --- LOGIKA RENDEROWANIA WIDOKÓW ---

# 1. Start (Wspólny)
if "Start" in choice:
    # Nagłówek z ikoną
    st.title("🏗️ Witaj w systemie zarządzania wypożyczalnią narzędzi!")

    # Układ dwukolumnowy: Lewa (Główna treść), Prawa (Kontakt)
    col_main, col_contact = st.columns([2, 1], gap="large")

    with col_main:
        st.markdown("""
        ### 🛠️ Profesjonalny sprzęt na wyciągnięcie ręki
        Nasza wypożyczalnia oferuje szeroki zakres narzędzi budowlanych, ogrodowych i specjalistycznych. 
        Zaloguj się, aby sprawdzić dostępność i zarezerwować sprzęt online.
        """)

        # Fancy Regulamin - Sekcja rozwijana po kliknięciu
        with st.expander("📄 Przeczytaj Regulamin Wypożyczalni"):
            st.write("### Regulamin Wypożyczalni Narzędzi")

            tab1, tab2, tab3 = st.tabs(["I. Rezerwacja", "II. Odbiór i Zwrot", "III. Usterki"])

            with tab1:
                st.markdown("**1. Rezerwacja i Wypożyczenie Online**")
                st.write("- Wszystkie rezerwacje dokonywane są wyłącznie przez system online.")
                st.write("- Potwierdzenie przez system gwarantuje dostępność narzędzia w wybranym terminie.")
                st.write("- Anulowanie rezerwacji musi nastąpić min. 24h przed terminem odbioru.")

            with tab2:
                st.markdown("**II. Odbiór i Zwrot**")
                st.write("- Przy odbiorze należy okazać dokument tożsamości i potwierdzenie rezerwacji.")
                st.write("- Klient jest zobowiązany sprawdzić stan techniczny narzędzia przy odbiorze.")
                st.write("- Narzędzie musi zostać zwrócone w terminie, czyste i kompletne.")

            with tab3:
                st.markdown("**III. Odpowiedzialność i Usterki**")
                st.write("- W przypadku awarii należy niezwłocznie zaprzestać pracy i zgłosić usterkę online.")
                st.write("- Klient ponosi odpowiedzialność za uszkodzenia wynikające z niewłaściwego użytkowania.")
                st.write("- Zapewniamy naprawę lub wymianę, jeśli usterka nie wynikła z winy Klienta.")

    with col_contact:
        # Panel boczny z danymi kontaktowymi w "fancy" ramce
        with st.container(border=True):
            st.subheader("📞 Dane kontaktowe")
            st.markdown(f"""
            **Narzędziarnia Express Sp. z o.o.**

            📍 {892 if False else 'ul. Przemysłowa 54/A'}  
            🏙️ 30-701 Kraków

            ☎️ **{903 if False else '+48 123 456 789'}**  
            📧 {903 if False else 'kontakt@narzedziarnia.pl'}

            **NIP:** 676-249-12-00
            """)

            st.divider()
            st.info(f"🕒 **Godziny otwarcia:** \nPon - Pt: 7:00 - 17:00")

    # Stopka zachęcająca do działania dla niezalogowanych
    if not st.session_state.user:
        st.divider()
        st.warning("👋 Nie jesteś zalogowany. Przejdź do zakładki **Logowanie**, aby zarządzać rezerwacjami.")

# 2. Zmiana hasła (Dla wszystkich zalogowanych)
elif "Zmiana hasła" in choice:
    st.header("🔐 Zmiana hasła")
    # Tu później wstawisz formularz

# 3. Widoki KIEROWNIKA
elif "Zarządzaj modelami" in choice:
    # show_manager_ui z filtrem na modele
    show_manager_ui(db, section="Modele")
elif "Zarządzaj kontami" in choice:
    show_manager_ui(db, section="Pracownicy")
elif "Analiza danych" in choice:
    show_manager_ui(db, section="Analiza")
elif "Eksport danych" in choice:
    show_manager_ui(db, section="Eksport")

# 4. Widoki SERWISANTA
elif "Zarządzanie narzędziami" in choice:
    show_technician_ui(db, st.session_state.user)

# 5. Widoki MAGAZYNIERA (Placeholdery)
elif choice == "🔍 Przeglądaj narzędzia":
    from views.warehouse_view import show_warehouseman_ui
    show_warehouseman_ui(db, st.session_state.user, "Przeglądaj narzędzia")

elif choice == "📦 Wypożyczenia":
    from views.warehouse_view import show_warehouseman_ui
    show_warehouseman_ui(db, st.session_state.user, "Wypożyczenia")

elif choice == "📥 Przyjmij zasoby":
    from views.warehouse_view import show_warehouseman_ui
    show_warehouseman_ui(db, st.session_state.user, "Przyjmij zasoby")
# app/frontend/app.py
elif choice == "🛠 Dostępne narzędzia":
    from views.client_view import show_client_catalog
    show_client_catalog(db, st.session_state.user)
# 6. Widoki KLIENTA / GOŚCIA
elif choice == "📝 Rejestracja":
    from views.guest_view import show_registration_view
    show_registration_view(db)
elif choice == "🔑 Logowanie":
    from views.guest_view import show_login_view
    show_login_view(db, navigate_to)
elif choice == "❓ Przypomnij hasło":
    from views.guest_view import show_forgot_password_view
    show_forgot_password_view(db, navigate_to)
elif choice in ["📜 Historia Wypożyczeń"]:
    st.title(f"Panel Klienta: {choice}")
    st.info("Ten moduł zostanie zrealizowany w kolejnym kroku.")

db.close()

