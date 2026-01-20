# app/frontend/views/warehouse_view.py
import streamlit as st
from app.backend import crud
from app.backend import models


@st.dialog("Zarejestruj dostawę narzędzi")
def receive_delivery_dialog(db, available_models):
    st.write("Wybierz model i podaj liczbę sztuk, które fizycznie przyjechały do magazynu.")

    model_options = {f"{m.ModelNarzedzia.producent} {m.ModelNarzedzia.nazwa_modelu}": m.ModelNarzedzia.id for m in
                     available_models}

    with st.form("delivery_form"):
        st.markdown("<style>[data-testid='stForm'] small {display:none !important;}</style>", unsafe_allow_html=True)

        selected_label = st.selectbox("Model narzędzia*", list(model_options.keys()))
        quantity = st.number_input("Liczba nowych sztuk*", min_value=1, max_value=100, value=1)

        st.info("Po zatwierdzeniu, system wygeneruje nowe unikalne ID dla każdego egzemplarza.")

        if st.form_submit_button("Zatwierdź dostawę", use_container_width=True):
            try:
                model_id = model_options[selected_label]
                crud.bulk_create_items(db, model_id, int(quantity))
                st.success(f"Pomyślnie zarejestrowano dostawę {quantity} sztuk.")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd: {str(e)}")


def render_receive_resources(db):
    st.header("📥 Przyjmij zasoby")

    # Pobieranie danych (Modele + liczba sztuk)
    model_data = crud.list_models_with_counts(db)

    # --- FILTRY ---
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        s_text = c1.text_input("🔍 Szukaj modelu...")

        all_cats = ["Wszystkie"] + sorted(list(set(m.ModelNarzedzia.kategoria for m in model_data)))
        all_prods = ["Wszyscy"] + sorted(list(set(m.ModelNarzedzia.producent for m in model_data)))

        f_cat = c2.selectbox("Kategoria", all_cats)
        f_prod = c3.selectbox("Producent", all_prods)

    # --- TABELA (Zgodnie z wymaganiem) ---
    h1, h2, h3, h4, h5 = st.columns([0.7, 2, 1.2, 1.2, 1])
    h1.write("**ID_MODELU**")
    h2.write("**NAZWA**")
    h3.write("**KATEGORIA**")
    h4.write("**PRODUCENT**")
    h5.write("**LICZBA SZTUK**")
    st.divider()

    # Logika wyświetlania wierszy z filtrowaniem
    for m in model_data:
        # Filtrowanie lokalne
        if s_text.lower() not in m.ModelNarzedzia.nazwa_modelu.lower(): continue
        if f_cat != "Wszystkie" and m.ModelNarzedzia.kategoria != f_cat: continue
        if f_prod != "Wszyscy" and m.ModelNarzedzia.producent != f_prod: continue

        col1, col2, col3, col4, col5 = st.columns([0.7, 2, 1.2, 1.2, 1])
        col1.write(f"`{m.ModelNarzedzia.id}`")
        col2.write(m.ModelNarzedzia.nazwa_modelu)
        col3.write(m.ModelNarzedzia.kategoria)
        col4.write(m.ModelNarzedzia.producent)
        col5.write(f"**{m.liczba_sztuk}**")

    st.divider()
    # ZIELONY PRZYCISK (Streamlit type="primary" jest domyślnie niebieski, ale w Twoim motywie może być zielony)
    if st.button("➕ ZAREJESTRUJ DOSTAWĘ", type="primary", use_container_width=True):
        receive_delivery_dialog(db, model_data)


