import psycopg2
from psycopg2.extensions import AsIs

def display_postgres_database():
    # 1. Читаем доступы из .env
    env_data = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_data[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        print("Файл .env не найден!")
        return

    # Если в .env у вас только DATABASE_URL, распарсим её
    if "DATABASE_URL" in env_data and not "DB_NAME" in env_data:
        # Пример: postgresql+asyncpg://user:pass@host:port/dbname
        url = env_data["DATABASE_URL"].replace("postgresql+asyncpg://", "")
        auth, rest = url.split("@")
        user, password = auth.split(":")
        host_port, dbname = rest.split("/")
        host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
    else:
        user = env_data.get("DB_USER")
        password = env_data.get("DB_PASSWORD")
        host = env_data.get("DB_HOST", "localhost")
        port = env_data.get("DB_PORT", "5432")
        dbname = env_data.get("DB_NAME")

    # 2. Подключаемся к Postgres
    try:
        conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"Не удалось подключиться к PostgreSQL: {e}")
        return

    # 3. Получаем список всех пользовательских таблиц
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' AND table_type='BASE TABLE';
    """)
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        print("\n" + "="*80)
        print(f" ТАБЛИЦА: {table.upper()}")
        print("="*80)

        # Получаем названия колонок
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema='public'
            ORDER BY ordinal_position;
        """, (table,))
        columns = [row[0] for row in cursor.fetchall()]

        # Получаем данные
        cursor.execute("SELECT * FROM %s;", (AsIs(table),))
        rows = cursor.fetchall()

        if not rows:
            print(" Таблица пустая.")
            continue

        # Считаем ширину колонок
        widths = [len(col) for col in columns]
        for row in rows:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val if val is not None else "None")))

        # Выводим заголовок
        header_line = " | ".join(f"{col:<{widths[i]}}" for i, col in enumerate(columns))
        print(header_line)
        print("-" * len(header_line))

        # Выводим строки
        for row in rows:
            row_line = " | ".join(f"{str(val if val is not None else 'None'):<{widths[i]}}" for i, val in enumerate(row))
            print(row_line)

    conn.close()

if __name__ == "__main__":
    display_postgres_database()

