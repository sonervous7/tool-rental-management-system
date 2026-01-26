import streamlit as st
import datetime as dt
from datetime import datetime, timedelta
import time as py_time
from collections import Counter


# --- FUNKCJE CACHE ---

@st.cache_data(ttl=600)
def get_cached_catalog(_api):
    resp = _api.get("/inventory/models")
    return resp.json() if resp and resp.status_code == 200 else []


@st.cache_data(ttl=60)
def get_cached_history(_api, client_id):
    resp = _api.get(f"/rentals/customer/{client_id}")
    return resp.json() if resp and resp.status_code == 200 else []


@st.cache_data(ttl=60)
def get_cached_issued_items(_api, client_id):
    resp = _api.get(f"/rentals/customer/{client_id}/issued")
    return resp.json() if resp and resp.status_code == 200 else []


# --- DIALOGI ---

@st.dialog("Zgłoś awarię sprzętu")
def report_fault_dialog(api, item):
    pozycja_id = item.get('id')
    model_name = item.get('model_name', 'Nieznany model')
    sn = item.get('sn', 'Brak SN')

    st.error(f"⚠️ Zgłaszasz usterkę dla: **{model_name}**")
    st.caption(f"Numer seryjny: `{sn}` | ID Pozycji: `{pozycja_id}`")

    st.markdown("---")

    with st.form("fault_form"):
        opis = st.text_area(
            "Opisz dokładnie, co się stało*",
            placeholder="Np. silnik przestał kręcić, czuć spaleniznę, złamany uchwyt...",
            help="Opis pomoże serwisantowi szybciej naprawić narzędzie."
        )

        st.info("💡 Po zgłoszeniu narzędzie zostanie oznaczone jako AWARIA i będzie wymagało interwencji serwisu.")

        if st.form_submit_button("🚨 Wyślij zgłoszenie", use_container_width=True):
            if len(opis.strip()) < 5:
                st.warning("Proszę podać nieco dokładniejszy opis usterki.")
                return

            resp = api.post("/rentals/faults", params={
                "pozycja_id": pozycja_id,
                "opis": opis
            })

            if resp and resp.status_code == 200:
                st.success("Zgłoszenie zostało wysłane. Serwisant zajmie się sprawą.")
                st.cache_data.clear()
                st.rerun()
            else:
                detail = resp.json().get('detail', 'Nieznany błąd serwera') if resp else "Brak odpowiedzi API"
                st.error(f"Błąd: {detail}")


@st.dialog("Rezerwacja narzędzia")
def reserve_tool_dialog(api, model, user):
    st.subheader(f"🛒 {model['nazwa_modelu']}")

    c1, c2 = st.columns(2)
    d_start = c1.date_input("Planowana data odbioru", min_value=datetime.now().date())
    d_end = c2.date_input("Planowana data zwrotu", min_value=d_start + timedelta(days=1))

    dt_start = datetime.combine(d_start, dt.time.min).isoformat()
    dt_end = datetime.combine(d_end, dt.time.max).isoformat()

    resp = api.get(f"/inventory/models/{model['id']}/availability",
                   params={"start_dt": dt_start, "end_dt": dt_end})

    if resp and resp.status_code == 200:
        count = resp.json().get("count", 0)
        if count > 0:
            st.success(f"Dostępność w wybranym terminie: **{count} szt.**")
            quantity = st.number_input("Ile sztuk?", min_value=1, max_value=count, value=1)

            days = (d_end - d_start).days
            total_rent = days * model['cena_za_dobe'] * quantity
            total_kaucja = quantity * model.get('kaucja', 0)
            total_sum = total_rent + total_kaucja

            st.markdown("---")
            col_a, col_b = st.columns(2)

            with col_a:
                st.write("**Koszt najmu:**")
                st.write(f"({days} dni x {quantity} szt.)")
                st.subheader(f"{total_rent:.2f} PLN")

            with col_b:
                st.write("**Kaucja zwrotna:**")
                st.write(f"({quantity} szt. x {model.get('kaucja', 0)} zł)")
                st.subheader(f"{total_kaucja:.2f} PLN")

            st.warning(f"💡 Łączna kwota przy odbiorze: **{total_sum:.2f} PLN**")
            st.markdown("---")

            if st.button("Potwierdzam rezerwację", type="primary", use_container_width=True):
                res = api.post("/rentals/", params={
                    "client_id": user['id'],
                    "model_id": model['id'],
                    "qty": int(quantity),
                    "start_dt": dt_start,
                    "end_dt": dt_end
                })
                if res and res.status_code == 201:
                    st.cache_data.clear()
                    st.success("Rezerwacja zapisana!")
                    st.balloons()
                    st.rerun()
        else:
            st.error("Brak wolnych egzemplarzy w tym terminie.")


