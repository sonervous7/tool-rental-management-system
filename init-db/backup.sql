--
-- PostgreSQL database dump
--

\restrict FYcaRADnxMRLoe1bgGQidSEbV1JSfzAQxeotAQundPTONDjMhTJN8KvGENbATcW

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg13+1)
-- Dumped by pg_dump version 15.15 (Debian 15.15-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: czynnosci_serwisowe; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.czynnosci_serwisowe (
    id integer NOT NULL,
    egzemplarz_id integer NOT NULL,
    serwisant_id integer NOT NULL,
    rodzaj character varying(50) NOT NULL,
    data_rozpoczecia timestamp without time zone NOT NULL,
    data_zakonczenia timestamp without time zone,
    notatka_opis text
);


ALTER TABLE public.czynnosci_serwisowe OWNER TO "user";

--
-- Name: czynnosci_serwisowe_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.czynnosci_serwisowe_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.czynnosci_serwisowe_id_seq OWNER TO "user";

--
-- Name: czynnosci_serwisowe_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.czynnosci_serwisowe_id_seq OWNED BY public.czynnosci_serwisowe.id;


--
-- Name: egzemplarze_narzedzi; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.egzemplarze_narzedzi (
    id integer NOT NULL,
    model_id integer NOT NULL,
    numer_seryjny character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    stan_techniczny character varying(50) NOT NULL,
    data_zakupu timestamp without time zone,
    licznik_wypozyczen integer NOT NULL,
    magazyn_id integer,
    warsztat_id integer,
    CONSTRAINT ck_egzemplarz_magazyn_xor_warsztat CHECK ((NOT ((magazyn_id IS NOT NULL) AND (warsztat_id IS NOT NULL))))
);


ALTER TABLE public.egzemplarze_narzedzi OWNER TO "user";

--
-- Name: egzemplarze_narzedzi_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.egzemplarze_narzedzi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.egzemplarze_narzedzi_id_seq OWNER TO "user";

--
-- Name: egzemplarze_narzedzi_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.egzemplarze_narzedzi_id_seq OWNED BY public.egzemplarze_narzedzi.id;


--
-- Name: kierownicy; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.kierownicy (
    pracownik_id integer NOT NULL,
    data_zatrudnienia timestamp without time zone NOT NULL,
    data_zwolnienia timestamp without time zone
);


ALTER TABLE public.kierownicy OWNER TO "user";

--
-- Name: klienci; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.klienci (
    id integer NOT NULL,
    imie character varying(50) NOT NULL,
    nazwisko character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    telefon character varying(15),
    haslo character varying(255) NOT NULL,
    pytanie_pomocnicze character varying(255),
    odp_na_pytanie_pom character varying(255),
    data_utworzenia timestamp without time zone NOT NULL
);


ALTER TABLE public.klienci OWNER TO "user";

--
-- Name: klienci_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.klienci_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.klienci_id_seq OWNER TO "user";

--
-- Name: klienci_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.klienci_id_seq OWNED BY public.klienci.id;


--
-- Name: magazynierzy; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.magazynierzy (
    pracownik_id integer NOT NULL,
    data_zatrudnienia timestamp without time zone NOT NULL,
    data_zwolnienia timestamp without time zone
);


ALTER TABLE public.magazynierzy OWNER TO "user";

--
-- Name: magazyny; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.magazyny (
    id integer NOT NULL,
    nazwa character varying(100) NOT NULL,
    adres character varying(255),
    pojemnosc integer
);


ALTER TABLE public.magazyny OWNER TO "user";

--
-- Name: magazyny_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.magazyny_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.magazyny_id_seq OWNER TO "user";

--
-- Name: magazyny_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.magazyny_id_seq OWNED BY public.magazyny.id;


--
-- Name: modele_narzedzi; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.modele_narzedzi (
    id integer NOT NULL,
    nazwa_modelu character varying(100) NOT NULL,
    producent character varying(50),
    kategoria character varying(50),
    opis text,
    cena_za_dobe numeric(10,2) NOT NULL,
    kaucja numeric(10,2),
    wycofany boolean NOT NULL,
    data_utworzenia timestamp without time zone NOT NULL
);


ALTER TABLE public.modele_narzedzi OWNER TO "user";

--
-- Name: modele_narzedzi_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.modele_narzedzi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.modele_narzedzi_id_seq OWNER TO "user";

--
-- Name: modele_narzedzi_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.modele_narzedzi_id_seq OWNED BY public.modele_narzedzi.id;


--
-- Name: opinie; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.opinie (
    id integer NOT NULL,
    model_id integer NOT NULL,
    klient_id integer NOT NULL,
    ocena integer NOT NULL,
    komentarz text,
    data_wystawienia timestamp without time zone NOT NULL
);


ALTER TABLE public.opinie OWNER TO "user";

--
-- Name: opinie_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.opinie_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.opinie_id_seq OWNER TO "user";

--
-- Name: opinie_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.opinie_id_seq OWNED BY public.opinie.id;


--
-- Name: pozycje_wypozyczenia; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.pozycje_wypozyczenia (
    id integer NOT NULL,
    wypozyczenie_id integer NOT NULL,
    egzemplarz_id integer NOT NULL,
    czy_zgloszono_usterke boolean NOT NULL,
    opis_usterki text
);


ALTER TABLE public.pozycje_wypozyczenia OWNER TO "user";

--
-- Name: pozycje_wypozyczenia_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.pozycje_wypozyczenia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pozycje_wypozyczenia_id_seq OWNER TO "user";

--
-- Name: pozycje_wypozyczenia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.pozycje_wypozyczenia_id_seq OWNED BY public.pozycje_wypozyczenia.id;


--
-- Name: pracownicy; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.pracownicy (
    id integer NOT NULL,
    imie character varying(50) NOT NULL,
    nazwisko character varying(50) NOT NULL,
    pesel character varying(11) NOT NULL,
    adres character varying(255),
    telefon character varying(15),
    email character varying(100),
    login character varying(30) NOT NULL,
    haslo character varying(255) NOT NULL,
    data_utworzenia timestamp without time zone NOT NULL
);


ALTER TABLE public.pracownicy OWNER TO "user";

--
-- Name: pracownicy_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.pracownicy_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pracownicy_id_seq OWNER TO "user";

--
-- Name: pracownicy_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.pracownicy_id_seq OWNED BY public.pracownicy.id;


--
-- Name: serwisanci; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.serwisanci (
    pracownik_id integer NOT NULL,
    data_zatrudnienia timestamp without time zone NOT NULL,
    data_zwolnienia timestamp without time zone
);


ALTER TABLE public.serwisanci OWNER TO "user";

--
-- Name: warsztaty; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.warsztaty (
    id integer NOT NULL,
    nazwa character varying(100) NOT NULL,
    adres character varying(255)
);


ALTER TABLE public.warsztaty OWNER TO "user";

--
-- Name: warsztaty_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.warsztaty_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.warsztaty_id_seq OWNER TO "user";

--
-- Name: warsztaty_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.warsztaty_id_seq OWNED BY public.warsztaty.id;


--
-- Name: wypozyczenia; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.wypozyczenia (
    id integer NOT NULL,
    klient_id integer NOT NULL,
    magazynier_wydaj_id integer,
    magazynier_przyjmij_id integer,
    data_rezerwacji timestamp without time zone NOT NULL,
    data_plan_wydania timestamp without time zone,
    data_plan_zwrotu timestamp without time zone,
    data_faktyczna_wydania timestamp without time zone,
    data_faktyczna_zwrotu timestamp without time zone,
    status character varying(20) NOT NULL,
    koszt_calkowity numeric(10,2) NOT NULL
);


ALTER TABLE public.wypozyczenia OWNER TO "user";

--
-- Name: wypozyczenia_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.wypozyczenia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.wypozyczenia_id_seq OWNER TO "user";

--
-- Name: wypozyczenia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.wypozyczenia_id_seq OWNED BY public.wypozyczenia.id;


--
-- Name: czynnosci_serwisowe id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.czynnosci_serwisowe ALTER COLUMN id SET DEFAULT nextval('public.czynnosci_serwisowe_id_seq'::regclass);


--
-- Name: egzemplarze_narzedzi id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.egzemplarze_narzedzi ALTER COLUMN id SET DEFAULT nextval('public.egzemplarze_narzedzi_id_seq'::regclass);


--
-- Name: klienci id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.klienci ALTER COLUMN id SET DEFAULT nextval('public.klienci_id_seq'::regclass);


--
-- Name: magazyny id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.magazyny ALTER COLUMN id SET DEFAULT nextval('public.magazyny_id_seq'::regclass);


--
-- Name: modele_narzedzi id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.modele_narzedzi ALTER COLUMN id SET DEFAULT nextval('public.modele_narzedzi_id_seq'::regclass);


--
-- Name: opinie id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.opinie ALTER COLUMN id SET DEFAULT nextval('public.opinie_id_seq'::regclass);


--
-- Name: pozycje_wypozyczenia id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pozycje_wypozyczenia ALTER COLUMN id SET DEFAULT nextval('public.pozycje_wypozyczenia_id_seq'::regclass);


--
-- Name: pracownicy id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pracownicy ALTER COLUMN id SET DEFAULT nextval('public.pracownicy_id_seq'::regclass);


--
-- Name: warsztaty id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.warsztaty ALTER COLUMN id SET DEFAULT nextval('public.warsztaty_id_seq'::regclass);


--
-- Name: wypozyczenia id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.wypozyczenia ALTER COLUMN id SET DEFAULT nextval('public.wypozyczenia_id_seq'::regclass);


--
-- Data for Name: czynnosci_serwisowe; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.czynnosci_serwisowe (id, egzemplarz_id, serwisant_id, rodzaj, data_rozpoczecia, data_zakonczenia, notatka_opis) FROM stdin;
1	3	3	PRZEGLAD	2026-01-26 00:40:14.73113	2026-01-26 00:40:14.728131	Zrobiłem to i owo.
2	1	3	NAPRAWA	2026-01-26 01:07:13.911944	2026-01-26 01:07:13.909946	Wymieniłem wiertło
3	2	3	NAPRAWA	2026-01-26 01:07:31.154515	2026-01-26 01:07:31.153514	Naprawiłem silnik szczotkowy
4	44	3	PRZEGLAD	2026-01-26 03:50:04.771173	2026-01-26 03:50:04.769945	Sprawdziłem co się dzieje i wszystko ok, nie wiem co oni gadają w ogóle.
5	87	3	PRZEGLAD	2026-01-26 03:50:19.726889	2026-01-26 03:50:19.725977	Git
6	93	3	PRZEGLAD	2026-01-26 03:50:26.861016	2026-01-26 03:50:26.860261	Gut gut
7	67	3	PRZEGLAD	2026-01-26 03:50:37.246675	2026-01-26 03:50:37.246005	Doine
8	79	3	PRZEGLAD	2026-01-26 03:50:41.863759	2026-01-26 03:50:41.862825	Działa
9	81	3	PRZEGLAD	2026-01-26 03:50:50.037405	2026-01-26 03:50:50.03544	Działa na pewno
10	82	3	PRZEGLAD	2026-01-26 03:51:01.130191	2026-01-26 03:51:01.129541	Co tu się dzieje
11	69	3	NAPRAWA	2026-01-26 03:52:58.637584	2026-01-26 03:52:58.636785	Działa
12	73	3	NAPRAWA	2026-01-26 03:53:05.324505	2026-01-26 03:53:05.3238	Działa
13	74	3	NAPRAWA	2026-01-26 03:53:09.889627	2026-01-26 03:53:09.888936	Działa
14	76	3	NAPRAWA	2026-01-26 03:53:16.381327	2026-01-26 03:53:16.380676	Działa
15	78	3	NAPRAWA	2026-01-26 03:53:18.994871	2026-01-26 03:53:18.994121	Działa
16	80	3	NAPRAWA	2026-01-26 03:53:21.940683	2026-01-26 03:53:21.940013	Działa
17	85	3	NAPRAWA	2026-01-26 03:53:24.503393	2026-01-26 03:53:24.502692	Działa
18	86	3	NAPRAWA	2026-01-26 03:53:27.734584	2026-01-26 03:53:27.733956	Działa
19	82	3	NAPRAWA	2026-01-26 03:53:30.995218	2026-01-26 03:53:30.994137	Działa
20	108	3	NAPRAWA	2026-01-26 03:53:34.307635	2026-01-26 03:53:34.306693	Działa
21	117	3	NAPRAWA	2026-01-26 03:53:37.160079	2026-01-26 03:53:37.159267	Działa
22	123	3	PRZEGLAD	2026-01-26 03:53:42.406873	2026-01-26 03:53:42.405975	Działa
23	115	3	PRZEGLAD	2026-01-26 03:53:45.864262	2026-01-26 03:53:45.863456	Działa
24	113	3	PRZEGLAD	2026-01-26 03:54:33.156813	2026-01-26 03:54:33.156	Naprawiłem
25	101	3	PRZEGLAD	2026-01-26 03:54:46.532442	2026-01-26 03:54:46.531705	Działa
26	104	3	PRZEGLAD	2026-01-26 03:54:50.093625	2026-01-26 03:54:50.092478	Działa
27	105	3	PRZEGLAD	2026-01-26 03:54:52.235702	2026-01-26 03:54:52.234626	Działa
28	106	3	PRZEGLAD	2026-01-26 03:54:54.205312	2026-01-26 03:54:54.204668	Działa
29	107	3	PRZEGLAD	2026-01-26 03:54:56.114266	2026-01-26 03:54:56.113561	Działa
\.


--
-- Data for Name: egzemplarze_narzedzi; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.egzemplarze_narzedzi (id, model_id, numer_seryjny, status, stan_techniczny, data_zakupu, licznik_wypozyczen, magazyn_id, warsztat_id) FROM stdin;
2	1	SN-D9B276	W_WARSZTACIE	SPRAWNY	\N	0	\N	1
3	1	SN-71BB3E	W_MAGAZYNIE	SPRAWNY	\N	1	1	\N
4	1	SN-8B04BA	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
5	1	SN-DEDD5E	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
6	1	SN-EEE0E2	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
7	1	SN-13B145	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
8	1	SN-99E47A	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
9	1	SN-5CC2DF	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
10	1	SN-6ED313	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
11	1	SN-48F1C7	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
12	1	SN-AA19C6	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
13	1	SN-5F84D8	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
14	1	SN-55D979	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
15	1	SN-2A2916	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
16	1	SN-98A7C8	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
17	1	SN-B1352A	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
18	1	SN-64348D	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
19	1	SN-065BAC	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
20	1	SN-5F4473	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
21	1	SN-2C5CFC	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
22	1	SN-402227	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
23	1	SN-C88418	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
24	1	SN-DC0B3B	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
25	1	SN-524CC4	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
27	1	SN-9744BE	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
28	1	SN-58D29C	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
29	1	SN-4430EC	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
30	1	SN-6C7AEF	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
31	1	SN-191FBA	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
32	1	SN-B4207F	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
33	1	SN-450FA7	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
34	1	SN-C63F76	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
35	1	SN-58A359	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
36	1	SN-71CAB2	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
37	1	SN-BD3402	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
38	1	SN-69D959	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
39	1	SN-36FE0E	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
40	1	SN-6B81CC	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
41	1	SN-5EC8FE	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
42	1	SN-042932	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
43	1	SN-7B3BFB	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
45	1	SN-8074E5	W_WARSZTACIE	AWARIA	\N	0	\N	1
46	1	SN-2FB1E4	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
47	1	SN-3F74F3	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
48	1	SN-CF33C0	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
49	1	SN-1A5495	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
50	1	SN-D0EAA4	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
51	2	SN-06821B	W_WARSZTACIE	AWARIA	\N	1	\N	1
52	2	SN-76B20F	W_WARSZTACIE	AWARIA	\N	1	\N	1
53	2	SN-E0CFD7	W_MAGAZYNIE	SPRAWNY	\N	1	\N	\N
54	2	SN-8D8AA5	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
55	2	SN-084CE6	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
56	2	SN-D8FD90	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
57	2	SN-D17FA3	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
58	2	SN-44E52E	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
59	2	SN-3408BE	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
60	2	SN-48AA5D	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
61	2	SN-B5BF07	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
62	2	SN-1787C9	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
63	2	SN-AEC8E0	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
64	2	SN-7E0B8B	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
65	2	SN-E8B242	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
66	4	BE-4-3863	W_MAGAZYNIE	SPRAWNY	2025-02-20 03:04:34.27498	25	1	\N
68	4	BE-4-1572	W_MAGAZYNIE	SPRAWNY	2025-08-26 03:04:34.275981	28	1	\N
70	4	BE-4-4248	W_MAGAZYNIE	SPRAWNY	2025-06-18 03:04:34.275981	23	1	\N
71	4	BE-4-2950	W_MAGAZYNIE	SPRAWNY	2025-12-26 03:04:34.276982	13	1	\N
72	5	AL-5-5328	W_MAGAZYNIE	SPRAWNY	2025-09-14 03:04:34.279983	5	1	\N
75	5	AL-5-3000	W_MAGAZYNIE	SPRAWNY	2025-11-13 03:04:34.280982	21	1	\N
77	6	BO-6-7198	W_MAGAZYNIE	SPRAWNY	2025-10-23 03:04:34.283984	3	1	\N
83	7	TO-7-3707	W_MAGAZYNIE	SPRAWNY	2025-06-04 03:04:34.286981	13	1	\N
84	7	TO-7-8806	W_MAGAZYNIE	SPRAWNY	2025-08-12 03:04:34.28798	17	1	\N
88	7	TO-7-7096	W_MAGAZYNIE	SPRAWNY	2025-02-16 03:04:34.28898	12	1	\N
89	8	FL-8-6594	W_MAGAZYNIE	SPRAWNY	2025-11-18 03:04:34.290979	8	1	\N
90	8	FL-8-3858	W_MAGAZYNIE	SPRAWNY	2025-11-20 03:04:34.290979	49	1	\N
91	8	FL-8-3081	W_MAGAZYNIE	SPRAWNY	2025-12-24 03:04:34.290979	45	1	\N
92	8	FL-8-2729	W_MAGAZYNIE	SPRAWNY	2025-11-05 03:04:34.290979	25	1	\N
26	1	SN-A0B155	W_MAGAZYNIE	AWARIA	\N	0	\N	\N
44	1	SN-C9D907	W_WARSZTACIE	SPRAWNY	\N	0	\N	1
87	7	TO-7-9147	W_WARSZTACIE	SPRAWNY	2025-02-02 03:04:34.28898	0	\N	2
93	9	ST-9-8091	W_WARSZTACIE	SPRAWNY	2025-08-08 03:04:34.29298	0	\N	2
67	4	BE-4-7165	W_WARSZTACIE	SPRAWNY	2025-06-08 03:04:34.27498	0	\N	2
79	6	BO-6-6083	W_WARSZTACIE	SPRAWNY	2025-06-25 03:04:34.28498	0	\N	2
81	6	BO-6-9649	W_WARSZTACIE	SPRAWNY	2025-10-10 03:04:34.28498	0	\N	2
69	4	BE-4-8247	W_WARSZTACIE	SPRAWNY	2025-12-20 03:04:34.275981	0	\N	2
73	5	AL-5-5059	W_WARSZTACIE	SPRAWNY	2025-08-13 03:04:34.279983	0	\N	2
74	5	AL-5-6157	W_WARSZTACIE	SPRAWNY	2025-10-26 03:04:34.280982	0	\N	2
76	6	BO-6-3178	W_WARSZTACIE	SPRAWNY	2025-07-09 03:04:34.283984	0	\N	2
78	6	BO-6-9797	W_WARSZTACIE	SPRAWNY	2025-11-07 03:04:34.283984	0	\N	2
80	6	BO-6-7490	W_WARSZTACIE	SPRAWNY	2025-03-16 03:04:34.28498	0	\N	2
85	7	TO-7-7740	W_WARSZTACIE	SPRAWNY	2025-05-19 03:04:34.28798	0	\N	2
86	7	TO-7-9184	W_WARSZTACIE	SPRAWNY	2025-05-07 03:04:34.28798	0	\N	2
82	7	TO-7-9392	W_WARSZTACIE	SPRAWNY	2025-07-21 03:04:34.286981	0	\N	2
98	9	ST-9-1705	W_MAGAZYNIE	SPRAWNY	2025-08-05 03:04:34.29398	30	1	\N
99	10	HO-10-1541	W_MAGAZYNIE	SPRAWNY	2025-12-20 03:04:34.295978	28	1	\N
100	10	HO-10-1586	W_MAGAZYNIE	SPRAWNY	2025-05-27 03:04:34.295978	10	1	\N
102	10	HO-10-8731	W_MAGAZYNIE	SPRAWNY	2025-05-08 03:04:34.296979	2	1	\N
103	10	HO-10-7476	W_MAGAZYNIE	SPRAWNY	2025-02-01 03:04:34.296979	25	1	\N
109	11	ST-11-3726	W_MAGAZYNIE	SPRAWNY	2025-08-09 03:04:34.29998	5	1	\N
110	11	ST-11-3504	W_MAGAZYNIE	SPRAWNY	2025-11-06 03:04:34.29998	10	1	\N
111	11	ST-11-4039	W_MAGAZYNIE	SPRAWNY	2025-10-29 03:04:34.300978	16	1	\N
112	12	CE-12-3990	W_MAGAZYNIE	SPRAWNY	2025-06-15 03:04:34.301978	39	1	\N
114	12	CE-12-2141	W_MAGAZYNIE	SPRAWNY	2025-03-12 03:04:34.301978	29	1	\N
116	12	CE-12-8638	W_MAGAZYNIE	SPRAWNY	2025-02-07 03:04:34.302978	38	1	\N
118	12	CE-12-4972	W_MAGAZYNIE	SPRAWNY	2025-08-02 03:04:34.303978	18	1	\N
119	13	HU-13-9597	W_MAGAZYNIE	SPRAWNY	2025-02-14 03:04:34.30498	23	1	\N
120	13	HU-13-3540	W_MAGAZYNIE	SPRAWNY	2025-03-08 03:04:34.30498	9	1	\N
121	13	HU-13-1671	W_MAGAZYNIE	SPRAWNY	2025-08-04 03:04:34.30598	14	1	\N
122	13	HU-13-6181	W_MAGAZYNIE	SPRAWNY	2025-08-07 03:04:34.30598	14	1	\N
1	1	SN-D11CC3	W_MAGAZYNIE	SPRAWNY	\N	0	1	\N
108	11	ST-11-6112	W_WARSZTACIE	SPRAWNY	2025-03-15 03:04:34.29998	0	\N	2
117	12	CE-12-3925	W_WARSZTACIE	SPRAWNY	2025-04-08 03:04:34.302978	0	\N	2
123	13	HU-13-2935	W_WARSZTACIE	SPRAWNY	2025-12-12 03:04:34.30598	0	\N	2
115	12	CE-12-6215	W_WARSZTACIE	SPRAWNY	2025-11-19 03:04:34.302978	0	\N	2
113	12	CE-12-4716	W_WARSZTACIE	SPRAWNY	2025-03-04 03:04:34.301978	0	\N	2
101	10	HO-10-7306	W_WARSZTACIE	SPRAWNY	2025-05-26 03:04:34.295978	0	\N	2
104	10	HO-10-2423	W_WARSZTACIE	SPRAWNY	2025-08-15 03:04:34.296979	0	\N	2
105	10	HO-10-8426	W_WARSZTACIE	SPRAWNY	2025-03-10 03:04:34.296979	0	\N	2
106	11	ST-11-2390	W_WARSZTACIE	SPRAWNY	2025-10-03 03:04:34.298981	0	\N	2
107	11	ST-11-9785	W_WARSZTACIE	SPRAWNY	2025-02-28 03:04:34.298981	0	\N	2
96	9	ST-9-2909	W_MAGAZYNIE	AWARIA	2025-10-03 03:04:34.29398	12	1	\N
97	9	ST-9-1914	W_MAGAZYNIE	AWARIA	2025-07-24 03:04:34.29398	3	1	\N
124	10	SN-4FB287	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
125	10	SN-1C257C	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
126	10	SN-DBE974	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
127	10	SN-FAD62E	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
128	10	SN-C980A8	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
129	10	SN-B868EF	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
130	10	SN-059A8B	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
131	10	SN-3B7CD9	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
132	10	SN-0CE9DA	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
133	10	SN-2210C2	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
134	11	SN-FE4244	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
135	11	SN-C5530A	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
136	11	SN-2229A0	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
137	11	SN-27F6B8	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
138	11	SN-4F3DBF	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
139	11	SN-6AB290	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
140	11	SN-28E183	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
141	11	SN-87E505	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
142	11	SN-BBF942	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
143	11	SN-A5B81A	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
144	11	SN-0B3FDD	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
145	11	SN-730C25	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
146	11	SN-9EDC91	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
147	11	SN-239138	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
148	11	SN-22A678	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
149	11	SN-2B5B95	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
150	11	SN-706308	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
151	11	SN-AEDCF8	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
152	11	SN-FD50EA	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
153	11	SN-4B8A5F	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
154	11	SN-FE5B79	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
155	11	SN-E57698	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
156	11	SN-46FC67	W_MAGAZYNIE	SPRAWNY	\N	0	\N	\N
94	9	ST-9-6785	W_MAGAZYNIE	WYMAGA_PRZEGLADU	2025-08-05 03:04:34.29298	46	1	\N
95	9	ST-9-5224	W_MAGAZYNIE	WYMAGA_PRZEGLADU	2025-02-25 03:04:34.29298	29	1	\N
\.


--
-- Data for Name: kierownicy; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.kierownicy (pracownik_id, data_zatrudnienia, data_zwolnienia) FROM stdin;
1	2026-01-25 22:44:23.315	\N
4	2026-01-26 03:48:28.724591	\N
\.


--
-- Data for Name: klienci; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.klienci (id, imie, nazwisko, email, telefon, haslo, pytanie_pomocnicze, odp_na_pytanie_pom, data_utworzenia) FROM stdin;
1	Adam	Nowak	adam@nowak.pl	123123123	$2b$12$lpHBLGGynXpOypl/OY6.0OXf2R0PWAFOyEXud1xdHFhDVZoiMcIP6	Imię i nazwisko panieńskie matki?	Mariola	2026-01-25 21:25:42
2	Mariusz	Pudzianowski	pudzian@pudzian.pl	123123123	$2b$12$W4U/no.wJLKeydNQgejM..brXu1SRlJFrJoODt1wKEL2YQUacOv8S	Model Twojego pierwszego samochodu?	Multipla	2026-01-26 04:04:38.939337
\.


--
-- Data for Name: magazynierzy; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.magazynierzy (pracownik_id, data_zatrudnienia, data_zwolnienia) FROM stdin;
2	2026-01-26 02:39:22.282866	\N
\.


--
-- Data for Name: magazyny; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.magazyny (id, nazwa, adres, pojemnosc) FROM stdin;
1	Magazyn Główny	ul. Przemysłowa 54, Wrocław	10000
\.


--
-- Data for Name: modele_narzedzi; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.modele_narzedzi (id, nazwa_modelu, producent, kategoria, opis, cena_za_dobe, kaucja, wycofany, data_utworzenia) FROM stdin;
1	Wiertarka AX50	BOSCH	Elektronarzędzia		60.00	100.00	f	2026-01-25 23:37:14
2	Kosiarka P42S	GreenPower	Ogrodowe		100.00	300.00	f	2026-01-25 23:37:51
4	Zagęszczarka gruntu 90kg	Belle	Maszyny budowlane	Wydajna zagęszczarka do prac brukarskich i zagęszczania ścieżek.	110.00	500.00	f	2026-01-26 02:04:34
5	Betoniarka wolnospadowa 150L	Altrad	Maszyny budowlane	Solidna betoniarka zasilana 230V, idealna na małe place budowy.	55.00	300.00	f	2026-01-26 02:04:34
6	Młot wyburzeniowy 30kg	Bosch	Maszyny budowlane	Ekstremalna siła uderzenia (62J) do kucia w grubym betonie.	150.00	800.00	f	2026-01-26 02:04:34
7	Niwelator laserowy rotacyjny	Topcon	Technika pomiarowa	W pełni automatyczny laser do wyznaczania poziomów i spadków w terenie.	130.00	1000.00	f	2026-01-26 02:04:34
8	Kamera termowizyjna FLIR One	FLIR	Technika pomiarowa	Precyzyjne lokalizowanie wycieków i mostków termicznych w budynkach.	180.00	1500.00	f	2026-01-26 02:04:34
9	Kompresor olejowy 50L	Stanley	Pneumatyka	Uniwersalny kompresor do malowania, pompowania i narzędzi pneumatycznych.	40.00	200.00	f	2026-01-26 02:04:34
10	Agregat prądotwórczy 5.5kW	Honda	Agregaty	Niezawodne źródło zasilania awaryjnego z systemem stabilizacji napięcia AVR.	140.00	1200.00	f	2026-01-26 02:04:34
11	Glebogryzarka spalinowa	Stiga	Ogrodowe	Mocna glebogryzarka do przygotowania podłoża pod trawnik lub warzywniak.	120.00	600.00	f	2026-01-26 02:04:34
12	Rębak do gałęzi	Cedrus	Ogrodowe	Profesjonalny rozdrabniacz do gałęzi o średnicy do 10 cm.	200.00	1000.00	f	2026-01-26 02:04:34
13	Wertykulator spalinowy	Husqvarna	Ogrodowe	Usuwa filc z trawnika, zapewniając trawie lepszy dostęp do wody i powietrza.	90.00	400.00	f	2026-01-26 02:04:34
3	Młot pneumatyczny X1000	Pneumatic Company	Maszyny budowlane		500.00	1000.00	f	2026-01-25 23:42:06
\.


--
-- Data for Name: opinie; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.opinie (id, model_id, klient_id, ocena, komentarz, data_wystawienia) FROM stdin;
1	1	1	3	Mogło być lepiej. Po 2h intensywnego wiercenia, wiertarka się przegrzała. Ale no nie ma co się dziwić - za tą cenę to i tak okej.	2026-01-26 01:14:57.521647
2	2	1	1	Masakra, dwóm z wypożyczonych kosiarek prawie wybuchł silnik!!? to jakieś nieporozumienie, nie brać tego modelu!!!!!!	2026-01-26 01:37:44.692789
\.


--
-- Data for Name: pozycje_wypozyczenia; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.pozycje_wypozyczenia (id, wypozyczenie_id, egzemplarz_id, czy_zgloszono_usterke, opis_usterki) FROM stdin;
1	1	3	f	\N
2	1	4	f	\N
3	1	5	f	\N
4	1	6	f	\N
5	1	7	f	\N
6	1	8	f	\N
7	1	9	f	\N
8	1	10	f	\N
9	1	11	f	\N
10	1	12	f	\N
11	2	51	t	Silnik przestał działać
12	2	52	t	CZUĆ SPALENIZNE
13	2	53	f	\N
14	3	94	f	\N
15	3	95	f	\N
17	3	97	t	Czuć spaleniznę
16	3	96	t	Zepsuty
18	4	66	f	\N
19	4	68	f	\N
20	4	70	f	\N
21	4	71	f	\N
\.


--
-- Data for Name: pracownicy; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.pracownicy (id, imie, nazwisko, pesel, adres, telefon, email, login, haslo, data_utworzenia) FROM stdin;
2	Jan	Kowalski	21321321321	Kolorowa 23	322222223	jan@kowalski.pl	jan.kowalski	$2b$12$k.E0EmqQ6AYCBq7xbk8uMeyJRgRfN9ZTK/ASNt9XZYIzDGXrpPZT.	2026-01-25 22:59:29
3	Marcin	Nowak	88888888888	Kolorowa 25	892123590	marcin@nowak.pl	marcin.nowak	$2b$12$VWxj28O8wXf1VEDpmnKa4umTH0nQhb/3XQvjcxRnngJk1FbPmhBmC	2026-01-25 23:58:34
1	Andrzej	Kieras	12312312312	Przykładowy adres	793332020	andrzej.kieras.pl	andrzej.kieras	$2b$12$vJDjzbDYVEnf5ftc2hw.KO08fqYJHqYv80SRULoh5qPQNYuEbIVlK	2026-01-25 22:44:40
4	Anna	Szef	11100022233	Wrocław	999111222	anna@szef.pl	anna.szef	$2b$12$b8xrLk7q37VEjnnyi5anUeUrrR0C2BGFthp8MylsPWQDIygbVGgS2	2026-01-26 03:48:28.721954
\.


--
-- Data for Name: serwisanci; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.serwisanci (pracownik_id, data_zatrudnienia, data_zwolnienia) FROM stdin;
3	2026-01-25 23:58:34.193243	\N
\.


--
-- Data for Name: warsztaty; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.warsztaty (id, nazwa, adres) FROM stdin;
1	Warsztat Centralny	\N
2	Warsztat Serwisowy	ul. Serwisowa 5, Wrocław
\.


--
-- Data for Name: wypozyczenia; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.wypozyczenia (id, klient_id, magazynier_wydaj_id, magazynier_przyjmij_id, data_rezerwacji, data_plan_wydania, data_plan_zwrotu, data_faktyczna_wydania, data_faktyczna_zwrotu, status, koszt_calkowity) FROM stdin;
1	1	\N	\N	2026-01-26 00:51:53.162217	2026-01-26 00:00:00	2026-01-27 23:59:59.999999	2026-01-26 00:58:58.341812	2026-01-26 00:59:29.074681	ZAKOŃCZONA	600.00
2	1	\N	\N	2026-01-26 00:53:26.045569	2026-01-26 00:00:00	2026-01-30 23:59:59.999999	2026-01-26 00:59:04.78982	2026-01-26 01:34:37.390996	ZAKOŃCZONA	1200.00
3	1	\N	\N	2026-01-26 04:00:54.105443	2026-01-26 00:00:00	2026-01-29 23:59:59.999999	2026-01-26 04:01:44.269027	2026-01-26 04:03:20.141603	ZAKOŃCZONA	480.00
4	2	\N	\N	2026-01-26 04:05:18.441591	2026-01-28 00:00:00	2026-02-14 23:59:59.999999	\N	\N	REZERWACJA	7480.00
\.


--
-- Name: czynnosci_serwisowe_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.czynnosci_serwisowe_id_seq', 29, true);


--
-- Name: egzemplarze_narzedzi_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.egzemplarze_narzedzi_id_seq', 156, true);


--
-- Name: klienci_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.klienci_id_seq', 2, true);


--
-- Name: magazyny_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.magazyny_id_seq', 2, false);


--
-- Name: modele_narzedzi_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.modele_narzedzi_id_seq', 14, false);


--
-- Name: opinie_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.opinie_id_seq', 3, false);


--
-- Name: pozycje_wypozyczenia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.pozycje_wypozyczenia_id_seq', 21, true);


--
-- Name: pracownicy_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.pracownicy_id_seq', 4, true);


--
-- Name: warsztaty_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.warsztaty_id_seq', 3, false);


--
-- Name: wypozyczenia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.wypozyczenia_id_seq', 4, true);


--
-- Name: czynnosci_serwisowe czynnosci_serwisowe_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.czynnosci_serwisowe
    ADD CONSTRAINT czynnosci_serwisowe_pkey PRIMARY KEY (id);


--
-- Name: egzemplarze_narzedzi egzemplarze_narzedzi_numer_seryjny_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.egzemplarze_narzedzi
    ADD CONSTRAINT egzemplarze_narzedzi_numer_seryjny_key UNIQUE (numer_seryjny);


--
-- Name: egzemplarze_narzedzi egzemplarze_narzedzi_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.egzemplarze_narzedzi
    ADD CONSTRAINT egzemplarze_narzedzi_pkey PRIMARY KEY (id);


--
-- Name: kierownicy kierownicy_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.kierownicy
    ADD CONSTRAINT kierownicy_pkey PRIMARY KEY (pracownik_id);


--
-- Name: klienci klienci_email_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.klienci
    ADD CONSTRAINT klienci_email_key UNIQUE (email);


--
-- Name: klienci klienci_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.klienci
    ADD CONSTRAINT klienci_pkey PRIMARY KEY (id);


--
-- Name: magazynierzy magazynierzy_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.magazynierzy
    ADD CONSTRAINT magazynierzy_pkey PRIMARY KEY (pracownik_id);


--
-- Name: magazyny magazyny_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.magazyny
    ADD CONSTRAINT magazyny_pkey PRIMARY KEY (id);


--
-- Name: modele_narzedzi modele_narzedzi_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.modele_narzedzi
    ADD CONSTRAINT modele_narzedzi_pkey PRIMARY KEY (id);


--
-- Name: opinie opinie_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.opinie
    ADD CONSTRAINT opinie_pkey PRIMARY KEY (id);


--
-- Name: pozycje_wypozyczenia pozycje_wypozyczenia_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pozycje_wypozyczenia
    ADD CONSTRAINT pozycje_wypozyczenia_pkey PRIMARY KEY (id);


--
-- Name: pracownicy pracownicy_email_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pracownicy
    ADD CONSTRAINT pracownicy_email_key UNIQUE (email);


--
-- Name: pracownicy pracownicy_login_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pracownicy
    ADD CONSTRAINT pracownicy_login_key UNIQUE (login);


--
-- Name: pracownicy pracownicy_pesel_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pracownicy
    ADD CONSTRAINT pracownicy_pesel_key UNIQUE (pesel);


--
-- Name: pracownicy pracownicy_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pracownicy
    ADD CONSTRAINT pracownicy_pkey PRIMARY KEY (id);


--
-- Name: serwisanci serwisanci_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.serwisanci
    ADD CONSTRAINT serwisanci_pkey PRIMARY KEY (pracownik_id);


--
-- Name: pozycje_wypozyczenia uq_pozycja_wyp_egz; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pozycje_wypozyczenia
    ADD CONSTRAINT uq_pozycja_wyp_egz UNIQUE (wypozyczenie_id, egzemplarz_id);


--
-- Name: warsztaty warsztaty_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.warsztaty
    ADD CONSTRAINT warsztaty_pkey PRIMARY KEY (id);


--
-- Name: wypozyczenia wypozyczenia_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.wypozyczenia
    ADD CONSTRAINT wypozyczenia_pkey PRIMARY KEY (id);


--
-- Name: ix_czynnosci_serwisowe_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_czynnosci_serwisowe_id ON public.czynnosci_serwisowe USING btree (id);


--
-- Name: ix_egzemplarze_narzedzi_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_egzemplarze_narzedzi_id ON public.egzemplarze_narzedzi USING btree (id);


--
-- Name: ix_klienci_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_klienci_id ON public.klienci USING btree (id);


--
-- Name: ix_magazyny_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_magazyny_id ON public.magazyny USING btree (id);


--
-- Name: ix_modele_narzedzi_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_modele_narzedzi_id ON public.modele_narzedzi USING btree (id);


--
-- Name: ix_opinie_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_opinie_id ON public.opinie USING btree (id);


--
-- Name: ix_pozycje_wypozyczenia_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_pozycje_wypozyczenia_id ON public.pozycje_wypozyczenia USING btree (id);


--
-- Name: ix_pracownicy_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_pracownicy_id ON public.pracownicy USING btree (id);


--
-- Name: ix_warsztaty_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_warsztaty_id ON public.warsztaty USING btree (id);


--
-- Name: ix_wypozyczenia_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_wypozyczenia_id ON public.wypozyczenia USING btree (id);


--
-- Name: czynnosci_serwisowe czynnosci_serwisowe_egzemplarz_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.czynnosci_serwisowe
    ADD CONSTRAINT czynnosci_serwisowe_egzemplarz_id_fkey FOREIGN KEY (egzemplarz_id) REFERENCES public.egzemplarze_narzedzi(id);


--
-- Name: czynnosci_serwisowe czynnosci_serwisowe_serwisant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.czynnosci_serwisowe
    ADD CONSTRAINT czynnosci_serwisowe_serwisant_id_fkey FOREIGN KEY (serwisant_id) REFERENCES public.serwisanci(pracownik_id);


--
-- Name: egzemplarze_narzedzi egzemplarze_narzedzi_magazyn_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.egzemplarze_narzedzi
    ADD CONSTRAINT egzemplarze_narzedzi_magazyn_id_fkey FOREIGN KEY (magazyn_id) REFERENCES public.magazyny(id);


--
-- Name: egzemplarze_narzedzi egzemplarze_narzedzi_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.egzemplarze_narzedzi
    ADD CONSTRAINT egzemplarze_narzedzi_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.modele_narzedzi(id);


--
-- Name: egzemplarze_narzedzi egzemplarze_narzedzi_warsztat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.egzemplarze_narzedzi
    ADD CONSTRAINT egzemplarze_narzedzi_warsztat_id_fkey FOREIGN KEY (warsztat_id) REFERENCES public.warsztaty(id);


--
-- Name: kierownicy kierownicy_pracownik_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.kierownicy
    ADD CONSTRAINT kierownicy_pracownik_id_fkey FOREIGN KEY (pracownik_id) REFERENCES public.pracownicy(id) ON DELETE CASCADE;


--
-- Name: magazynierzy magazynierzy_pracownik_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.magazynierzy
    ADD CONSTRAINT magazynierzy_pracownik_id_fkey FOREIGN KEY (pracownik_id) REFERENCES public.pracownicy(id) ON DELETE CASCADE;


--
-- Name: opinie opinie_klient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.opinie
    ADD CONSTRAINT opinie_klient_id_fkey FOREIGN KEY (klient_id) REFERENCES public.klienci(id);


--
-- Name: opinie opinie_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.opinie
    ADD CONSTRAINT opinie_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.modele_narzedzi(id);


--
-- Name: pozycje_wypozyczenia pozycje_wypozyczenia_egzemplarz_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pozycje_wypozyczenia
    ADD CONSTRAINT pozycje_wypozyczenia_egzemplarz_id_fkey FOREIGN KEY (egzemplarz_id) REFERENCES public.egzemplarze_narzedzi(id);


--
-- Name: pozycje_wypozyczenia pozycje_wypozyczenia_wypozyczenie_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pozycje_wypozyczenia
    ADD CONSTRAINT pozycje_wypozyczenia_wypozyczenie_id_fkey FOREIGN KEY (wypozyczenie_id) REFERENCES public.wypozyczenia(id) ON DELETE CASCADE;


--
-- Name: serwisanci serwisanci_pracownik_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.serwisanci
    ADD CONSTRAINT serwisanci_pracownik_id_fkey FOREIGN KEY (pracownik_id) REFERENCES public.pracownicy(id) ON DELETE CASCADE;


--
-- Name: wypozyczenia wypozyczenia_klient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.wypozyczenia
    ADD CONSTRAINT wypozyczenia_klient_id_fkey FOREIGN KEY (klient_id) REFERENCES public.klienci(id);


--
-- Name: wypozyczenia wypozyczenia_magazynier_przyjmij_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.wypozyczenia
    ADD CONSTRAINT wypozyczenia_magazynier_przyjmij_id_fkey FOREIGN KEY (magazynier_przyjmij_id) REFERENCES public.magazynierzy(pracownik_id);


--
-- Name: wypozyczenia wypozyczenia_magazynier_wydaj_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.wypozyczenia
    ADD CONSTRAINT wypozyczenia_magazynier_wydaj_id_fkey FOREIGN KEY (magazynier_wydaj_id) REFERENCES public.magazynierzy(pracownik_id);


--
-- PostgreSQL database dump complete
--

\unrestrict FYcaRADnxMRLoe1bgGQidSEbV1JSfzAQxeotAQundPTONDjMhTJN8KvGENbATcW

