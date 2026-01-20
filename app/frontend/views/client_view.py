import streamlit as st
from datetime import datetime, timedelta, time
from app.backend import crud, models
from collections import Counter

@st.dialog("Rezerwacja narzędzia")
def reserve_tool_dialog(db, model, user):
    st.subheader(f"🛒 {model.nazwa_modelu}")

    c1, c2 = st.columns(2)
    # Użytkownik wybiera daty, które trafią do pól 'plan_wydania' i 'plan_zwrotu'
    d_start = c1.date_input("Planowana data odbioru", min_value=datetime.now().date())
    d_end = c2.date_input("Planowana data zwrotu", min_value=d_start + timedelta(days=1))

    dt_start = datetime.combine(d_start, time.min)
    dt_end = datetime.combine(d_end, time.max)

    term_available = crud.get_available_items_for_term(db, model.id, dt_start, dt_end)
    count = len(term_available)

    if count > 0:
        st.success(f"Dostępność w wybranym terminie: **{count} szt.**")
        quantity = st.number_input("Ile sztuk chcesz zarezerwować?", min_value=1, max_value=count, value=1)

        days = (d_end - d_start).days
        total = days * model.cena_za_dobe * quantity
        st.info(f"💰 Przewidywany koszt: **{total} PLN** (+ kaucja: {model.kaucja * quantity} PLN)")

        if st.form_submit_button("Potwierdzam rezerwację") if False else st.button("Potwierdzam rezerwację",
                                                                                   type="primary",
                                                                                   use_container_width=True):
            try:
                # W systemie docelowym user.id powinien być powiązany z ID Klienta
                crud.create_reservation(db, user.id, model.id, int(quantity), dt_start, dt_end)
                st.success("Rezerwacja zapisana! Czeka na odbiór w magazynie.")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Błąd rezerwacji: {e}")
    else:
        st.error("Brak wolnych egzemplarzy w tym terminie. Spróbuj zmienić daty.")


@st.dialog("Opinie użytkowników")
def show_opinions_dialog(db, model):
    st.subheader(f"⭐ Recenzje dla: {model.nazwa_modelu}")

    opinie = crud.get_model_opinions(db, model.id)

    if not opinie:
        st.info("Ten model nie posiada jeszcze żadnych opinii. Bądź pierwszy!")
        return

    # Wyświetlamy średnią (opcjonalnie)
    avg_rating = sum(o.ocena for o in opinie) / len(opinie)
    st.markdown(f"**Średnia ocena: {avg_rating:.1f}/5** ({len(opinie)} opinii)")
    st.divider()

    # Przewijalna lista opinii
    for o in opinie:
        with st.container():
            # Gwiazdki i data
            stars = "⭐" * int(o.ocena)
            date_str = o.data_wystawienia.strftime("%d.%m.%Y") if hasattr(o, 'data_wystawienia') else ""

            st.markdown(f"### {stars}")
            st.write(o.komentarz)

            # Podpis autora (korzystając z relacji do klienta)
            klient_name = f"{o.klient.imie} {o.klient.nazwisko[0]}."  # Skracamy nazwisko dla prywatności
            st.caption(f"✍️ {klient_name} | 📅 {date_str}")
            st.divider()

