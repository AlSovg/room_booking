# Тестирование

Запуск: `docker compose up -d db`, `alembic upgrade head`; бэкенд — `cd backend && .venv/Scripts/python -m pytest`; фронтенд — `cd frontend && npx vitest run`.
Тесты бэкенда идут в реальный PostgreSQL; каждый — во внешней транзакции с откатом (`tests/conftest.py`). Исключение — гонка.

| Уровень | Файл | Что проверяет |
|---|---|---|
| Unit (без БД) | `backend/tests/test_rules.py` | `overlaps` (встык, совпадающие, вложенные, частичные, далеко), интервал 15 мин–8 ч, шаг 15 мин, рабочие часы в зоне организации, прошлое, вместимость, право менять |
| Констрейнты БД | `backend/tests/test_schema.py` | `23P01` на пересечении, встык и отменённая бронь допустимы, `23514` на неверную длительность |
| Интеграция API | `backend/tests/test_bookings.py`, `test_rooms.py`, `test_auth_users.py`, `test_notifications.py`, `test_stats.py` | создание, 409 с данными конфликтующей брони, изменение, отмена, права, календарь, «мои брони», поиск свободных, уведомления, статистика |
| Гонка | `backend/tests/test_race.py` | два потока, два соединения, реальные коммиты, 5 слотов подряд: всегда одна бронь `ok` и один `BOOKING_CONFLICT` |
| Фронтенд | `frontend/src/utils/time.test.ts` | утилиты времени и часовых поясов |

## Результаты прогона критериев приёмки
Прогон 2026-10-02: PostgreSQL 16 в Docker, бэкенд — 65 passed, фронтенд — 6 passed. AC-17 проверен вручную в браузере (Chrome).

| # | Сценарий | Проверка | Результат |
|---|---|---|---|
| AC-1 | 10:00–11:00 и 10:30–11:30 в одной комнате | `test_bookings.py::test_conflict_returns_409_with_conflicting_booking` | ✅ 409 `BOOKING_CONFLICT`, в ответе первая бронь |
| AC-2 | 10:00–11:00 и 11:00–12:00 | `test_bookings.py::test_adjacent_and_other_room_are_fine`, `test_schema.py` | ✅ обе приняты |
| AC-3 | Те же интервалы в разных комнатах | `test_bookings.py::test_adjacent_and_other_room_are_fine` | ✅ обе приняты |
| AC-4 | Изменение без смены времени | `test_bookings.py::test_patch_without_time_change_and_self_overlap_ok` | ✅ 200 |
| AC-5 | Отмена и новая бронь на тот же слот | `test_bookings.py::test_cancel_frees_slot_and_is_idempotent` | ✅ новая принята (201) |
| AC-6 | Два параллельных запроса на слот | `test_race.py::test_parallel_bookings_one_wins` | ✅ один 201, один 409, 5 повторов |
| AC-7 | Поиск на 10:00–11:00 | `test_bookings.py::test_available_rooms` | ✅ занятая и малые комнаты исключены, отменённая бронь не мешает |
| AC-8 | Сотрудник меняет чужую бронь | `test_bookings.py::test_patch_permissions` | ✅ 403; админ — 200 |
| AC-9 | 07:45–08:45, 19:45–20:15, 5 мин, 9 ч | `test_bookings.py::test_rule_violations_422` | ✅ 422: `OUTSIDE_WORKING_HOURS` ×2, `INVALID_DURATION` ×2 |
| AC-10 | Бронь в прошлом | `test_bookings.py::test_past_inactive_missing_room_and_bad_input` | ✅ 422 `BOOKING_IN_PAST` |
| AC-11 | Участников больше вместимости | `test_bookings.py::test_rule_violations_422` | ✅ 422 `CAPACITY_EXCEEDED` |
| AC-12 | Бронь стартует через 15 минут | `test_notifications.py::test_reminder_once_only_for_active_upcoming` | ✅ ровно одно напоминание, повторный проход — 0 |
| AC-13 | Админ отменил чужую бронь | `test_notifications.py::test_changed_and_cancelled_by_admin_notify_owner_but_own_actions_do_not` | ✅ уведомление у организатора; свои действия — без уведомлений |
| AC-14 | Вход заблокированного | `test_auth_users.py::test_block_takes_effect_immediately_and_unblock` | ✅ 403 `ACCOUNT_DISABLED`, в т. ч. для уже выданного токена |
| AC-15 | Сотрудник открывает статистику | `test_stats.py::test_stats_numbers_csv_and_access` | ✅ 403 |
| AC-16 | 6 ч при рабочем дне 12 ч | `test_stats.py::test_stats_numbers_csv_and_access` | ✅ `utilization` = 0.5 |
| AC-17 | Клик по свободному слоту | Вручную: календарь → «Волга», 14:00 | ✅ форма «Новая бронь»: Волга, 02.10.2026, 14:00–14:15 |

Итог: 17/17 пройдено.
