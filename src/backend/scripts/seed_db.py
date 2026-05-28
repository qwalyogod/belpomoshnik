from backend.database import SessionLocal
from backend.seeds.mvp_childbirth import seed_mvp_childbirth


def run() -> None:
    db = SessionLocal()
    try:
        result = seed_mvp_childbirth(db)
        print("MVP seed применен:", result)
    finally:
        db.close()


if __name__ == "__main__":
    run()

