from backend.scripts.migrate import run as run_migrations


def run() -> None:
    run_migrations()


if __name__ == "__main__":
    run()

