#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Audit Log функциональности.
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from backend.database.users_db import get_database

def test_audit_log():
    """Тестирует функции audit log"""
    print("=" * 60)
    print("🧪 Тестирование Audit Log функциональности")
    print("=" * 60)
    
    db = get_database()
    
    # Тест 1: Логирование действия
    print("\n1️⃣ Тест: Логирование действия set_level")
    success = db.log_admin_action(
        admin_user_id="test_admin_123",
        admin_username="@testadmin",
        action_type="set_level",
        target_user_id="test_user_456",
        old_value="user",
        new_value="subscriber",
        chat_id="-1001234567890",
        message_id=999,
        success=True,
        details={"test": True}
    )
    print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
    
    # Тест 2: Логирование действия add_user
    print("\n2️⃣ Тест: Логирование действия add_user")
    success = db.log_admin_action(
        admin_user_id="test_admin_123",
        admin_username="@testadmin",
        action_type="add_user",
        target_user_id="new_user_789",
        chat_id="-1001234567890",
        message_id=1000,
        success=True
    )
    print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
    
    # Тест 3: Логирование действия view_history
    print("\n3️⃣ Тест: Логирование действия view_history")
    success = db.log_admin_action(
        admin_user_id="test_admin_123",
        admin_username="@testadmin",
        action_type="view_history",
        target_user_id="test_user_456",
        details={"limit": 50},
        chat_id="-1001234567890",
        message_id=1001,
        success=True
    )
    print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
    
    # Тест 4: Получение записей из audit log
    print("\n4️⃣ Тест: Получение записей из audit log")
    logs = db.get_admin_audit_log(admin_user_id="test_admin_123", limit=10)
    print(f"   Найдено записей: {len(logs)}")
    if logs:
        print("   Последние записи:")
        for log in logs[:3]:
            print(f"   - {log.get('action_type')}: {log.get('target_user_id')} ({log.get('created_at', '')[:19]})")
    else:
        print("   ⚠️ Записи не найдены")
    
    # Тест 5: Получение статистики администратора
    print("\n5️⃣ Тест: Получение статистики администратора")
    stats = db.get_admin_stats("test_admin_123")
    if stats:
        print(f"   Статистика:")
        print(f"   - Всего действий: {stats.get('total_actions', 0)}")
        print(f"   - Успешных: {stats.get('successful_actions', 0)}")
        print(f"   - Изменений уровня: {stats.get('level_changes', 0)}")
        print(f"   - Добавлено пользователей: {stats.get('users_added', 0)}")
    else:
        print("   ⚠️ Статистика не получена")
    
    # Тест 6: Получение записей по целевому пользователю
    print("\n6️⃣ Тест: Получение записей по целевому пользователю")
    logs = db.get_admin_audit_log(target_user_id="test_user_456", limit=10)
    print(f"   Найдено записей: {len(logs)}")
    if logs:
        print("   Записи:")
        for log in logs:
            icon = "✅" if log.get('success', True) else "❌"
            print(f"   {icon} {log.get('action_type')} by {log.get('admin_user_id')}")
    
    # Тест 7: Проверка поддержки Supabase vs SQLite
    print("\n7️⃣ Тест: Проверка типа базы данных")
    from backend.database.users_db import USE_SUPABASE
    if USE_SUPABASE:
        print("   📡 Используем Supabase")
    else:
        print("   💾 Используем SQLite")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    print("=" * 60)
    
    # Вывод итоговой таблицы
    print("\n📊 Итоговая таблица записей:")
    print("-" * 80)
    all_logs = db.get_admin_audit_log(limit=20)
    
    if all_logs:
        print(f"{'ID':<5} {'Action':<15} {'Admin':<20} {'Target':<20} {'Success':<8} {'Time':<20}")
        print("-" * 80)
        for log in all_logs[:10]:
            log_id = str(log.get('id', 'N/A'))[:5]
            action = str(log.get('action_type', 'N/A'))[:15]
            admin = str(log.get('admin_user_id', 'N/A'))[:20]
            target = str(log.get('target_user_id', 'N/A'))[:20]
            success = "✅" if log.get('success', True) else "❌"
            time = str(log.get('created_at', 'N/A'))[:20]
            print(f"{log_id:<5} {action:<15} {admin:<20} {target:<20} {success:<8} {time:<20}")
    else:
        print("Записи не найдены")
    
    print("-" * 80)


if __name__ == "__main__":
    try:
        test_audit_log()
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
