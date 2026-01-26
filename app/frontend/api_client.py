import requests
import os
import streamlit as st

BASE_URL = os.getenv("API_URL", "http://localhost:8000")


class APIClient:
    @staticmethod
    def get(endpoint, params=None):
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", params=params)
            return response
        except Exception as e:
            st.error(f"Błąd połączenia z API: {e}")
            return None

    @staticmethod
    def post(endpoint, data=None, params=None):
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, params=params)
            return response
        except Exception as e:
            st.error(f"Błąd połączenia z API: {e}")
            return None

    @staticmethod
    def patch(endpoint, data=None, params=None):
        try:
            response = requests.patch(f"{BASE_URL}{endpoint}", json=data, params=params)
            return response
        except Exception as e:
            st.error(f"Błąd połączenia z API: {e}")
            return None

    @staticmethod
    def delete(endpoint):
        try:
            response = requests.delete(f"{BASE_URL}{endpoint}")
            return response
        except Exception as e:
            st.error(f"Błąd połączenia z API: {e}")
            return None
