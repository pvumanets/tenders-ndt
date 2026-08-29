# Sales Inbox — RU microcopy

**status:** accepted-with-notes  
**last-review-date:** 2026-08-29  
**voice:** короткий RU, без сленга и emoji; директор и продажи — без жаргона L1  
**catalog:** [`sales-inbox-components.md`](./sales-inbox-components.md)  
**note:** строки copy ок по flight worksheet; UI = иконка + подпись на ключевых действиях  
**Прогон TO-BE:** [`../search-groups.md`](../search-groups.md) · [047](../../delivery/tasks/047-run-ux-copy.md)

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
| chip_expired | Просроченные |
| badge_deadline_expired | Срок подачи вышел |
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
| action_archive | В архив |
| action_restore_board | Вернуть на доску |
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

## Tech tab (Прогон) — TO-BE 044+

Primary UI **не** показывает имена cookie-файлов и «Путь/папку прогона» в основном потоке. Файлы cookies — только в [`../../delivery/auth-cookies.md`](../../delivery/auth-cookies.md) / ops.  
Review: [UX copy rethink](b79f82c4-c3c9-46e4-94f8-6506df6e55da) 2026-08-29.

### Секции

Рендерить **один** заголовок секции (`run_section_*`). Не дублировать `groups_title` рядом с `run_section_groups`.

| Key | String |
| --- | --- |
| run_section_controls | Управление |
| run_section_platforms | Площадки |
| run_section_groups | Группы поиска |
| run_section_diagnostics | Диагностика |

### Управление

| Key | String |
| --- | --- |
| run_start | Старт |
| run_stop | Стоп |
| run_start_busy | Запуск… |
| run_idle_hint | Нажмите «Старт», когда площадки и группы готовы. |
| run_running_hint | Прогон идёт. «Стоп» прервёт текущий шаг и очередь. |
| run_queue_summary | Очередь: {groups} групп × {platforms} площадки → {steps} шагов |
| run_queue_empty | Очередь пуста — включите группу и площадку |
| run_queue_step | Шаг {current}/{total} · {group} × {platform} |
| phase_idle | Ожидание прогона |
| phase_list | Фаза: список |
| phase_score | Фаза: оценка |
| phase_cards | Фаза: карточки |
| phase_artifacts | Фаза: файлы |
| phase_done | Прогон завершён |
| phase_partial | Прогон завершён частично |
| phase_stopped | Прогон остановлен |
| phase_error | Прогон завершился с ошибкой |
| progress_list | Список: {n} / {total} |
| progress_cards | Карточки: {k} / {total} |
| counters_legend | Счётчики L1–L3 |
| run_report_legend | Отчёт прогона |
| run_report_new | Новые лоты |
| run_report_already | Уже были в системе |
| run_report_updated | Обновлено с площадки |
| run_report_expired | Ушли в просроченные |
| queue_position | Очередь: {current} из {total} |
| queue_status_pending | ждёт |
| queue_status_running | идёт |
| queue_status_done | готово |
| queue_status_skipped | пропущен |
| queue_status_error | ошибка |
| queue_status_cancelled | отменён |

### Площадки — единый словарь статусов

Шаблон primary: `{platform_name}: {session_label}`. Имена файлов cookies **не** в primary.  
Не смешивать статус сессии и тогл «Участвует» в одной фразе.

| Key | String |
| --- | --- |
| platform_participate | Участвует |
| platform_rostender | РосТендер |
| platform_tender_pro | Tender.Pro |
| platform_roseltorg | Росэлторг |
| session_status_ok | сессия в порядке |
| session_status_missing | нет сессии |
| session_status_expired | сессия устарела |
| session_status_list_without_login | вход для списка не нужен |
| session_status_unknown | статус неизвестен |
| session_hint_docs | Как обновить сессию — в инструкции |
| platforms_none_enabled | Нет включённых площадок |
| platforms_none_enabled_body | Включите хотя бы одну площадку в блоке «Площадки». |

Спец-кейс Tender.Pro: primary = `Tender.Pro: вход для списка не нужен` (норма, не ошибка). Файлы лотов без сессии — hint в docs, не в строке статуса списка.

### Группы поиска

Заголовок секции = `run_section_groups` (не второй `groups_title` в UI).

| Key | String |
| --- | --- |
| groups_queue | В очереди |
| groups_add | Новая группа |
| groups_save | Сохранить |
| groups_cancel | Отмена |
| groups_delete | Удалить |
| groups_edit | Править |
| groups_name | Имя |
| groups_queries | Плюс — запросы (по одному на строку) |
| groups_exclude | Минус — отсечь по заголовку |
| groups_exclude_hint | Минус отсекает строки списка этой группы до доски. На другие группы не действует. |
| groups_limit | Лимит |
| groups_limit_hint | 0 — без потолка |
| groups_empty | Нет групп поиска |
| groups_empty_body | Создайте группу с плюс-запросами — она пойдёт на все включённые площадки. |
| groups_none_queued | Нет групп в очереди |
| groups_none_queued_body | Включите «В очереди» хотя бы у одной группы. |
| groups_save_failed | Не удалось сохранить группу |
| groups_duplicate_name | Группа с таким именем уже есть |
| groups_delete_confirm | Удалить эту группу? |
| groups_drawer_title | Группа поиска |
| groups_drawer_close_aria | Закрыть |

Приоритет empty на экране: нет групп → нет площадок → нет в очереди (не показывать сразу два).

### Ошибки Старта

| Key | String |
| --- | --- |
| run_error_already | Прогон уже идёт |
| run_error_cookies | Нет сессии площадки — обновите сессию по инструкции |
| run_error_failed | Не удалось запустить прогон. Обновите страницу и повторите. |
| run_error_empty_queue | Включите хотя бы одну группу и одну площадку |

### Диагностика (свёрнуто)

| Key | String |
| --- | --- |
| diagnostics_title | Диагностика |
| diagnostics_expand | Показать |
| diagnostics_collapse | Скрыть |
| log_title | Лог |
| log_empty | Записей пока нет |
| run_path_label | Папка прогона |
| run_path_copy | Копировать |
| run_path_copied | Скопировано |

`run_path_*` — **только** внутри диагностики (или не рендерить). Не в секции «Управление». Не возвращать лейбл «Путь прогона».

### Legacy keys (AS-IS runtime до 049 — не для нового UI)

Не использовать в TO-BE primary: `session_ok`, `session_rostender_*` с «cookies OK», `session_tender_pro` с именем файла, `searches_*` с «Площадка» в drawer, `run_path_label` вне диагностики.

| Key | String (historical) |
| --- | --- |
| searches_title | Поиски |
| searches_platform | Площадка |
| searches_tender_pro_docs | (MVP; не primary TO-BE) |
| session_rostender_ok | РосТендер: cookies OK |
| session_tender_pro | Tender.Pro: список без cookies; файлы — с cookies.tender-pro.txt |

Tech показывает `L1` / `L2` / `L3` в счётчиках — это норма. Старт/Стоп и группы — после [049](../../delivery/tasks/049-search-groups-ui.md). Сессия — **по площадке**, единый словарь. Query/exclude/limit — в группе, не на кнопке Старт.

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
