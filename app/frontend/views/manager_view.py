import streamlit as st
import datetime
from datetime import datetime, date, time
from app.backend import crud, models, schemas
from pydantic import ValidationError


@st.dialog("Zarządzaj Modelem Narzędzia")
def tool_model_dialog(db, model=None):
    mode = "Edytuj" if model else "Dodaj"
    st.subheader(f"{mode} model narzędzia")
    with st.form("tool_model_form"):
        nazwa = st.text_input("Nazwa modelu", value=model.nazwa_modelu if model else "")
        prod = st.text_input("Producent", value=model.producent if model else "")
        kat = st.text_input("Kategoria", value=model.kategoria if model else "")
        opis = st.text_area("Opis", value=model.opis if model else "")
        c1, c2 = st.columns(2)
        cena = c1.number_input("Cena za dobę (zł)", min_value=0.0, value=float(model.cena_za_dobe) if model else 50.0)
        kaucja = c2.number_input("Kaucja (zł)", min_value=0.0, value=float(model.kaucja) if model else 100.0)

        if st.form_submit_button("Zapisz", use_container_width=True):
            try:
                if model:
                    crud.update_tool_model(db, model.id, schemas.ToolModelUpdate(
                        nazwa_modelu=nazwa, producent=prod, kategoria=kat, opis=opis,
                        cena_za_dobe=cena, kaucja=kaucja
                    ))
                else:
                    crud.create_tool_model(db, schemas.ToolModelCreate(
                        nazwa_modelu=nazwa, producent=prod, kategoria=kat, opis=opis,
                        cena_za_dobe=cena, kaucja=kaucja
                    ))
                st.success("Zapisano!")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd: {e}")


@st.dialog("Edycja danych pracownika")
def edit_employee_dialog(emp, db):


    st.write(f"Edytujesz profil: **{emp['imie']} {emp['nazwisko']}**")

    with st.form("edit_form_modal"):
        c1, c2 = st.columns(2)
        # Streamlit domyślnie zwraca "", jeśli pole jest puste
        new_imie = c1.text_input("Imię*", value=emp['imie'])
        new_nazwisko = c2.text_input("Nazwisko*", value=emp['nazwisko'])
        new_email = c1.text_input("Email*", value=emp['email'] or "")
        new_tel = c2.text_input("Telefon", value=emp['telefon'] or "")
        new_adres = st.text_input("Adres zamieszkania", value=emp['adres'] or "")

        st.markdown("---")
        roles = ["KIEROWNIK", "MAGAZYNIER", "SERWISANT"]
        current_role_idx = roles.index(emp['rola']) if emp['rola'] in roles else 0
        new_rola = st.selectbox("Rola systemowa", roles, index=current_role_idx)

        current_hire_date = emp['zatrudniony_od'].date() if isinstance(emp['zatrudniony_od'],
                                                                       datetime) else date.today()
        new_date_zatr = st.date_input("Data rozpoczęcia pracy w tej roli", value=current_hire_date)

        if st.form_submit_button("Zapisz zmiany", use_container_width=True):
            # Prosta walidacja wstępna w UI (wizualna)
            if not new_imie or not new_nazwisko or not new_email:
                st.error("❌ Pola oznaczone gwiazdką (*) nie mogą być puste!")
                return

            try:
                # Próba walidacji przez Pydantic
                update_data = schemas.EmployeeUpdate(
                    imie=new_imie,
                    nazwisko=new_nazwisko,
                    email=new_email,
                    telefon=new_tel if new_tel else None,
                    adres=new_adres if new_adres else None
                )

                # Jeśli Pydantic przepuścił, robimy update
                crud.update_employee(db, emp['id'], payload=update_data)

                new_dt = datetime.combine(new_date_zatr, time.min)
                crud.change_employee_role(db, emp['id'], new_rola, data_startu=new_dt)

                st.success("Dane zostały zaktualizowane!")
                st.rerun()

            except ValidationError as e:
                # Tutaj używamy naszego helpera od "ładnych błędów"
                show_clean_pydantic_error(e)
            except Exception as ex:
                st.error(f"Wystąpił błąd: {ex}")

