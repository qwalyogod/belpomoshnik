from backend.database import SessionLocal
from backend.seeds.mvp_childbirth import seed_mvp_childbirth
from backend.seeds.full_content import seed_full_content


def run() -> None:
    db = SessionLocal()
    try:
        result = seed_mvp_childbirth(db)
        print("MVP seed применен:", result)
        full = seed_full_content(db)
        print("Полный контент из Flet-макета применён:", full)
    finally:
        db.close()


if __name__ == "__main__":
    run()
