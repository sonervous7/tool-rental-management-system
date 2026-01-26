import streamlit as st

# --- FUNKCJE CACHE ---

@st.cache_data(ttl=300)
def get_cached_workshop_items(_api):
    """Pobiera tylko te narzędzia, które fizycznie są w warsztacie."""
    resp = _api.get("/inventory/items", params={"location": "W_WARSZTACIE"})
    return resp.json() if resp and resp.status_code == 200 else []


# --- DIALOGI ---

@st.dialog("Zarejestruj Czynność Serwisowej")
def service_action_dialog(api, item, user, rodzaj):
    tytuly = {
        "NAPRAWA": "🛠 Zarejestruj naprawę",
        "PRZEGLAD": "🔍 Zarejestruj przegląd",
        "NOTATKA": "📝 Dodaj notatkę techniczną"
    }
    st.subheader(tytuly.get(rodzaj, "Czynność"))

    model_name = item.get('model_name', 'Nieznany model')
    item_id = item.get('id')
    sn = item.get('sn', 'Brak SN')

    st.write(f"Narzędzie: **{model_name}**")
    st.write(f"ID: `{item_id}` | **SN: {sn}**")

    with st.form("service_form_tech"):
        opis = st.text_area("Opis wykonanych działań*" if rodzaj != "NOTATKA" else "Treść notatki*")

        nowy_stan = None
        if rodzaj in ["NAPRAWA", "PRZEGLAD"]:
            nowy_stan = st.selectbox("Status po serwisie", ["SPRAWNY", "AWARIA", "WYMAGA_PRZEGLADU"])

        if st.form_submit_button("Zatwierdź", use_container_width=True):
            if not opis.strip():
                st.error("Opis nie może być pusty!")
            else:
                payload = {
                    "egzemplarz_id": item_id,
                    "serwisant_id": user['id'],
                    "rodzaj": rodzaj,
                    "notatka_opis": opis
                }

                params = {"nowy_stan": nowy_stan} if nowy_stan else {}
                resp = api.post("/rentals/service-action", data=payload, params=params)

                if resp and resp.status_code == 200:
                    st.cache_data.clear() # Czyścimy cache
                    st.success("Zapisano pomyślnie!")
                    st.rerun()
                else:
                    detail = resp.json().get('detail', 'Błąd zapisu') if resp else "Brak odpowiedzi API"
                    st.error(f"Błąd API: {detail}")


# --- GŁÓWNY WIDOK ---

def show_technician_ui(api, user):
    st.title("🔧 Zarządzanie narzędziami (Warsztat)")

    all_items = get_cached_workshop_items(api)

    if not all_items:
        st.info("Warsztat jest obecnie pusty. Wszystkie narzędzia są sprawne lub u klientów.")
        return

    categories = ["Wszystkie"] + sorted(list(set(i.get('category', 'Narzędzia') for i in all_items)))
    producers = ["Wszyscy"] + sorted(list(set(i.get('producer', 'Różni') for i in all_items)))

    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        search_q = c1.text_input("🔍 Szukaj po modelu lub numerze seryjnym")
        f_cat = c2.selectbox("Kategoria", categories)
        f_prod = c3.selectbox("Producent", producers)

    filtered = [
        i for i in all_items if
        (search_q.lower() in i['model_name'].lower() or search_q.lower() in i['sn'].lower()) and
        (f_cat == "Wszystkie" or i.get('category') == f_cat) and
        (f_prod == "Wszyscy" or i.get('producer') == f_prod)
    ]

    if not filtered:
        st.warning("Brak narzędzi pasujących do filtrów.")
    else:
        h1, h2, h3, h4, h5, h6 = st.columns([0.5, 2, 1.2, 1, 1.2, 1.8])
        h1.write("**ID**"); h2.write("**Model**"); h3.write("**SN**")
        h4.write("**Cykle**"); h5.write("**Stan**"); h6.write("**Akcje**")
        st.divider()

        for item in filtered:
            r1, r2, r3, r4, r5, r6 = st.columns([0.5, 2, 1.2, 1, 1.2, 1.8])

            r1.write(f"`{item['id']}`")
            r2.write(item['model_name'])
            r3.write(f"`{item['sn']}`")
            r4.write(f"{item['licznik']}/5")

            stan = item['stan'] # TU POPRAWKA
            color = {"SPRAWNY": "green", "AWARIA": "red", "WYMAGA_PRZEGLADU": "orange"}.get(stan, "gray")
            r5.markdown(f":{color}[{stan}]")
            with r6:
                c_fix, c_insp, c_note = st.columns(3)

                if item['stan'] == "AWARIA":
                    if c_fix.button("🔧", key=f"fix_{item['id']}", help="Naprawa"):
                        service_action_dialog(api, item, user, "NAPRAWA")

                if item['stan'] == "WYMAGA_PRZEGLADU":
                    if c_insp.button("🔍", key=f"insp_{item['id']}", help="Przegląd"):
                        service_action_dialog(api, item, user, "PRZEGLAD")

                if c_note.button("📝", key=f"note_{item['id']}", help="Notatka"):
                    service_action_dialog(api, item, user, "NOTATKA")