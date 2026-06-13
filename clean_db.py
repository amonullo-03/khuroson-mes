import sqlite3

def clean_transactions_exactly():
    conn = sqlite3.connect('khuroson_mes.db')
    cursor = conn.cursor()
    try:
        print("Запуск точной очистки транзакций...")

        # Группируем по комментарию и количеству, оставляя только первую транзакцию из пачки дубликатов
        cursor.execute("""
            DELETE FROM material_transactions 
            WHERE transaction_type = 'OUTFLOW' 
              AND id NOT IN (
                  SELECT MIN(id) 
                  FROM material_transactions 
                  WHERE transaction_type = 'OUTFLOW'
                  GROUP BY comment, quantity
              );
        """)
        
        conn.commit()
        print("✅ Лишние транзакции списания успешно удалены!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clean_transactions_exactly()

