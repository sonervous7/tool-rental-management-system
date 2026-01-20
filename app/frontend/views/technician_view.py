# app/frontend/views/technician_view.py
import streamlit as st
from app.backend import crud, models
import datetime


@st.dialog("Rejestracja Czynności Serwisowej")
def service_action_dialog(db, item, user, rodzaj):
    tytuly = {
        "NAPRAWA": "🛠 Zarejestruj naprawę",
        "PRZEGLAD": "🔍 Zarejestruj przegląd",
        "NOTATKA": "📝 Dodaj notatkę techniczną"
    }
    st.subheader(tytuly.get(rodzaj, "Czynność"))
    # Dodano Numer Seryjny do nagłówka okna
    st.write(f"Narzędzie: **{item.model.nazwa_modelu}**")
    st.write(f"ID: `{item.id}` | **SN: {item.numer_seryjny}**")

    with st.form("service_form_tech"):
        st.markdown("<style>[data-testid='stForm'] small {display:none !important;}</style>", unsafe_allow_html=True)

        opis = st.text_area("Opis wykonanych działań*" if rodzaj != "NOTATKA" else "Treść notatki*")

        nowy_stan = None
        if rodzaj in ["NAPRAWA", "PRZEGLAD"]:
            nowy_stan = st.selectbox("Status po serwisie", ["SPRAWNY", "AWARIA", "WYMAGA_PRZEGLADU"])

        if st.form_submit_button("Zatwierdź", use_container_width=True):
            if not opis.strip():
                st.error("Opis nie może być pusty!")
            else:
                try:
                    crud.add_service_action(
                        db=db, egzemplarz_id=item.id, serwisant_id=user.id,
                        rodzaj=rodzaj, notatka=opis, nowy_stan=nowy_stan
                    )
                    st.success("Zapisano pomyślnie!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")


def show_technician_ui(db, user):
    st.title("🔧 Zarządzanie narzędziami (Warsztat)")

    # 1. Pobieramy egzemplarze W_WARSZTACIE
    workshop_query = db.query(models.EgzemplarzNarzedzia).filter(
        models.EgzemplarzNarzedzia.status == "W_WARSZTACIE"
    )
    workshop_items_for_filters = workshop_query.all()

    # --- FILTRY ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        search_q = c1.text_input("🔍 Szukaj (Model lub SN)", placeholder="Np. Bosch lub SN123...")

        categories = ["Wszystkie"] + sorted(
            list(set(i.model.kategoria for i in workshop_items_for_filters if i.model.kategoria)))
        producers = ["Wszyscy"] + sorted(
            list(set(i.model.producent for i in workshop_items_for_filters if i.model.producent)))

        f_cat = c2.selectbox("Kategoria", categories)
        f_prod = c3.selectbox("Producent", producers)
        f_stan = c4.selectbox("Stan techniczny", ["Wszystkie", "AWARIA", "WYMAGA_PRZEGLADU"])

    # --- LOGIKA FILTROWANIA ---
    query = workshop_query.join(models.ModelNarzedzia)

    if search_q:
        query = query.filter(
            (models.ModelNarzedzia.nazwa_modelu.ilike(f"%{search_q}%")) |
            (models.EgzemplarzNarzedzia.numer_seryjny.ilike(f"%{search_q}%"))
        )
    if f_cat != "Wszystkie":
        query = query.filter(models.ModelNarzedzia.kategoria == f_cat)
    if f_prod != "Wszyscy":
        query = query.filter(models.ModelNarzedzia.producent == f_prod)
    if f_stan != "Wszystkie":
        query = query.filter(models.EgzemplarzNarzedzia.stan_techniczny == f_stan)

    items = query.all()

    # --- TABELA EGZEMPLARZY ---
    if not items:
        st.info("Obecnie w warsztacie nie ma żadnych narzędzi do serwisu.")
    else:
        # Dodano kolumnę dla SN (Numer Seryjny)
        h1, h2, h3, h4, h5, h6 = st.columns([0.5, 2, 1.2, 1, 1.2, 1.8])
        h1.write("**ID**")
        h2.write("**Model**")
        h3.write("**SN**")
        h4.write("**Cykle**")
        h5.write("**Stan**")
        h6.write("**Akcje**")
        st.divider()

        for item in items:
            r1, r2, r3, r4, r5, r6 = st.columns([0.5, 2, 1.2, 1, 1.2, 1.8])

            r1.write(f"`{item.id}`")
            r2.write(item.model.nazwa_modelu)
            # Wyświetlanie Numeru Seryjnego w tabeli
            r3.write(f"`{item.numer_seryjny}`")

            # Licznik wypożyczeń (pamiętaj o limicie 5)
            r4.write(f"{item.licznik_wypozyczen}/5")

            color = {"SPRAWNY": "green", "AWARIA": "red", "WYMAGA_PRZEGLADU": "orange"}.get(item.stan_techniczny,
                                                                                            "gray")
            r5.markdown(f":{color}[{item.stan_techniczny}]")

            with r6:
                c_fix, c_insp, c_note = st.columns(3)

                if item.stan_techniczny == "AWARIA":
                    if c_fix.button("🔧", key=f"fix_{item.id}", help="Naprawa"):
                        service_action_dialog(db, item, user, "NAPRAWA")

                if item.stan_techniczny == "WYMAGA_PRZEGLADU":
                    if c_insp.button("🔍", key=f"insp_{item.id}", help="Przegląd"):
                        service_action_dialog(db, item, user, "PRZEGLAD")

                if c_note.button("📝", key=f"note_{item.id}", help="Notatka"):
                    service_action_dialog(db, item, user, "NOTATKA")