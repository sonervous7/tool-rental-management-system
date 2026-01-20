import streamlit as st
from datetime import datetime, timedelta, time
from app.backend import crud, models


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

        c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 1, 1, 1])
        c1.write(f"**{m.nazwa_modelu}**")
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