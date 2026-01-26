import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from pydantic import ValidationError


# --- FUNKCJE CACHE ---

@st.cache_data(ttl=600)
def get_cached_employees(_api):
    resp = _api.get("/users/employees")
    return resp.json() if resp and resp.status_code == 200 else []


@st.cache_data(ttl=600)
def get_cached_models(_api):
    resp = _api.get("/inventory/models")
    return resp.json() if resp and resp.status_code == 200 else []


@st.cache_data(ttl=60)
def get_cached_analytics(_api, date_from, date_to):
    params = {"date_from": str(date_from), "date_to": str(date_to)}
    resp = _api.get("/analytics/summary", params=params)
    return resp.json() if resp and resp.status_code == 200 else None


# --- HELPERY DO BŁĘDÓW ---
def show_clean_pydantic_error(errors):
    if hasattr(errors, 'errors'):
        error_list = errors.errors()
    elif isinstance(errors, list):
        error_list = errors
    else:
        st.error(f"❌ Wystąpił nieoczekiwany błąd: {errors}")
        return

    translations = {
        "string_too_short": "jest za krótkie (min. {min_length} znaków).",
        "string_too_long": "jest za długie (max. {max_length} znaków).",
        "value_error.missing": "jest wymagane.",
        "assertion_error": "ma niepoprawną wartość.",
        "value_error.email": "musi być poprawnym adresem e-mail."
    }

    for err in error_list:
        field_raw = err['loc'][-1]
        field_name = field_raw.replace("_", " ").capitalize()
        err_type = err.get('type', '')
        ctx = err.get('ctx', {})
        msg = translations.get(err_type, err.get('msg', 'niepoprawne dane.'))
        if "{" in msg:
            msg = msg.format(**ctx)
        st.error(f"⚠️ **{field_name}**: {msg}")


# --- DIALOGI ---

@st.dialog("Zarządzaj Modelem Narzędzia")
def tool_model_dialog(api, model=None):
    from app.backend.modules.inventory import schemas as inv_schemas
    mode = "Edytuj" if model else "Dodaj"
    st.subheader(f"{mode} model narzędzia")
    m = model if model else {}

    with st.form("tool_model_form"):
        nazwa = st.text_input("Nazwa modelu", value=m.get('nazwa_modelu', ""))
        prod = st.text_input("Producent", value=m.get('producent', ""))
        kat = st.text_input("Kategoria", value=m.get('kategoria', ""))
        opis = st.text_area("Opis", value=m.get('opis', ""))
        c1, c2 = st.columns(2)
        val_cena = float(m.get('cena_za_dobe', 50.0))
        val_kaucja = float(m.get('kaucja', 100.0))
        cena = c1.number_input("Cena za dobę (zł)", min_value=0.0, value=val_cena)
        kaucja = c2.number_input("Kaucja (zł)", min_value=0.0, value=val_kaucja)

        if st.form_submit_button("Zapisz", use_container_width=True):
            try:
                payload = inv_schemas.ToolModelCreate(
                    nazwa_modelu=nazwa, producent=prod, kategoria=kat,
                    opis=opis, cena_za_dobe=cena, kaucja=kaucja
                )
                p_json = payload.model_dump(mode='json')

                if model:
                    resp = api.patch(f"/inventory/models/{m['id']}", data=p_json)
                else:
                    resp = api.post("/inventory/models", data=p_json)

                if resp is not None and resp.status_code in [200, 201]:
                    st.cache_data.clear()
                    st.success("✅ Zapisano pomyślnie!")
                    st.rerun()
                elif resp is not None:
                    show_clean_pydantic_error(resp.json().get('detail', []))
            except ValidationError as e:
                show_clean_pydantic_error(e)


@st.dialog("Potwierdź wycofanie")
def withdraw_confirm_dialog(api, model):
    st.warning(f"Czy na pewno chcesz wycofać model: **{model['nazwa_modelu']}**?")
    if st.button("Potwierdzam wycofanie", type="primary", use_container_width=True):
        resp = api.patch(f"/inventory/models/{model['id']}", data={"wycofany": True})
        if resp and resp.status_code == 200:
            st.cache_data.clear()
            st.success("Model wycofany!")
            st.rerun()
        else:
            st.error("Nie udało się wycofać modelu.")