@st.dialog("Potwierdź wycofanie")
def withdraw_confirm_dialog(db, model):
    st.warning(f"Czy na pewno chcesz wycofać model: {model.nazwa_modelu}?")
    st.write("Tej operacji nie można cofnąć, jeśli model jest już niepotrzebny.")

    if st.button("Potwierdzam wycofanie", type="primary", use_container_width=True):
        try:
            crud.withdraw_tool_model(db, model.id)
            st.success("Model wycofany!")
            st.rerun()
        except Exception as e:
            st.error(str(e))

def show_manager_ui(db, section):

    if section == "Pracownicy":
        render_employees_section(db)
    elif section == "Modele":
        render_models_section(db)
    elif section == "Analiza":
        render_analytics_section(db)
    elif section == "Eksport":
        render_export_section(db)

def render_employees_section(db):
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
                        payload=schemas.EmployeeCreate(
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
                except ValidationError as e:
                    show_clean_pydantic_error(e)
                except ValueError as e:
                    # Tutaj wpadają błędy z bazy (np. duplikacja PESEL w DB)
                    st.error(f"⚠️ {str(e)}")
                except Exception as e:
                    st.error(f"🔥 Nieoczekiwany błąd: {str(e)}")

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

def render_models_section(db):
    st.header("🧰 Katalog Modeli")
    # --- FILTRY ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        search_q = c1.text_input("🔍 Szukaj modelu", placeholder="Np. Wiertarka...")

        # Pobieramy unikalne wartości do filtrów
        all_models = db.query(models.ModelNarzedzia).all()
        categories = ["Wszystkie"] + sorted(list(set(m.kategoria for m in all_models if m.kategoria)))
        producers = ["Wszyscy"] + sorted(list(set(m.producent for m in all_models if m.producent)))

        f_cat = c2.selectbox("Kategoria", categories)
        f_prod = c3.selectbox("Producent", producers)

        price_range = st.slider("Zakres ceny za dobę (zł)", 0, 1000, (0, 1000))

        if st.button("Resetuj filtry", use_container_width=True):
            st.rerun()

    # --- LISTA ---
    tool_models = crud.list_tool_models_extended(
        db, search=search_q, cat=f_cat, prod=f_prod,
        min_price=price_range[0], max_price=price_range[1]
    )

    if not tool_models:
        st.info("Nie znaleziono modeli spełniających kryteria.")
    else:
        # Nagłówki tabeli
        h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 1.5])
        h1.write("**Nazwa / Producent**")
        h2.write("**Kategoria**")
        h3.write("**Cena**")
        h4.write("**Kaucja**")
        h5.write("**Akcje**")
        st.divider()

        for m in tool_models:
            r1, r2, r3, r4, r5 = st.columns([2, 1, 1, 1, 1.5])
            r1.write(f"**{m.nazwa_modelu}** \n_{m.producent}_")
            r2.write(m.kategoria)
            r3.write(f"{m.cena_za_dobe} zł")
            r4.write(f"{m.kaucja} zł")

            with r5:
                ca1, ca2 = st.columns(2)
                if ca1.button("Edytuj", key=f"edit_m_{m.id}"):
                    tool_model_dialog(db, m)

                # Przycisk wycofaj
                if ca2.button("Wycofaj", key=f"with_m_{m.id}", type="secondary"):
                    withdraw_confirm_dialog(db, m)

    st.divider()
    if st.button("➕ Dodaj nowy model narzędzia", type="primary"):
        tool_model_dialog(db)

def render_analytics_section(db):
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

def render_export_section(db):
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


def show_clean_pydantic_error(e: ValidationError):
    """Przetwarza techniczny błąd Pydantic na czytelny komunikat Streamlit."""
    for error in e.errors():
        # Pobieramy nazwę pola (np. 'pesel') i typ błędu
        field = error['loc'][-1]
        msg = error['msg']

        # Opcjonalne tłumaczenie najczęstszych błędów
        friendly_msg = msg
        if "at least 11 characters" in msg:
            friendly_msg = "musi mieć dokładnie 11 cyfr."
        elif "value is not a valid email" in msg:
            friendly_msg = "ma niepoprawny format adresu e-mail."

        st.error(f"❌ Pole **{field.capitalize()}** {friendly_msg}")