def show_client_catalog(db, user):
    st.title("🛠️ Oferta dostępnych narzędzi")

    # --- FILTROWANIE ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        search = c1.text_input("🔍 Szukaj narzędzia (nazwa)...").lower()

        models_raw = db.query(models.ModelNarzedzia).filter(models.ModelNarzedzia.wycofany == False).all()

        cats = ["Wszystkie"] + sorted(list(set(m.kategoria for m in models_raw)))
        prods = ["Wszyscy"] + sorted(list(set(m.producent for m in models_raw)))

        f_cat = c2.selectbox("Kategoria", cats)
        f_prod = c3.selectbox("Producent", prods)
        f_price = c4.number_input("Max cena/doba", min_value=0, value=2000)

    # --- TABELA ---
    h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 1, 1, 1])
    h1.write("**NAZWA MODELU**")
    h2.write("**KATEGORIA**")
    h3.write("**PRODUCENT**")
    h4.write("**NA STANIE**")
    h5.write("**CENA/DOBA**")
    h6.write("**REZERWOWANIE**")
    st.divider()

    for m in models_raw:
        # Filtrowanie lokalne
        if search not in m.nazwa_modelu.lower(): continue
        if f_cat != "Wszystkie" and m.kategoria != f_cat: continue
        if f_prod != "Wszyscy" and m.producent != f_prod: continue
        if m.cena_za_dobe > f_price: continue

        # Szybki licznik fizyczny (W_MAGAZYNIE + SPRAWNY)
        physical_count = crud.count_physical_in_stock(db, m.id)
        opinions_count = len(crud.get_model_opinions(db, m.id))

        c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 1, 1, 1])
        with c1:
            st.write(f"**{m.nazwa_modelu}**")
            # Przycisk "Opinie" - mniejszy, żeby nie przytłaczał
            label_op = f"💬 Opinie ({opinions_count})"
            if st.button(label_op, key=f"ops_{m.id}", type="tertiary"):
                show_opinions_dialog(db, m)
        c2.write(m.kategoria)
        c3.write(m.producent)

        # Kolorowanie dostępności fizycznej
        q_color = "green" if physical_count > 0 else "gray"
        c4.markdown(f":{q_color}[**{physical_count} szt.**]")

        c5.write(f"{m.cena_za_dobe} PLN")

        with c6:
            # --- LOGIKA DLA ZALOGOWANEGO KLIENTA ---
            if user is not None:
                if physical_count > 0:
                    if st.button("Rezerwuj", key=f"res_{m.id}", type="primary", use_container_width=True):
                        reserve_tool_dialog(db, m, user)
                else:
                    st.button("Brak sztuk", key=f"none_{m.id}", disabled=True, use_container_width=True)

            # --- LOGIKA DLA GOŚCIA ---
            else:
                # Wyświetlamy nieaktywny przycisk z podpowiedzią
                st.button("Rezerwuj", key=f"guest_{m.id}", disabled=True, use_container_width=True,
                          help="Musisz być zalogowany, aby zarezerwować narzędzie.")


def show_rentals_history(db, user):
    st.title("📜 Twoja Historia Wypożyczeń")

    # Reanimacja sesji obiektu
    user_db = db.merge(user)
    rentals = crud.get_customer_rentals(db, user_db.id)

    # Filtrowanie (Search, Data, Status)
    with st.expander("🔍 Filtrowanie i wyszukiwanie"):
        c1, c2, c3 = st.columns([2, 2, 2])
        search = c1.text_input("Szukaj narzędzia")
        # Zakres dat bazuje na dacie planowanego wydania
        date_range = c2.date_input("Zakres dat", [])
        status_filter = c3.multiselect("Status", ["Zakończona", "Aktywna", "Anulowana"],
                                       default=["Zakończona", "Aktywna", "Anulowana"])

    # Nagłówki tabeli zgodne z Twoim wymaganiem
    st.divider()
    cols = st.columns([0.8, 2.5, 1.5, 1.5, 1.2, 1.2, 1.3])
    headers = ["ID_REZ", "NAZWA NARZEDZIA", "DATA_OD", "DATA_DO", "STATUS", "KWOTA", "AKCJA"]
    for col, h in zip(cols, headers):
        col.write(f"**{h}**")
    st.divider()

    for r in rentals:
        # --- NOWA LOGIKA GRUPOWANIA ---
        # 1. Pobieramy wszystkie nazwy modeli z pozycji
        all_names = [p.egzemplarz.model.nazwa_modelu for p in r.pozycje]

        # 2. Liczymy wystąpienia każdego modelu
        counts = Counter(all_names)

        # 3. Formatuje tekst: "Model A (x3), Model B (x1)"
        tools_formatted = [f"{name} (x{qty})" for name, qty in counts.items()]
        tools_str = ", ".join(tools_formatted)
        # ------------------------------

        # Mapowanie statusów
        status_map = {
            "REZERWACJA": ("Aktywna", "blue"),
            "WYDANE": ("Aktywna", "orange"),
            "ZAKOŃCZONA": ("Zakończona", "green"),
            "ANULOWANA": ("Anulowana", "red")
        }
        display_status, color = status_map.get(r.status, ("Nieznany", "gray"))


        # Filtrowanie "w locie"
        if search.lower() not in tools_str.lower(): continue
        if display_status not in status_filter: continue

        row = st.columns([0.8, 2.5, 1.5, 1.5, 1.2, 1.2, 1.3])

        row[0].write(f"#{r.id}")
        row[1].write(tools_str)  # Tutaj wyświetlamy pogrupowane dane
        row[2].write(r.data_plan_wydania.strftime("%Y-%m-%d") if r.data_plan_wydania else "-")
        row[3].write(r.data_plan_zwrotu.strftime("%Y-%m-%d") if r.data_plan_zwrotu else "-")
        row[4].markdown(f":{color}[{display_status}]")
        row[5].write(f"{r.koszt_calkowity:.2f} zł")

        # LOGIKA PRZYCISKU OPINII
        if display_status == "Zakończona":
            # Pobieramy ID modelu z pierwszej pozycji wypożyczenia
            model_id = r.pozycje[0].egzemplarz.model_id

            # Sprawdzamy czy para Klient-Model już istnieje w Opiniach
            already_voted = crud.check_if_opinion_exists(db, user_db.id, model_id)

            if already_voted:
                row[6].button("OCENIONO", key=f"voted_{r.id}", disabled=True, use_container_width=True)
            else:
                if row[6].button("WYSTAW", key=f"btn_{r.id}", type="primary", use_container_width=True):
                    show_opinion_dialog(db, r, r.pozycje[0].egzemplarz.model)


