import streamlit as st


# --- FUNKCJE CACHE ---

@st.cache_data(ttl=300)  # Cache na 5 minut
def get_cached_summary(_api):
    resp = _api.get("/inventory/models/summary")
    return resp.json() if resp and resp.status_code == 200 else []


@st.cache_data(ttl=60)  # Krótszy cache dla wypożyczeń, bo tu ruch jest większy
def get_cached_pending_rentals(_api):
    resp = _api.get("/rentals/pending")
    return resp.json() if resp and resp.status_code == 200 else []


@st.cache_data(ttl=300)
def get_cached_items(_api):
    resp = _api.get("/inventory/items")
    return resp.json() if resp and resp.status_code == 200 else []


# --- DIALOGI ---

@st.dialog("Zarejestruj dostawę narzędzi")
def receive_delivery_dialog(api, available_models):
    st.write("Wybierz model i podaj liczbę sztuk.")

    model_options = {
        f"{m['ModelNarzedzia']['producent']} {m['ModelNarzedzia']['nazwa_modelu']}": m['ModelNarzedzia']['id']
        for m in available_models
    }

    with st.form("delivery_form"):
        selected_label = st.selectbox("Model narzędzia*", list(model_options.keys()))
        quantity = st.number_input("Liczba nowych sztuk*", min_value=1, max_value=100, value=1)

        if st.form_submit_button("Zatwierdź dostawę", use_container_width=True):
            model_id = model_options[selected_label]
            resp = api.post("/inventory/items/bulk", params={"model_id": model_id, "quantity": int(quantity)})

            if resp and resp.status_code == 201:
                st.cache_data.clear()
                st.success(f"Pomyślnie zarejestrowano dostawę.")
                st.rerun()
            else:
                st.error("Błąd podczas rejestracji dostawy.")


# --- SEKCJE RENDEROWANIA ---

def render_receive_resources(api):
    st.header("📥 Przyjmij zasoby")

    # POBIERANIE Z CACHE
    model_data = get_cached_summary(api)

    if model_data:
        # DYNAMICZNE FILTRY
        all_cats = ["Wszystkie"] + sorted(list(set(m['ModelNarzedzia']['kategoria'] for m in model_data)))
        all_prods = ["Wszyscy"] + sorted(list(set(m['ModelNarzedzia']['producent'] for m in model_data)))

        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            s_text = c1.text_input("🔍 Szukaj modelu...")
            f_cat = c2.selectbox("Kategoria", all_cats)
            f_prod = c3.selectbox("Producent", all_prods)

        st.divider()
        h1, h2, h3, h4, h5 = st.columns([0.7, 2, 1.2, 1.2, 1])
        h1.write("**ID**");
        h2.write("**NAZWA**");
        h3.write("**KAT.**");
        h4.write("**PROD.**");
        h5.write("**SZTUK**")

        for m in model_data:
            model = m['ModelNarzedzia']
            if s_text.lower() not in model['nazwa_modelu'].lower(): continue
            if f_cat != "Wszystkie" and model['kategoria'] != f_cat: continue
            if f_prod != "Wszyscy" and model['producent'] != f_prod: continue

            col1, col2, col3, col4, col5 = st.columns([0.7, 2, 1.2, 1.2, 1])
            col1.write(f"`{model['id']}`");
            col2.write(model['nazwa_modelu'])
            col3.write(model['kategoria']);
            col4.write(model['producent'])
            col5.write(f"**{m['liczba_sztuk']}**")

        if st.button("➕ ZAREJESTRUJ DOSTAWĘ", type="primary", use_container_width=True):
            receive_delivery_dialog(api, model_data)