@st.dialog("Twoja opinia ma znaczenie!")
def add_opinion_dialog(api, user_id, model_id, model_name):
    st.write(f"Jak oceniasz narzędzie: **{model_name}**?")

    rating_index = st.feedback("stars")

    ocena = rating_index + 1 if rating_index is not None else None

    komentarz = st.text_area(
        "Napisz kilka słów o sprzęcie (opcjonalnie)",
        placeholder="Czy sprzęt spełnił oczekiwania?"
    )

    if st.button("Wyślij opinię", type="primary", use_container_width=True):
        if ocena is None:
            st.warning("Proszę zaznaczyć gwiazdki przed wysłaniem.")
            return

        if not komentarz.strip():
            st.warning("Dodaj chociaż krótki komentarz.")
            return

        resp = api.post("/rentals/opinions", params={
            "client_id": user_id,
            "model_id": model_id,
            "rating": ocena,
            "comment": komentarz
        })

        if resp and resp.status_code == 200:
            st.balloons()
            st.success("Dziękujemy! Twoja opinia została dodana.")

            st.cache_data.clear()

            py_time.sleep(2)
            st.rerun()
        else:
            st.error("Coś poszło nie tak przy zapisywaniu opinii.")


@st.dialog("Opinie użytkowników")
def show_opinions_dialog(api, model):
    st.subheader(f"Recenzje dla: {model['nazwa_modelu']}")

    resp = api.get(f"/inventory/models/{model['id']}/opinions")
    if resp and resp.status_code == 200:
        opinie = resp.json()
        if not opinie:
            st.info("Brak opinii dla tego modelu.")
        else:
            for o in opinie:
                with st.container(border=True):
                    st.markdown("⭐" * int(o['ocena']))
                    st.write(f"_{o['komentarz']}_")
                    autor = o.get('autor', 'Anonim')
                    data = o.get('data_wystawienia', '')[:10]
                    st.caption(f"👤 **{autor}** |  📅 {data}")


# --- GŁÓWNE WIDOKI ---

def show_client_catalog(api, user):
    st.title("🛠️ Oferta narzędzi")

    all_data = get_cached_catalog(api)
    if not all_data:
        st.info("Katalog jest obecnie pusty.")
        return

    raw_models = [m['ModelNarzedzia'] for m in all_data]
    cats = ["Wszystkie"] + sorted(list(set(m['kategoria'] for m in raw_models)))
    prods = ["Wszyscy"] + sorted(list(set(m['producent'] for m in raw_models)))

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        search = c1.text_input("🔍 Szukaj narzędzia...")
        f_cat = c2.selectbox("Kategoria", cats)
        f_prod = c3.selectbox("Producent", prods)
        f_price = c4.number_input("Max cena/doba", value=2000)

    filtered_models = [
        m for m in all_data
        if (search.lower() in m['ModelNarzedzia']['nazwa_modelu'].lower()) and
           (f_cat == "Wszystkie" or m['ModelNarzedzia']['kategoria'] == f_cat) and
           (f_prod == "Wszyscy" or m['ModelNarzedzia']['producent'] == f_prod) and
           (m['ModelNarzedzia']['cena_za_dobe'] <= f_price)
    ]

    if not filtered_models:
        st.warning("Nie znaleziono narzędzi spełniających kryteria.")
    else:
        st.divider()
        for m in filtered_models:
            model = m['ModelNarzedzia']
            q = m.get('liczba_sztuk', 0)

            with st.container(border=False):
                col_main, col_price, col_deposit = st.columns([2.5, 1, 1])

                with col_main:
                    st.markdown(f"### {model['nazwa_modelu']}")
                    st.caption(f"📂 {model['kategoria']} | 🏭 {model['producent']}")

                with col_price:
                    st.markdown(f"### {model['cena_za_dobe']} zł")
                    st.caption("💰 cena / doba")

                with col_deposit:
                    st.markdown(f"### {model['kaucja']} zł")
                    st.caption("🛡️ kaucja / szt.")

                c_opt, c_stat, c_res = st.columns([1, 1, 2])

                with c_opt:
                    if st.button(f"💬 Opinie", key=f"ops_{model['id']}", type="secondary", use_container_width=True):
                        show_opinions_dialog(api, model)

                with c_stat:
                    if q > 0:
                        st.markdown(
                            f"<div style='text-align: center; padding-top: 5px; font-weight: bold; color: green;'>✅ "
                            f"Dostępne: {q} szt.</div>",
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f"<div style='text-align: center; padding-top: 5px; font-weight: bold; color: gray;'>❌ "
                            f"Chwilowy brak</div>",
                            unsafe_allow_html=True)

                with c_res:
                    if not user:
                        st.button("🔐 Zaloguj się", key=f"login_{model['id']}",
                                  disabled=True, use_container_width=True)
                    elif q <= 0:

                        st.button("🚫 Niedostępne", key=f"empty_{model['id']}",
                                  disabled=True, use_container_width=True)
                    else:
                        if st.button("🛒 Zarezerwuj teraz", key=f"res_{model['id']}",
                                     type="primary", use_container_width=True):
                            reserve_tool_dialog(api, model, user)

                st.divider()


