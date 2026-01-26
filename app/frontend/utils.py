def check_password_strength_live(password: str):
    """Funkcja wspólna dla Rejestracji i Zmiany hasła."""
    if not password:
        return 0, "Brak hasła", "gray"

    score = 0
    if len(password) >= 8: score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*(),.?\":{}|<>" for c in password): score += 1

    if score <= 1:
        return score, "🔴 Słabe hasło", "red"
    elif score < 4:
        return score, "🟡 Średnie hasło", "orange"
    else:
        return score, "🟢 Mocne hasło", "green"
