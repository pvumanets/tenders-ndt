/** Column catalog + AI review preset for inbox export (story 100). */

export type ExportFormat = "csv" | "xlsx";

export type ExportColumnKey =
  | "tender_id"
  | "title"
  | "customer_name"
  | "customer_inn"
  | "location"
  | "status"
  | "url"
  | "source_platform_id"
  | "price_rub"
  | "deadline_msk"
  | "published_msk"
  | "ingested_at"
  | "deadline_expired"
  | "score"
  | "fit_reason"
  | "rules_tier"
  | "ai_tier"
  | "manual_tier"
  | "effective_tier"
  | "ai_reviewed"
  | "ai_trigger"
  | "ai_reason_ru"
  | "ai_error"
  | "ai_wrong"
  | "ai_wrong_note"
  | "viewed"
  | "board_hidden"
  | "bitrix_sent_at"
  | "contact_name"
  | "contact_phone"
  | "contact_email"
  | "documents_count";

export type ExportColumnGroup = {
  id: string;
  keys: ExportColumnKey[];
};

export const EXPORT_COLUMN_LABELS: Record<ExportColumnKey, string> = {
  tender_id: "Id",
  title: "Название",
  customer_name: "Заказчик",
  customer_inn: "ИНН",
  location: "Регион",
  status: "Статус",
  url: "Ссылка",
  source_platform_id: "Площадка",
  price_rub: "НМЦ, ₽",
  deadline_msk: "Срок подачи",
  published_msk: "Опубликовано",
  ingested_at: "Попало к нам",
  deadline_expired: "Срок истёк",
  score: "Балл",
  fit_reason: "Почему подходит",
  rules_tier: "Тир по правилам",
  ai_tier: "Тир ИИ",
  manual_tier: "Тир вручную",
  effective_tier: "Итоговый тир",
  ai_reviewed: "Разобрано ИИ",
  ai_trigger: "Источник ИИ",
  ai_reason_ru: "Почему ИИ",
  ai_error: "Ошибка ИИ",
  ai_wrong: "ИИ ошибся",
  ai_wrong_note: "Заметка об ошибке ИИ",
  viewed: "Просмотрено",
  board_hidden: "Скрыт с доски",
  bitrix_sent_at: "В Битрикс",
  contact_name: "Контакт",
  contact_phone: "Телефон",
  contact_email: "Email",
  documents_count: "Число файлов",
};

export const EXPORT_COLUMN_GROUPS: ExportColumnGroup[] = [
  {
    id: "identity",
    keys: [
      "tender_id",
      "title",
      "customer_name",
      "customer_inn",
      "location",
      "status",
      "url",
      "source_platform_id",
    ],
  },
  {
    id: "money",
    keys: ["price_rub", "deadline_msk", "published_msk", "ingested_at", "deadline_expired"],
  },
  {
    id: "score",
    keys: ["score", "fit_reason"],
  },
  {
    id: "tiers",
    keys: ["rules_tier", "ai_tier", "manual_tier", "effective_tier"],
  },
  {
    id: "ai",
    keys: ["ai_reviewed", "ai_trigger", "ai_reason_ru", "ai_error", "ai_wrong", "ai_wrong_note"],
  },
  {
    id: "state",
    keys: ["viewed", "board_hidden", "bitrix_sent_at"],
  },
  {
    id: "contacts",
    keys: ["contact_name", "contact_phone", "contact_email"],
  },
  {
    id: "docs",
    keys: ["documents_count"],
  },
];

export const ALL_EXPORT_COLUMNS: ExportColumnKey[] = EXPORT_COLUMN_GROUPS.flatMap((g) => g.keys);

/** Default preset «Разбор ИИ». */
export const AI_REVIEW_EXPORT_PRESET: ExportColumnKey[] = [
  "tender_id",
  "title",
  "customer_name",
  "rules_tier",
  "ai_tier",
  "manual_tier",
  "effective_tier",
  "ai_reason_ru",
  "ai_error",
  "ai_wrong",
  "ai_wrong_note",
  "ai_trigger",
  "score",
  "fit_reason",
  "url",
  "source_platform_id",
];
