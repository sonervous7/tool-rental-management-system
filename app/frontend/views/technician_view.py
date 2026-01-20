import streamlit as st
from app.backend import crud, models
import datetime


# Reużywamy okno dialogowe (możesz je trzymać w tym pliku lub w osobnym module helpers)
@st.dialog("Rejestracja Czynności Serwisowej")
def service_action_dialog(db, item, user, rodzaj):
    tytuly = {
        "NAPRAWA": "🛠 Zarejestruj naprawę",
        "PRZEGLAD": "🔍 Zarejestruj przegląd",
        "NOTATKA": "📝 Dodaj notatkę techniczną"
    }
    st.subheader(tytuly.get(rodzaj, "Czynność"))
    st.write(f"Egzemplarz ID: **{item.id}** | Model: **{item.model.nazwa_modelu}**")

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
    st.title("🔧 Zarządzanie narzędziami")

    # --- FILTRY (Dynamiczne) ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        search_q = c1.text_input("🔍 Szukaj (Model lub SN)", placeholder="Np. Bosch...")

        # Pobieranie list do filtrów z bazy danych przez relację model
        all_items = db.query(models.EgzemplarzNarzedzia).all()
        categories = ["Wszystkie"] + sorted(list(set(i.model.kategoria for i in all_items if i.model.kategoria)))
        producers = ["Wszyscy"] + sorted(list(set(i.model.producent for i in all_items if i.model.producent)))

        f_cat = c2.selectbox("Kategoria", categories)
        f_prod = c3.selectbox("Producent", producers)
        f_stan = c4.selectbox("Stan techniczny", ["Wszystkie", "SPRAWNY", "AWARIA", "WYMAGA_PRZEGLADU"])

    # --- LOGIKA FILTROWANIA ---
    query = db.query(models.EgzemplarzNarzedzia).join(models.ModelNarzedzia)

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
        st.info("Brak egzemplarzy spełniających kryteria.")
    else:
        # Nagłówki
        h1, h2, h3, h4, h5 = st.columns([0.6, 2, 1.5, 1.5, 2])
        h1.write("**ID**")
        h2.write("**Nazwa modelu**")
        h3.write("**Producent**")
        h4.write("**Stan techniczny**")
        h5.write("**Dostępne akcje**")
        st.divider()

        for item in items:
            r1, r2, r3, r4, r5 = st.columns([0.6, 2, 1.5, 1.5, 2])

            r1.write(f"`{item.id}`")
            r2.write(item.model.nazwa_modelu)
            r3.write(item.model.producent)

            # Kolorowanie stanu
            color = {"SPRAWNY": "green", "AWARIA": "red", "WYMAGA_PRZEGLADU": "orange"}.get(item.stan_techniczny,
                                                                                            "gray")
            r4.markdown(f":{color}[{item.stan_techniczny}]")

            with r5:
                # Przyciski akcji zgodnie z PU
                c_fix, c_insp, c_note = st.columns(3)

                # Naprawa aktywna tylko przy Awarii
                if item.stan_techniczny == "AWARIA":
                    if c_fix.button("Naprawa", key=f"fix_{item.id}", help="Zarejestruj naprawę"):
                        service_action_dialog(db, item, user, "NAPRAWA")

                # Przegląd aktywny przy "Wymaga przeglądu" (lub zawsze, zależy od polityki)
                if item.stan_techniczny == "WYMAGA_PRZEGLADU":
                    if c_insp.button("Przegląd", key=f"insp_{item.id}", help="Zarejestruj przegląd"):
                        service_action_dialog(db, item, user, "PRZEGLAD")

                # Notatka zawsze dostępna
                if c_note.button("Notatka", key=f"note_{item.id}", help="Dodaj notatkę techniczną"):
                    service_action_dialog(db, item, user, "NOTATKA")
