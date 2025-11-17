from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///zakupki.db")

with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO purchases (number, customer, subject, amount, dates, status, link)
        VALUES ('11111', 'Тестовый заказчик', 'Тестовый предмет', '12345', '2025-11-10', 'active', 'https://example.com')
    """))
    conn.commit()

    rows = conn.execute(text("SELECT * FROM purchases")).fetchall()

print(rows)
