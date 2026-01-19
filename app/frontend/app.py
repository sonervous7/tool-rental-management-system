import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import datetime
from datetime import datetime, date, time
import streamlit as st

from app.backend.database import SessionLocal
from app.backend import crud
from app.backend.schemas import EmployeeCreate, EmployeeUpdate

st.set_page_config(page_title="Rental System – DEV", layout="wide")

st.title("🛠 Rental System – Panel Kierownika (DEV)")


def get_db():
    return SessionLocal()


# --- OKNO DIALOGOWE EDYCJI ---
@st.dialog("Edycja danych pracownika")
def edit_employee_dialog(emp, db):
    st.write(f"Edytujesz: **{emp['imie']} {emp['nazwisko']}**")

    with st.form("modal_edit_form"):
        c1, c2 = st.columns(2)
        new_imie = c1.text_input("Imię", value=emp['imie'])
        new_nazwisko = c2.text_input("Nazwisko", value=emp['nazwisko'])
        new_email = c1.text_input("Email", value=emp['email'] or "")
        new_tel = c2.text_input("Telefon", value=emp['telefon'] or "")
        new_adres = st.text_input("Adres", value=emp['adres'] or "")

        st.markdown("---")
        roles = ["KIEROWNIK", "MAGAZYNIER", "SERWISANT"]
        new_rola = st.selectbox("Rola", roles, index=roles.index(emp['rola']) if emp['rola'] in roles else 0)

        # Obsługa daty
        curr_d = emp['zatrudniony_od'].date() if isinstance(emp['zatrudniony_od'], datetime) else date.today()
        new_d = st.date_input("Data zatrudnienia w roli", value=curr_d)

        if st.form_submit_button("Zapisz zmiany", use_container_width=True):
            try:
                # 1. Update danych podstawowych
                crud.update_employee(db, emp['id'], payload=EmployeeUpdate(
                    imie=new_imie, nazwisko=new_nazwisko, email=new_email,
                    telefon=new_tel, adres=new_adres
                ))
                # 2. Update roli i daty
                new_dt = datetime.combine(new_d, time.min)
                crud.change_employee_role(db, emp['id'], new_rola, data_startu=new_dt)

                st.success("Zapisano!")
                st.rerun()
            except Exception as ex:
                st.error(f"Błąd: {ex}")


menu = st.sidebar.selectbox(
    "Menu",
    [
        "Pracownicy",
        "Modele narzędzi",
        "Analiza",
        "Eksport",
    ],
)

db = get_db()

# -------------------------------------------------
# PRACOWNICY
# -------------------------------------------------
if menu == "Pracownicy":
    st.header("👷 Zarządzanie Kadrami")

    # --- SEKCJA DODAWANIA NOWEGO PRACOWNIKA ---
    with st.expander("➕ Dodaj nowego pracownika"):
        with st.form("add_employee_new"):
            c1, c2 = st.columns(2)
            imie = c1.text_input("Imię")
            nazwisko = c2.text_input("Nazwisko")
            pesel = c1.text_input("PESEL (11 znaków)")
            email = c2.text_input("Adres Email")
            telefon = c1.text_input("Numer telefonu")
            adres = c2.text_input("Adres zamieszkania")

            login = c1.text_input("Login")
            haslo = c2.text_input("Hasło", type="password")
            rola = st.selectbox("Rola systemowa", ["KIEROWNIK", "MAGAZYNIER", "SERWISANT"])

            # Data zatrudnienia dla nowej roli
            data_zatr_new = st.date_input("Data zatrudnienia", value=date.today())

            if st.form_submit_button("Utwórz konto pracownika"):
                try:
                    dt_zatr = datetime.combine(data_zatr_new, time.min)
                    crud.create_employee(
                        db,
                        payload=EmployeeCreate(
                            imie=imie, nazwisko=nazwisko, pesel=pesel,
                            email=email if email else None,
                            telefon=telefon if telefon else None,
                            adres=adres if adres else None,
                            login=login, haslo=haslo, rola=rola,
                            data_zatrudnienia=dt_zatr
                        ),
                    )
                    st.success(f"Dodano pracownika: {imie} {nazwisko}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {str(e)}")

    # --- LISTA PRACOWNIKÓW ---
    st.subheader("Lista aktywnych kont")
    employees = crud.list_employees(db)

    if not employees:
        st.info("Brak zarejestrowanych pracowników.")

    for e in employees:
        with st.expander(f"👤 {e['imie']} {e['nazwisko']} — {e['rola']}"):
            col1, col2, col3 = st.columns([1, 1, 0.6])

            with col1:
                st.markdown("**Dane Kontaktowe**")
                st.write(f"📧 Email: {e['email'] or 'brak'}")
                st.write(f"📞 Tel: {e['telefon'] or 'brak'}")
                st.write(f"🏠 Adres: {e['adres'] or 'brak'}")

            with col2:
                st.markdown("**Informacje Systemowe**")
                st.write(f"🔑 Login: {e['login']}")
                st.write(f"🆔 PESEL: {e['pesel']}")
                if e['zatrudniony_od']:
                    st.write(f"📅 Zatrudniony od: {e['zatrudniony_od'].strftime('%d.%m.%Y')}")

            with col3:
                st.markdown("**Akcje**")

                # Klucze przycisków muszą być unikalne w pętli
                # Edycja przez Okno Dialogowe (Modal)
                if st.button("Edytuj", key=f"btn_edit_{e['id']}", use_container_width=True):
                    edit_employee_dialog(e, db)

                # Usuwanie
                if st.button("Usuń", key=f"btn_del_{e['id']}", use_container_width=True):
                    try:
                        crud.delete_employee(db, e["id"])
                        st.success("Konto usunięte")
                        st.rerun()
                    except Exception as ex:
                        st.error(str(ex))

# -------------------------------------------------
# MODELE NARZĘDZI
# -------------------------------------------------
elif menu == "Modele narzędzi":
    st.header("🧰 Modele narzędzi")

    models = crud.list_tool_models_for_manager(db)

    st.dataframe(models, use_container_width=True)

# -------------------------------------------------
# ANALIZA
# -------------------------------------------------
elif menu == "Analiza":
    st.header("📊 Analiza")

    col1, col2 = st.columns(2)
    date_from = col1.date_input("Od")
    date_to = col2.date_input("Do")

    if st.button("Generuj"):
        summary = crud.analytics_summary(db, date_from, date_to)
        daily = crud.analytics_daily(db, date_from, date_to)

        st.metric("Liczba wypożyczeń", summary["total_rentals"])
        st.metric("Przychód", f"{summary['total_revenue']} zł")

        st.line_chart(daily, x="dzien", y="liczba_wypozyczen")

# -------------------------------------------------
# EKSPORT
# -------------------------------------------------
elif menu == "Eksport":
    st.header("⬇️ Eksport CSV")

    table = st.selectbox(
        "Tabela",
        [
            "pracownicy",
            "modele_narzedzi",
            "wypozyczenia",
        ],
    )

    if st.button("Eksportuj"):
        csv_data = crud.export_table_to_csv(db, table)
        st.download_button(
            "Pobierz CSV",
            data=csv_data,
            file_name=f"{table}.csv",
            mime="text/csv",
        )