@st.dialog("Edycja danych pracownika")
def edit_employee_dialog(emp, api):
    st.write(f"Edytujesz profil: **{emp['imie']} {emp['nazwisko']}**")
    with st.form("edit_form_modal"):
        c1, c2 = st.columns(2)
        new_imie = c1.text_input("Imię*", value=emp['imie'])
        new_nazwisko = c2.text_input("Nazwisko*", value=emp['nazwisko'])
        new_email = c1.text_input("Email*", value=emp['email'] or "")
        new_tel = c2.text_input("Telefon", value=emp['telefon'] or "")
        new_adres = st.text_input("Adres zamieszkania", value=emp['adres'] or "")
        roles = ["KIEROWNIK", "MAGAZYNIER", "SERWISANT"]
        new_rola = st.selectbox("Rola systemowa", roles, index=roles.index(emp['rola']) if emp['rola'] in roles else 0)

        if st.form_submit_button("Zapisz zmiany", use_container_width=True):
            try:
                from app.backend.modules.users import schemas as user_schemas
                update_data = user_schemas.EmployeeUpdate(
                    imie=new_imie, nazwisko=new_nazwisko, email=new_email,
                    telefon=new_tel if new_tel else None,
                    adres=new_adres if new_adres else None, rola=new_rola
                )
                resp = api.patch(f"/users/employees/{emp['id']}", data=update_data.model_dump())
                if resp and resp.status_code == 200:
                    st.cache_data.clear()  # Czyścimy cache pracowników
                    st.success("Zaktualizowano dane!")
                    st.rerun()
                else:
                    show_clean_pydantic_error(resp.json().get('detail', []))
            except ValidationError as e:
                show_clean_pydantic_error(e)


# --- GŁÓWNE SEKCJE ---

def render_employees_section(api):
    from app.backend.modules.users import schemas as user_schemas
    st.header("👷 Zarządzanie Kadrami")

    with st.expander("➕ Dodaj nowego pracownika"):
        with st.form("add_employee_new"):
            c1, c2 = st.columns(2)
            imie = c1.text_input("Imię")
            nazwisko = c2.text_input("Nazwisko")
            c3, c4 = st.columns(2)
            pesel = c3.text_input("PESEL (11 cyfr)")
            email = c4.text_input("Adres Email")
            c5, c6 = st.columns(2)
            login = c5.text_input("Login")
            haslo = c6.text_input("Hasło", type="password")
            c7, c8 = st.columns(2)
            telefon = c7.text_input("Numer telefonu")
            rola = c8.selectbox("Rola systemowa", ["KIEROWNIK", "MAGAZYNIER", "SERWISANT"])
            adres = st.text_input("Adres zamieszkania (Ulica, nr, miasto)")

            if st.form_submit_button("🚀 Utwórz konto pracownicze", use_container_width=True):
                try:
                    payload = user_schemas.EmployeeCreate(
                        imie=imie, nazwisko=nazwisko, pesel=pesel, email=email,
                        login=login, haslo=haslo, rola=rola, adres=adres,
                        telefon=telefon, data_zatrudnienia=None
                    )
                    resp = api.post("/users/employees", data=payload.model_dump(mode='json'))
                    if resp and resp.status_code == 201:
                        st.cache_data.clear()
                        st.success(f"✅ Dodano pracownika!")
                        st.rerun()
                    elif resp:
                        show_clean_pydantic_error(resp.json().get('detail', []))
                except ValidationError as e:
                    show_clean_pydantic_error(e)

    st.divider()
    employees = get_cached_employees(api)  # POBIERANIE Z CACHE
    if employees:
        for e in employees:
            with st.expander(f"👤 {e['imie']} {e['nazwisko']} — **{e['rola']}**"):
                col1, col2, col3 = st.columns([1.5, 1.5, 1])
                with col1:
                    st.write(f"📧 **Email:** {e.get('email', 'brak')}")
                    st.write(f"📞 **Tel:** {e.get('telefon', 'brak')}")
                with col2:
                    st.write(f"🔑 **Login:** `{e.get('login', 'n/a')}`")
                    st.write(f"🏠 **Adres:** {e.get('adres', 'brak')}")
                with col3:
                    if st.button("✏️ Edytuj", key=f"ed_emp_{e['id']}", use_container_width=True):
                        edit_employee_dialog(e, api)
                    if st.button("🗑️ Usuń", key=f"del_emp_{e['id']}", type="secondary", use_container_width=True):
                        if api.delete(f"/users/employees/{e['id']}"):
                            st.cache_data.clear()
                            st.toast(f"Usunięto konto: {e['imie']}")
                            st.rerun()


