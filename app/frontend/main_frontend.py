import sys
import os
from pathlib import Path

root_path = str(Path(__file__).resolve().parents[2])

if root_path not in sys.path:
    sys.path.append(root_path)

import streamlit as st
from api_client import APIClient

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Rental System PRO",
    page_icon="🏗️",
    layout="wide"
)

# --- INICJALIZACJA SESJI ---
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Start"

# Inicjalizacja klienta API
api = APIClient()


# Funkcja pomocnicza do nawigacji
def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()


# Stałe
OPT_CHANGE_PASSWORD = "🔐 Zmiana hasła"


# --- LOGIKA MENU (Mapowanie ról na widoki) ---
def get_menu_options(role):
    if role == "KIEROWNIK":
        return ["🏠 Start", OPT_CHANGE_PASSWORD, "🧰 Zarządzaj modelami", "👥 Zarządzaj kontami", "📊 Analiza danych",
                "💾 Eksport danych"]
    elif role == "SERWISANT":
        return ["🏠 Start", "🔧 Zarządzanie narzędziami", OPT_CHANGE_PASSWORD]
    elif role == "MAGAZYNIER":
        return ["🏠 Start", OPT_CHANGE_PASSWORD, "🔍 Przeglądaj narzędzia", "📦 Wypożyczenia", "📥 Przyjmij zasoby"]
    elif role == "KLIENT":
        return ["🏠 Start", OPT_CHANGE_PASSWORD, "🛠 Dostępne narzędzia", "📜 Historia Wypożyczeń", "⚠️ Zgłoś usterkę"]
    else:
        return ["🏠 Start", "📝 Rejestracja", "🔑 Logowanie", "❓ Przypomnij hasło", "🛠 Dostępne narzędzia"]


menu_options = get_menu_options(st.session_state.role)

# --- SIDEBAR (NAWIGACJA) ---
with st.sidebar:
    st.title("📂 Rental System PRO")

    # Ustalanie aktualnego indeksu dla radia
    try:
        current_index = menu_options.index(st.session_state.current_page)
    except ValueError:
        current_index = 0

    # Główna nawigacja z unikalnym kluczem
    choice = st.radio(
        "Nawigacja",
        menu_options,
        index=current_index,
        key="main_navigation_radio_v1"
    )

    # Reakcja na zmianę w radio
    if choice != st.session_state.current_page:
        st.session_state.current_page = choice
        st.rerun()

    # Informacje o zalogowanym użytkowniku
    if st.session_state.user:
        st.sidebar.markdown("---")
        u = st.session_state.user
        st.sidebar.markdown(f"👤 **{u['imie']} {u['nazwisko']}**")
        st.sidebar.markdown(f"🏷️ Rola: `{st.session_state.role}`")

        if st.sidebar.button("Wyloguj się", use_container_width=True, key="sidebar_logout_btn"):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.current_page = "🏠 Start"
            st.rerun()

# --- GŁÓWNA LOGIKA RENDEROWANIA (ROUTING) ---

if choice == "🏠 Start":
    st.title("🏗️ Witaj w systemie Rental!")
    col_main, col_contact = st.columns([2, 1], gap="large")

    with col_main:
        st.markdown("### 🛠️ Profesjonalny sprzęt na wyciągnięcie ręki")

        # --- DYNAMICZNY KOMUNIKAT POWITALNY ---
        if st.session_state.user:
            u = st.session_state.user
            st.success(f"Witaj **{u['imie']}**!")
        else:
            st.info("👋 Zaloguj się, aby sprawdzić dostępność i zarezerwować sprzęt.")

        st.markdown("---")
        st.subheader("📄 Regulamin wypożyczalni")

        # Zakładki Regulaminu (PoC)
        tab1, tab2, tab3 = st.tabs(["I. Postanowienia ogólne", "II. Zasady wynajmu", "III. Odpowiedzialność"])

        with tab1:
            st.markdown("""
            **1. Zakres usług**
            * Wypożyczalnia Rental świadczy usługi krótkoterminowego najmu sprzętu budowlanego.
            * Usługi dostępne dla osób pełnoletnich i firm.
            """)

        with tab2:
            st.markdown("""
            **1. Rezerwacje**
            * Rezerwacja online jest ważna po potwierdzeniu przez system.
            * Kaucja pobierana jest przy odbiorze sprzętu.
            """)

        with tab3:
            st.markdown("""
            **1. Odpowiedzialność**
            * Najemca odpowiada za stan techniczny od momentu wydania do zwrotu.
            * Przekroczenie terminu skutkuje naliczeniem opłat dodatkowych.
            """)

    with col_contact:
        with st.container(border=True):
            st.subheader("📞 Kontakt")
            st.write("📍 ul. Przemysłowa 54/A, Wrocław")
            st.write("☎️ +48 123 456 789")
            st.write("📧 kontakt@rental-pro.pl")
            st.write("⏰ Pon-Pt: 7:00 - 18:00")

    if not st.session_state.user:
        st.divider()
        st.warning("👋 Przejdź do zakładki **Logowanie**, aby zacząć korzystać z systemu.")

# --- ROUTING DO MODUŁÓW (Lazy Imports) ---

# KIEROWNIK
elif choice == "🧰 Zarządzaj modelami":
    from views.manager_view import show_manager_ui

    show_manager_ui(api, section="Modele")

elif choice == "👥 Zarządzaj kontami":
    from views.manager_view import show_manager_ui

    show_manager_ui(api, section="Pracownicy")

elif choice == "📊 Analiza danych":
    from views.manager_view import show_manager_ui

    show_manager_ui(api, section="Analiza")

elif choice == "💾 Eksport danych":
    from views.manager_view import show_manager_ui

    show_manager_ui(api, section="Eksport")

# SERWISANT
elif choice == "🔧 Zarządzanie narzędziami":
    from views.technician_view import show_technician_ui

    show_technician_ui(api, st.session_state.user)

# MAGAZYNIER
elif choice in ["🔍 Przeglądaj narzędzia", "📦 Wypożyczenia", "📥 Przyjmij zasoby"]:
    from views.warehouse_view import show_warehouseman_ui

    show_warehouseman_ui(api, st.session_state.user, choice)

# KLIENT / GOŚĆ
elif choice == "🛠 Dostępne narzędzia":
    from views.client_view import show_client_catalog

    show_client_catalog(api, st.session_state.user)

elif choice == "📝 Rejestracja":
    from views.guest_view import show_registration_view

    show_registration_view(api)

elif choice == "🔑 Logowanie":
    from views.guest_view import show_login_view

    show_login_view(api, navigate_to)

elif choice == "❓ Przypomnij hasło":
    from views.guest_view import show_forgot_password_view

    show_forgot_password_view(api, navigate_to)

elif choice == OPT_CHANGE_PASSWORD:
    from views.user_view import show_change_password_view

    show_change_password_view(api)

elif choice == "📜 Historia Wypożyczeń":
    from views.client_view import show_rentals_history

    show_rentals_history(api, st.session_state.user)

elif choice == "⚠️ Zgłoś usterkę":
    from views.client_view import show_report_fault_view

    show_report_fault_view(api, st.session_state.user)