def render_loans_section(api):
    st.header("📦 Obsługa Wypożyczeń i Zwrotów")

    # POBIERANIE Z CACHE
    operations = get_cached_pending_rentals(api)

    if operations:
        all_clients = ["Wszystkie"] + sorted(list(set(op["klient"] for op in operations)))
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            search_q = c1.text_input("🔍 Szukaj (Klient/Model)...")
            f_typ = c2.selectbox("Typ operacji", ["Wszystkie", "WYDANIE", "ZWROT"])
            f_klient = c3.selectbox("Klient", all_clients)

        filtered = [op for op in operations if
                    (search_q.lower() in op["klient"].lower() or search_q.lower() in op["model"].lower()) and
                    (f_typ == "Wszystkie" or op["typ"] == f_typ) and
                    (f_klient == "Wszystkie" or op["klient"] == f_klient)]

        if not filtered:
            st.info("Brak oczekujących operacji.")
        else:
            st.divider()
            for op in filtered:
                c1, c2, c3, c4, c5, c6 = st.columns([0.5, 1, 1.2, 1.5, 1.5, 1.2])
                c1.write(f"`{op['id']}`")
                typ_color = "blue" if op["typ"] == "WYDANIE" else "orange"
                c2.markdown(f":{typ_color}[**{op['typ']}**]")
                c3.write(op['data_planowana'].split("T")[0])
                c4.write(op["klient"]);
                c5.write(op["model"])

                with c6:
                    target_status = "WYDANE" if op["typ"] == "WYDANIE" else "ZAKOŃCZONA"
                    if st.button("Zatwierdź", key=f"act_{op['id']}", use_container_width=True, type="primary"):
                        res = api.post(f"/rentals/{op['id']}/process", params={"action": target_status})
                        if res:
                            st.cache_data.clear()  # CZYSZCZENIE: Status wypożyczenia się zmienił
                            st.rerun()


def render_browse_tools_section(api):
    st.header("🔍 Zarządzaj egzemplarzami")

    # POBIERANIE Z CACHE
    items = get_cached_items(api)

    if items:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            search = c1.text_input("🔍 Szukaj (SN/Model)...")
            f_loc = c2.selectbox("Lokalizacja", ["Wszystkie", "W_MAGAZYNIE", "U_KLIENTA", "W_WARSZTACIE"])
            f_stan = c3.selectbox("Stan techniczny", ["Wszystkie", "SPRAWNY", "AWARIA", "WYMAGA_PRZEGLADU"])

        # Filtrowanie lokalne
        filtered = [i for i in items if
                    (search.lower() in i['model_name'].lower() or search.lower() in i['sn'].lower()) and
                    (f_loc == "Wszystkie" or i['status'] == f_loc) and
                    (f_stan == "Wszystkie" or i['stan'] == f_stan)]

        for i in filtered:
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 1.5, 1, 1, 1, 2.5])
            col1.write(f"`{i['id']}`");
            col2.write(i['model_name']);
            col3.write(f"`{i['sn']}`")

            s_color = {"SPRAWNY": "green", "AWARIA": "red", "WYMAGA_PRZEGLADU": "orange"}.get(i['stan'], "gray")
            col4.markdown(f":{s_color}[{i['stan']}]");
            col5.write(i['status'])

            with col6:
                c_act, c_exe = st.columns([2, 1])
                options = ["Brak akcji"]
                if i['status'] == "W_MAGAZYNIE":
                    if i['stan'] == "SPRAWNY": options += ["Zgłoś awarię", "Wymaga przeglądu"]
                    if i['stan'] in ["AWARIA", "WYMAGA_PRZEGLADU"]: options += ["Przekaż do serwisu"]
                elif i['status'] == "W_WARSZTACIE":
                    options += ["Odbierz z serwisu"]

                action = c_act.selectbox("Akcja", options, key=f"sel_{i['id']}", label_visibility="collapsed")
                if action != "Brak akcji":
                    if c_exe.button("OK", key=f"btn_{i['id']}"):
                        success = False
                        if action == "Zgłoś awarię":
                            success = api.patch(f"/inventory/items/{i['id']}/state", params={"new_state": "AWARIA"})
                        elif action == "Wymaga przeglądu":
                            success = api.patch(f"/inventory/items/{i['id']}/state",
                                                params={"new_state": "WYMAGA_PRZEGLADU"})
                        elif action == "Przekaż do serwisu":
                            success = api.post(f"/inventory/items/{i['id']}/send-to-service")
                        elif action == "Odbierz z serwisu":
                            success = api.post(f"/inventory/items/{i['id']}/receive-from-service")

                        if success:
                            st.cache_data.clear()  # CZYSZCZENIE
                            st.rerun()


def show_warehouseman_ui(api, user, section):
    if st.sidebar.button("🔄 Odśwież dane"):
        st.cache_data.clear()
        st.rerun()

    if section == "📦 Wypożyczenia":
        render_loans_section(api)
    elif section == "📥 Przyjmij zasoby":
        render_receive_resources(api)
    elif section == "🔍 Przeglądaj narzędzia":
        render_browse_tools_section(api)