# Funkcja okienka (Dialogu) - wywoływana przy kliknięciu "WYSTAW"
@st.dialog("Wystaw opinię")
def show_opinion_dialog(db, rental, tool_model):
    st.subheader(f"Ocena narzędzia: {tool_model.nazwa_modelu}")

    # Gwiazdki (0-4 w systemie, więc dodajemy +1)
    st.write("Wybierz ocenę:")
    stars = st.feedback("stars")

    komentarz = st.text_area("Twoje uwagi (opcjonalnie)", placeholder="Napisz kilka słów o sprzęcie...")

    col1, col2 = st.columns(2)
    if col1.button("WYSTAW", type="primary", use_container_width=True):
        if stars is not None:
            # Zapisujemy opinię dla konkretnego modelu
            crud.create_opinion(db, rental.klient_id, tool_model.id, stars + 1, komentarz)
            st.success("Dziękujemy! Opinia została zapisana.")
            st.rerun()
        else:
            st.error("Proszę zaznaczyć gwiazdki!")

    if col2.button("ANULUJ", use_container_width=True):
        st.rerun()


@st.dialog("Opisz usterkę")
def show_fault_report_dialog(db, pozycja):
    st.warning(f"Zgłaszasz usterkę dla: **{pozycja.egzemplarz.model.nazwa_modelu}**")
    st.write(f"Numer seryjny: `{pozycja.egzemplarz.numer_seryjny}`")

    opis = st.text_area("Co się stało?", placeholder="Opisz dokładnie problem z narzędziem...", height=150)

    st.info("⚠️ Zgłoszenie usterki spowoduje zmianę statusu narzędzia na AWARIA.")

    col1, col2 = st.columns(2)
    if col1.button("WYŚLIJ ZGŁOSZENIE", type="primary", use_container_width=True):
        if len(opis.strip()) < 5:
            st.error("Proszę podać dokładniejszy opis usterki.")
        else:
            crud.report_tool_fault(db, pozycja.id, opis)
            st.success("Usterka została zgłoszona. Serwisant został powiadomiony.")
            st.rerun()

    if col2.button("ANULUJ", use_container_width=True):
        st.rerun()


# app/frontend/views/client_view.py

def show_report_fault_view(db, user):
    st.title("⚠️ Zgłoś usterkę narzędzia")
    st.write("Wybierz narzędzie, które aktualnie posiadasz, a uległo awarii.")

    # Reanimacja sesji
    user_db = db.merge(user)

    # Pobieramy TYLKO WYDANE narzędzia
    issued_items = crud.get_issued_rental_items(db, user_db.id)

    if not issued_items:
        st.info("Nie posiadasz obecnie żadnych wydanych narzędzi, dla których można zgłosić usterkę.")
        st.caption("Usterkę można zgłosić dopiero po fizycznym odebraniu narzędzia z magazynu.")
        return

    # Nagłówki tabeli
    st.divider()
    cols = st.columns([1, 2.5, 2, 2, 1.5])
    headers = ["ID REZ", "NAZWA NARZĘDZIA", "NUMER SERYJNY", "TERMIN ZWROTU", "AKCJA"]
    for col, h in zip(cols, headers):
        col.write(f"**{h}**")
    st.divider()

    for item in issued_items:
        rez = item.wypozyczenie
        egz = item.egzemplarz

        row = st.columns([1, 2.5, 2, 2, 1.5])

        row[0].write(f"#{rez.id}")
        row[1].write(egz.model.nazwa_modelu)
        # Wyświetlamy numer seryjny, aby klient wiedział dokładnie którą sztukę zgłasza
        row[2].write(f"`{egz.numer_seryjny}`")

        # Termin planowanego zwrotu
        termin = rez.data_plan_zwrotu.strftime("%Y-%m-%d") if rez.data_plan_zwrotu else "-"
        row[3].write(termin)

        # Przycisk zgłoszenia - teraz mamy pewność, że klient posiada to narzędzie
        if row[4].button("Zgłoś usterkę", key=f"fault_{item.id}", type="primary", use_container_width=True):
            show_fault_report_dialog(db, item)