def render_loans_section(db):
    st.header("📦 Obsługa Wypożyczeń i Zwrotów")

    # 1. Pobieranie danych
    operations = crud.list_pending_operations(db)

    # 2. FILTRY I SEARCH
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        search_q = c1.text_input("🔍 Szukaj klienta lub modelu...", placeholder="Np. Kowalski...")

        f_typ = c2.selectbox("Typ operacji", ["Wszystkie", "WYDANIE", "ZWROT"])

        # Dynamiczne listy do filtrów
        clients = ["Wszystkie"] + sorted(list(set(op["klient"] for op in operations)))
        f_klient = c3.selectbox("Klient", clients)

        if st.button("Resetuj filtry", use_container_width=True):
            st.rerun()

    # 3. LOGIKA FILTROWANIA
    filtered = operations
    if search_q:
        filtered = [op for op in filtered if
                    search_q.lower() in op["klient"].lower() or search_q.lower() in op["model"].lower()]
    if f_typ != "Wszystkie":
        filtered = [op for op in filtered if op["typ"] == f_typ]
    if f_klient != "Wszystkie":
        filtered = [op for op in filtered if op["klient"] == f_klient]

    # 4. TABELA
    if not filtered:
        st.info("Brak oczekujących operacji spełniających kryteria.")
    else:
        # Nagłówki
        h1, h2, h3, h4, h5, h6 = st.columns([0.5, 1, 1.2, 1.5, 1.5, 1.2])
        h1.write("**ID**")
        h2.write("**TYP**")
        h3.write("**PLANOWANA DATA**")
        h4.write("**KLIENT**")
        h5.write("**MODEL NARZĘDZIA**")
        h6.write("**AKCJA**")
        st.divider()

        for op in filtered:
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 1, 1.2, 1.5, 1.5, 1.2])

            col1.write(f"`{op['id']}`")

            # Kolorowanie typu
            typ_color = "blue" if op["typ"] == "WYDANIE" else "orange"
            col2.markdown(f":{typ_color}[**{op['typ']}**]")

            col3.write(op["data_planowana"].strftime("%d.%m.%Y %H:%M"))
            col4.write(op["klient"])
            col5.write(op["model"])

            with col6:
                if op["typ"] == "WYDANIE":
                    if st.button("Zarejestruj wydanie", key=f"out_{op['id']}", use_container_width=True,
                                 type="primary"):
                        crud.process_rental_action(db, op["id"], "WYDANE")
                        st.success(f"Wydano wypożyczenie #{op['id']}")
                        st.rerun()

                elif op["typ"] == "ZWROT":  # Zmiana z 'else' na 'elif' sprawdzający typ operacji
                    if st.button("Zarejestruj zwrot", key=f"in_{op['id']}", use_container_width=True):
                        crud.process_rental_action(db, op["id"], "ZAKOŃCZONA")
                        st.success(f"Odebrano zwrot #{op['id']}")
                        st.rerun()


