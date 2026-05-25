import os
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    import psycopg2
    import redis
except ModuleNotFoundError as exc:
    print(f"Dependencia Python ausente: {exc.name}")
    print("Execute dentro da venv do projeto ou instale as dependencias de requirements.txt.")
    sys.exit(1)


REQUIRED_ENV = ("SECRET_KEY", "DATABASE_URL", "REDIS_URL", "POSTGRES_PASSWORD")


def check_env_vars():
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        print("Variaveis ausentes: " + ", ".join(missing))
        return False
    print("Variaveis obrigatorias: OK")
    return True


def check_postgres():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("PostgreSQL: FALHA (DATABASE_URL ausente)")
        return False
    try:
        conn = psycopg2.connect(database_url, connect_timeout=5)
        conn.close()
    except Exception as exc:
        print(f"PostgreSQL: FALHA ({exc})")
        return False
    print("PostgreSQL: OK")
    return True


def check_redis():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("Redis: FALHA (REDIS_URL ausente)")
        return False
    try:
        client = redis.from_url(redis_url, socket_connect_timeout=5)
        client.ping()
    except Exception as exc:
        print(f"Redis: FALHA ({exc})")
        return False
    print("Redis: OK")
    return True


def check_pdf_temp():
    path = Path(os.getenv("PDF_TEMP_DIR", "pdf_temp"))
    if not path.exists():
        print(f"Diretorio de PDFs: FALHA ({path} nao existe)")
        return False
    if not path.is_dir():
        print(f"Diretorio de PDFs: FALHA ({path} nao e diretorio)")
        return False
    print(f"Diretorio de PDFs: OK ({path})")
    return True


def main():
    load_dotenv()
    checks = [
        check_env_vars(),
        check_postgres(),
        check_redis(),
        check_pdf_temp(),
    ]
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
