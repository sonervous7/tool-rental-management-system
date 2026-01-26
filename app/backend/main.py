import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.backend.api import router_users, router_inventory, router_rentals, router_analytics

app = FastAPI(
    title="RentTool PRO API",
    description="System zarządzania wypożyczalnią narzędzi - Backend v1.0",
    version="1.0.0"
)

# CORS - żeby Streamlit mógł bez problemu wołać API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_users.router)
app.include_router(router_inventory.router)
app.include_router(router_rentals.router)
app.include_router(router_analytics.router)

if __name__ == "__main__":
    # Start: uvicorn app.backend.main:app --reload
    uvicorn.run("app.backend.main:app", host="0.0.0.0", port=8000, reload=True)