def render_models_section(api):
    st.header("🧰 Katalog Modeli")
    all_data = get_cached_models(api)  # POBIERANIE Z CACHE
    if not all_data:
        st.info("Brak modeli. Dodaj pierwszy model poniżej.")
    else:
        models_list = [m['ModelNarzedzia'] for m in all_data]
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            search_q = c1.text_input("🔍 Szukaj modelu")
            categories = ["Wszystkie"] + sorted(list(set(m['kategoria'] for m in models_list)))
            producers = ["Wszyscy"] + sorted(list(set(m['producent'] for m in models_list)))
            f_cat = c2.selectbox("Kategoria", categories)
            f_prod = c3.selectbox("Producent", producers)
            price_range = st.slider("Zakres ceny za dobę (zł)", 0, 2000, (0, 2000))

        filtered = [m for m in models_list if
                    (search_q.lower() in m['nazwa_modelu'].lower()) and
                    (f_cat == "Wszystkie" or m['kategoria'] == f_cat) and
                    (f_prod == "Wszyscy" or m['producent'] == f_prod) and
                    (price_range[0] <= m['cena_za_dobe'] <= price_range[1])]

        st.divider()
        for m in filtered:
            r1, r2, r3, r4, r5 = st.columns([2, 1, 1, 1, 1.5])
            r1.write(f"**{m['nazwa_modelu']}** \n_{m['producent']}_")
            r2.write(m['kategoria']);
            r3.write(f"{m['cena_za_dobe']} zł");
            r4.write(f"{m['kaucja']} zł")
            with r5:
                if st.button("✏️ Edytuj", key=f"edm_{m['id']}", use_container_width=True):
                    tool_model_dialog(api, m)

    st.divider()
    if st.button("➕ Dodaj nowy model", type="primary", use_container_width=True):
        tool_model_dialog(api)


def render_analytics_section(api):
    st.header("📊 Statystyki i Raporty")

    c1, c2 = st.columns(2)
    d_from = c1.date_input("Od", date.today() - timedelta(days=30))
    d_to = c2.date_input("Do", date.today())

    summary = api.get("/analytics/summary", params={"date_from": d_from, "date_to": d_to}).json()
    top_models = api.get("/analytics/top-models", params={"limit": 10}).json()
    categories = api.get("/analytics/categories").json()

    if summary:
        m1, m2 = st.columns(2)
        m1.metric("Łącznie rezerwacji", summary['total_rentals'])
        m2.metric("Całkowity przychód", f"{summary['total_revenue']:.2f} zł")

        st.subheader("📈 Przychód dzień po dniu")
        if summary['daily_stats']:
            df_daily = pd.DataFrame(summary['daily_stats'])
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            df_daily = df_daily.set_index('date')
            st.area_chart(df_daily['revenue'], color="#34495E")
        else:
            st.info("Brak danych do wykresu czasowego.")

    tab1, tab2 = st.tabs(["🏆 Najpopularniejsze Modele", "📁 Struktura Kategorii"])

    with tab1:
        if top_models:
            df_models = pd.DataFrame(top_models)
            st.bar_chart(df_models.set_index("model_name"), horizontal=True, color="#FF4B4B")
        else:
            st.write("Brak danych.")

    with tab2:
        if categories:
            df_cat = pd.DataFrame(categories)
            st.bar_chart(df_cat.set_index("kategoria"), color="#34495E")


def render_export_section(api):
    st.header("⬇️ Eksport")
    table = st.selectbox("Tabela", ["pracownicy", "modele_narzedzi", "wypozyczenia"])
    if st.button("Generuj i pobierz", use_container_width=True):
        resp = api.get(f"/analytics/export/{table}")
        if resp:
            st.download_button("Pobierz CSV", data=resp.content, file_name=f"{table}.csv")


def show_manager_ui(api, section):
    if st.sidebar.button("🔄 Odśwież wszystkie dane"):
        st.cache_data.clear()
        st.rerun()

    if section == "Pracownicy":
        render_employees_section(api)
    elif section == "Modele":
        render_models_section(api)
    elif section == "Analiza":
        render_analytics_section(api)
    elif section == "Eksport":
        render_export_section(api)