def render_browse_tools_section(db):
    st.header("🔍 Przeglądaj i zarządzaj narzędziami")

    # 1. Pobieranie danych (Egzemplarze + Modele)
    items = db.query(models.EgzemplarzNarzedzia).join(models.ModelNarzedzia).all()

    # 2. FILTRY I SEARCH
    with st.container(border=True):
        # Zmieniono układ na 5 kolumn, aby zmieścić nowy filtr
        c1, c2, c3, c4, c5 = st.columns([1.5, 1, 1, 1, 1])
        search_q = c1.text_input("🔍 Szukaj (Model lub SN)", placeholder="Wpisz nazwę...")

        # Dynamiczne listy do filtrów
        categories = ["Wszystkie"] + sorted(list(set(i.model.kategoria for i in items if i.model.kategoria)))
        producers = ["Wszyscy"] + sorted(list(set(i.model.producent for i in items if i.model.producent)))
        statuses = ["Wszystkie", "W_MAGAZYNIE", "U_KLIENTA", "W_WARSZTACIE"]
        # Lista dostępnych stanów technicznych
        technical_states = ["Wszystkie", "SPRAWNY", "AWARIA", "WYMAGA_PRZEGLADU"]

        f_cat = c2.selectbox("Kategoria", categories)
        f_prod = c3.selectbox("Producent", producers)
        f_stat = c4.selectbox("Lokalizacja", statuses)
        f_stan = c5.selectbox("Stan techniczny", technical_states)

    # 3. LOGIKA FILTROWANIA
    filtered = items
    if search_q:
        filtered = [i for i in filtered if
                    search_q.lower() in i.model.nazwa_modelu.lower() or search_q.lower() in i.numer_seryjny.lower()]
    if f_cat != "Wszystkie":
        filtered = [i for i in filtered if i.model.kategoria == f_cat]
    if f_prod != "Wszyscy":
        filtered = [i for i in filtered if i.model.producent == f_prod]
    if f_stat != "Wszystkie":
        filtered = [i for i in filtered if i.status == f_stat]
    # NOWY FILTR: Filtrowanie po stanie technicznym
    if f_stan != "Wszystkie":
        filtered = [i for i in filtered if i.stan_techniczny == f_stan]

    # 4. TABELA
    if not filtered:
        st.info("Brak egzemplarzy spełniających wybrane kryteria.")
    else:
        h1, h2, h3, h4, h5, h6, h7 = st.columns([0.5, 1.5, 1, 1, 1, 1, 1.8])
        h1.write("**ID**")
        h2.write("**MODEL**")
        h3.write("**SN**")
        h4.write("**STAN**")
        h5.write("**STATUS**")
        h6.write("**AKCJA**")
        h7.write("**ZATWIERDŹ**")
        st.divider()

        for i in filtered:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 1.5, 1, 1, 1, 1, 1.8])
            col1.write(f"`{i.id}`")
            col2.write(i.model.nazwa_modelu)
            col3.write(f"`{i.numer_seryjny}`")

            # Kolorowanie stanu technicznego
            s_color = {"SPRAWNY": "green", "AWARIA": "red", "WYMAGA_PRZEGLADU": "orange"}.get(i.stan_techniczny, "gray")
            col4.markdown(f":{s_color}[{i.stan_techniczny}]")
            col5.write(i.status)

            # --- LOGIKA WYBORU AKCJI (Combobox) ---
            options = ["Brak akcji"]

            if i.status == "W_MAGAZYNIE":
                if i.stan_techniczny == "SPRAWNY":
                    options.append("Oznacz: Wymaga przeglądu")
                elif i.stan_techniczny == "WYMAGA_PRZEGLADU":
                    options.append("Cofnij: Oznacz jako sprawny")
                    options.append("Przekaż: Do serwisu")
                elif i.stan_techniczny == "AWARIA":
                    options.append("Przekaż: Do serwisu")

            elif i.status == "W_WARSZTACIE":
                options.append("Odbierz: Przyjmij z serwisu")

            elif i.status == "U_KLIENTA":
                options.append("Zablokowane (U klienta)")

            with col6:
                action = st.selectbox("Wybierz...", options, key=f"sel_{i.id}", label_visibility="collapsed")

            with col7:
                if action != "Brak akcji" and not action.startswith("Zablokowane"):
                    if st.button("✅ Wykonaj", key=f"btn_{i.id}", use_container_width=True):
                        # Realizacja wybranej akcji
                        if action == "Oznacz: Wymaga przeglądu":
                            crud.update_technical_state(db, i.id, "WYMAGA_PRZEGLADU")
                        elif action == "Cofnij: Oznacz jako sprawny":
                            crud.update_technical_state(db, i.id, "SPRAWNY")
                        elif action == "Przekaż: Do serwisu":
                            crud.update_item_status(db, i.id, "W_WARSZTACIE")
                        elif action == "Odbierz: Przyjmij z serwisu":
                            crud.receive_from_service(db, i.id)

                        st.rerun()


def show_warehouseman_ui(db, user, section):
    if section == "Wypożyczenia":
        render_loans_section(db)
    elif section == "Przyjmij zasoby":
        render_receive_resources(db)
    elif section == "Przeglądaj narzędzia":
        render_browse_tools_section(db)
