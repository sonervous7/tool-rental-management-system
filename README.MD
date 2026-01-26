<p align="center">
  <a href="#polish-version">🇵🇱 Polish</a> |
  <a href="#english-version">🇬🇧 English</a>
</p>



<a name="polish-version"></a>
# Rental System PRO – System Zarządzania Wypożyczalnią Narzędzi

Zintegrowana platforma webowa do zarządzania procesami wypożyczalni narzędzi budowlanych i ogrodowych. Projekt realizuje pełny obieg dokumentacji i sprzętu: od rezerwacji klienta, przez wydanie magazynowe, aż po obsługę serwisową i opinie użytkowników.

---

## 🛠️ Stack Technologiczny

Projekt został zbudowany w architekturze mikroserwisowej z wykorzystaniem nowoczesnych standardów:

* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11).
* **Frontend:** [Streamlit](https://streamlit.io/).
* **Baza Danych:** [PostgreSQL 15](https://www.postgresql.org/).
* **ORM & Walidacja:** [SQLAlchemy](https://www.sqlalchemy.org/) oraz [Pydantic](https://docs.pydantic.dev/).
* **Konteneryzacja:** [Docker](https://www.docker.com/) & **Docker Compose** – pełna izolacja i powtarzalność środowiska.
* **Zarządzanie pakietami:** [Poetry](https://python-poetry.org/) (zarządzanie deweloperskie) oraz `requirements.txt` (konteneryzacja).
* **Bezpieczeństwo:** Haszowanie haseł za pomocą biblioteki `bcrypt`.

---

## 📂 Struktura Projektu

```text
tool-rental-management-system/
├── app/                        # Kod źródłowy aplikacji
│   ├── backend/                # API, modele bazy danych, logika biznesowa
│   └── frontend/               # Interfejs Streamlit, widoki, komponenty
├── init-db/                    # Inicjalizacja bazy danych
│   └── backup.sql              # Główny zrzut danych (pracownicy, klienci, narzędzia)
├── docker-compose.yml          # Orkiestracja kontenerów
├── Dockerfile.backend          # Definicja kontenera API
├── Dockerfile.frontend         # Definicja kontenera UI
└── README.md                   # Dokumentacja projektu
```
## 🚀 Instalacja i Uruchomienie

1. **Sklonuj repozytorium lub rozpakuj paczkę ZIP.**
2. **Skonfiguruj zmienne środowiskowe:** lub skorzystaj z domyślnych wartości w `docker-compose.yml`.
3. **Uruchom kontenery:** W terminalu, w folderze głównym projektu, wpisz: `docker-compose up -d --build`.
4. **Dostęp do aplikacji:**
   - **Frontend:** http://localhost:8501
   - **Dokumentacja API (Swagger):** http://localhost:8000/docs

## 📈 Kluczowe Funkcjonalności

- **Katalog z cache'owaniem:** Dynamiczne filtrowanie narzędzi po kategorii, producencie i cenie.

- **System Rezerwacji**: Automatyczne obliczanie kosztu najmu oraz kaucji zwrotnej.

- **Panel Serwisowy:** Zgłaszanie usterek przez klienta i zarządzanie naprawami przez serwisanta.

- **Opinie:** Możliwość oceniania sprzętu (system gwiazdkowy) po zakończeniu wynajmu.

- **Zasoby:** Moduł przyjmowania nowych dostaw narzędzi do magazynu przez pracowników.


<a name="english-version"></a>
# Rental System PRO – Tool Rental Management System

An integrated web platform for managing the processes of a construction and gardening tool rental service.  
The project covers the full lifecycle of equipment and documentation — from customer reservation, through warehouse issuance, to service handling and user feedback.

---

## 🛠️ Technology Stack

The project is built using a microservices-oriented architecture and modern development standards:

* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
* **Frontend:** [Streamlit](https://streamlit.io/)
* **Database:** [PostgreSQL 15](https://www.postgresql.org/)
* **ORM & Validation:** [SQLAlchemy](https://www.sqlalchemy.org/) and [Pydantic](https://docs.pydantic.dev/)
* **Containerization:** [Docker](https://www.docker.com/) & **Docker Compose** – full environment isolation and reproducibility
* **Dependency Management:** [Poetry](https://python-poetry.org/) (development) and `requirements.txt` (containerization)
* **Security:** Password hashing using the `bcrypt` library

---

## 📂 Project Structure

```text
tool-rental-management-system/
├── app/                        # Application source code
│   ├── backend/                # API, database models, business logic
│   └── frontend/               # Streamlit interface, views, components
├── init-db/                    # Database initialization
│   └── backup.sql              # Main data dump (employees, clients, tools)
├── docker-compose.yml          # Container orchestration
├── Dockerfile.backend          # API container definition
├── Dockerfile.frontend         # UI container definition
└── README.md                   # Project documentation
```

## 🚀 Installation and Setup

1. **Clone the repository or extract the ZIP package.**
2. **Configure environment variables** or use the default values provided in `docker-compose.yml`.
3. **Start the containers:**  
   In the root project directory, run:  
   `docker-compose up -d --build`
4. **Access the application:**
   - **Frontend:** http://localhost:8501
   - **API documentation (Swagger):** http://localhost:8000/docs


## 📈 Key Features

- **Catalog with caching:** Dynamic tool filtering by category, manufacturer, and price.

- **Reservation System:** Automatic calculation of rental cost and refundable deposit.

- **Service Panel:** Fault reporting by customers and repair management by service staff.

- **Reviews:** Star-based rating system available after rental completion.

- **Inventory Management:** Module for registering new tool deliveries by warehouse employees.