def show_rentals_history(api, user):
    st.title("📜 Twoja Historia Wypożyczeń")
    rentals = get_cached_history(api, user['id'])

    if not rentals:
        st.info("Nie masz jeszcze żadnych wypożyczeń.")
        return

    def f_dt(dt_str):
        return dt_str[:10] if dt_str else "---"

    for r in rentals:
        pozycje = r.get('pozycje', [])
        if not pozycje:
            continue

        first_item = pozycje[0].get('egzemplarz', {})
        m_id = first_item.get('model_id')
        m_name = first_item.get('model', {}).get('nazwa_modelu', "Narzędzie")

        all_names = [p['egzemplarz']['model']['nazwa_modelu'] for p in pozycje if 'egzemplarz' in p]
        counts = Counter(all_names)
        tools_str = ", ".join([f"{name} (x{qty})" for name, qty in counts.items()])

        with st.expander(f"📦 Wypożyczenie #{r['id']} - {tools_str}"):
            s_color = "green" if r['status'] == "ZAKOŃCZONA" else "blue"
            st.markdown(f"Status: :{s_color}[**{r['status']}**]")

            st.markdown("### 💰 Rozliczenie finansowe")
            c1, c2, c3 = st.columns(3)

            koszt_najmu = r.get('koszt_najmu', 0)
            suma_kaucji = r.get('suma_kaucji', 0)
            razem = koszt_najmu + suma_kaucji

            c1.metric("Koszt najmu", f"{koszt_najmu:.2f} zł")
            c2.metric("Suma kaucji (depozyt)", f"{suma_kaucji:.2f} zł")
            c3.metric("Łącznie", f"{razem:.2f} zł")

            if r['status'] == "ZAKOŃCZONA":
                st.success(f"✅ Kaucja {suma_kaucji:.2f} zł została zwrócona na Twoje konto.")

            st.markdown("---")
            st.markdown("### 📅 Terminy (Plan vs Realizacja)")

            col_plan, col_fact = st.columns(2)

            with col_plan:
                st.caption("📅 TERMINY PLANOWANE")
                st.write(f"**Odbiór:** `{f_dt(r.get('data_plan_wydania'))}`")
                st.write(f"**Zwrot:** `{f_dt(r.get('data_plan_zwrotu'))}`")

            with col_fact:
                st.caption("✅ REALIZACJA FAKTYCZNA")
                f_wydania = f_dt(r.get('data_faktyczna_wydania'))
                f_zwrotu = f_dt(r.get('data_faktyczna_zwrotu'))

                st.write(f"**Odebrano:** `{f_wydania}`")
                st.write(f"**Oddano:** `{f_zwrotu}`")

            st.markdown("---")

            if r['status'] == "ZAKOŃCZONA":
                check = api.get(f"/inventory/models/{m_id}/opinions/exists",
                                params={"client_id": user['id']})

                if check and not check.json().get("exists"):
                    if st.button("✍️ Wystaw opinię", key=f"op_{r['id']}", use_container_width=True):
                        add_opinion_dialog(api, user['id'], m_id, m_name)
                else:
                    st.caption("✅ Oceniłeś już to narzędzie. Dzięki!")


def show_report_fault_view(api, user):
    st.title("⚠️ Zgłoś awarię sprzętu")
    st.write("Wybierz narzędzie, które uległo awarii w trakcie użytkowania.")

    items = get_cached_issued_items(api, user['id'])

    if not items:
        st.info("Obecnie nie posiadasz żadnych wydanych narzędzi.")
        return

    active_items = [i for i in items if i.get('stan') not in ["AWARIA", "WYMAGA_PRZEGLADU"]]

    if not active_items:
        st.success("Wszystkie Twoje narzędzia są sprawne lub usterki zostały już zgłoszone! ✅")
        return

    for item in active_items:
        m_name = item.get('model_name', 'Nieznany model')
        sn = item.get('sn', '---')
        d_zwrotu = item.get('data_plan_zwrotu', '---')
        w_id = item.get('wypozyczenie_id', '?')

        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1.5])

            with c1:
                st.markdown(f"### {m_name}")
                st.caption(f"Numer seryjny: `{sn}`")

            with c2:
                clean_date = d_zwrotu[:10] if d_zwrotu else "brak daty"
                st.write(f"📅 Planowany zwrot: **{clean_date}**")
                st.caption(f"ID Wypożyczenia: `#{w_id}`")

            with c3:
                # Przycisk wywołuje dialog, który już przywróciliśmy
                if st.button("🚨 Zgłoś awarię", key=f"btn_f_{item['id']}",
                             type="primary", use_container_width=True):
                    report_fault_dialog(api, item)
