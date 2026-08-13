# Sales Inbox — RU microcopy

**status:** accepted-with-notes  
**last-review-date:** 2026-08-13  
**voice:** короткий RU, без сленга и emoji; директор и продажи — без жаргона L1  
**catalog:** [`sales-inbox-components.md`](./sales-inbox-components.md)  
**note:** строки copy ок по flight worksheet; UI = иконка + подпись на ключевых действиях

---

## App chrome

| Key | String |
| --- | --- |
| product_title | Мониторинг тендеров |
| tab_lots | Лоты |
| tab_run | Прогон |

---

## Login (P5.2)

| Key | String |
| --- | --- |
| login_username | Логин |
| login_password | Пароль |
| login_submit | Войти |
| login_error | Неверные логин или пароль |
| login_logout | Выйти |
| login_busy | Вход… |

Один текст ошибки на любой неуспешный вход. Нет «забыли пароль» и регистрации.

---

## Filters & view (Task D)

| Key | String |
| --- | --- |
| filter_unread | Непросмотренные |
| filter_menu | Фильтры |
| filter_menu_reset | Сбросить фильтры |
| filter_active_badge | {n} |
| filter_priority_hot | Горячие |
| filter_priority_strong | Сильные |
| filter_priority_watch | Смотреть |
| filter_bitrix_in | В Битрикс |
| filter_bitrix_out | Не в Битрикс |
| filter_deadline | Срок подачи |
| filter_ingested | Попало к нам |
| filter_date_any | Любой |
| filter_date_any_f | Любое |
| filter_deadline_7 | ≤ 7 дней |
| filter_deadline_14 | ≤ 14 дней |
| filter_deadline_30 | ≤ 30 дней |
| filter_ingested_today | Сегодня |
| filter_ingested_3 | За 3 дня |
| filter_ingested_7 | За 7 дней |
| filter_date_custom | Свой период |
| filter_date_from | С |
| filter_date_to | По |
| search_placeholder | Название, заказчик или номер |
| view_cards | Доска |
| view_table | Таблица |

Приоритет — меню **«Фильтры»** (чекбоксы списком). Даты — **отдельные** кнопки «Срок подачи» / «Попало к нам» (radio-список). «Непросмотренные» — кнопка с чекбоксом, не Chip.  
В bar нет date input и нет Chip как контроля фильтра. Пресеты дат: [007](../../delivery/tasks/007-date-filters.md) · визуал: [008](../../delivery/tasks/008-filters-personal-list.md).

---

## Priority chips (Task E)

| Key | String |
| --- | --- |
| chip_hot | Горячие |
| chip_strong | Сильные |
| chip_watch | Смотреть |
| chip_overridden_suffix | вручную |

Не показывать на вкладке Лоты: `L1`, `L2`, `L3`.  
На **карточке доски:** не показывать chip_hot/strong/watch и не показывать «новое»; chip «вручную» — только при ручном приоритете.  
В **таблице:** chip приоритета ок.

---

## List / table headers

| Key | String |
| --- | --- |
| col_priority | Приоритет |
| col_title | Название |
| col_customer | Заказчик |
| col_location | Где работать |
| col_platform | Площадка |
| col_deadline | Срок |
| col_price | НМЦ |
| card_location | Где работать |
| platform_icon_aria | Площадка: {name} |
| col_bitrix | Битрикс |

---

## Drawer

| Key | String |
| --- | --- |
| drawer_close_aria | Закрыть |
| link_on_site | На площадке |
| section_key_fields | (без заголовка — сразу field rows) |
| field_price | НМЦ |
| field_deadline | Срок подачи |
| field_region | Регион |
| field_status | Статус |
| field_empty | Нет данных |
| section_fit | Почему подходит |
| section_contacts | Контакты |
| section_docs | Документы |
| action_mark_viewed | Отметить просмотренным |
| action_viewed_done | Просмотрено |
| action_change_priority | Изменить приоритет |
| action_bitrix | Отправить в Битрикс |
| bitrix_soon | Скоро |
| bitrix_soon_hint | Отправка в Битрикс появится позже |

Футер drawer: `action_viewed_done` — лейбл **Switch** (состояние). `action_mark_viewed` не на кнопке. [009](../../delivery/tasks/009-drawer-switch-file-icons.md).

---

## DocumentsList

| Key | String |
| --- | --- |
| docs_empty_not_downloaded | Файлы ещё не скачаны. Появятся после загрузки документации прогона. |
| docs_empty_none | К этой закупке нет приложенных файлов. |
| docs_error | Не удалось показать документы. |
| docs_download | Скачать |

Ряд файла: `FileTypeIcon` 16–18px слева от имени (цвет по расширению).

---

## BitrixStatus (list)

| Key | String |
| --- | --- |
| bitrix_badge_soon | Скоро |
| bitrix_none | Нет |
| bitrix_created | В Битрикс |
| bitrix_error | Ошибка |

До API в списке и drawer использовать только **Скоро**.

---

## Empty / error (Лоты)

| Key | String |
| --- | --- |
| empty_no_data_title | Пока нет подходящих лотов |
| empty_no_data_body | Запустите прогон на вкладке «Прогон» или дождитесь окончания текущего. |
| empty_no_match_title | Нет лотов по текущим фильтрам |
| empty_no_match_body | Снимите часть фильтров или измените поисковый запрос. |
| empty_no_unread_title | Все лоты просмотрены |
| empty_no_unread_body | Снимите фильтр «Непросмотренные», чтобы увидеть все. |
| error_load_title | Не удалось загрузить лоты |
| error_load_body | Обновите страницу. Если ошибка повторяется — проверьте прогон на вкладке «Прогон». |

---

## Tech tab

| Key | String |
| --- | --- |
| run_start | Старт |
| run_stop | Стоп |
| session_ok | Сессия: cookies OK |
| session_expired | Сессия: cookies истекли — обновите файл cookies |
| session_missing | Нет файла cookies — положите cookies по инструкции |
| phase_list | Фаза: список |
| phase_score | Фаза: оценка |
| phase_cards | Фаза: карточки |
| phase_artifacts | Фаза: файлы |
| phase_idle | Ожидание прогона |
| phase_done | Прогон завершён |
| phase_stopped | Прогон остановлен |
| phase_error | Прогон завершился с ошибкой |
| progress_list | Список: {n} / {total} |
| progress_cards | Карточки: {k} / {total} |
| counters_legend | Счётчики fit (L1–L3) |
| run_path_label | Путь прогона |
| run_path_copy | Копировать |
| run_path_copied | Скопировано |
| log_title | Лог |
| log_empty | Записей пока нет |
| tech_readonly_note | Старт и стоп прогона в этом экране отключены |

Tech может показывать `L1` / `L2` / `L3` в счётчиках — это норма. `run_start` / `run_stop` в каноне остаются; в React P6 кнопки не показываем.

---

## Confirmations (override)

| Key | String |
| --- | --- |
| override_menu_title | Приоритет |
| override_done | Приоритет изменён |

Отдельный modal confirm не обязателен: смена из меню достаточна; при необходимости soft toast «Приоритет изменён».

---

## Handoff

Строки — канон для UI после owner accepted. Frontend не изобретает синонимы без ux-writer.
