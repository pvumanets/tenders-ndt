/** Канон slug/label: docs/discovery/platforms.md */

export type PlatformId =
  | "b2b-center"
  | "rostender"
  | "onlinecontract"
  | "rts-rosatom"
  | "sibur-srm"
  | "tender-pro"
  | "tektorg-kim"
  | "astgoz"
  | "roseltorg"
  | "oilb2bcs"
  | "gpb-etp"
  | "tmk"
  | "severstal";

export type PlatformMeta = {
  id: PlatformId;
  label_ru: string;
  logo: string;
  initials: string;
};

export const PLATFORMS: Record<PlatformId, PlatformMeta> = {
  "b2b-center": {
    id: "b2b-center",
    label_ru: "B2B-Center",
    logo: "/platforms/b2b-center.png",
    initials: "B2B",
  },
  rostender: {
    id: "rostender",
    label_ru: "РосТендер",
    logo: "/platforms/rostender.png",
    initials: "РТ",
  },
  onlinecontract: {
    id: "onlinecontract",
    label_ru: "OnlineContract",
    logo: "/platforms/onlinecontract.png",
    initials: "OC",
  },
  "rts-rosatom": {
    id: "rts-rosatom",
    label_ru: "РТС (Росатом)",
    logo: "/platforms/rts-rosatom.png",
    initials: "РТС",
  },
  "sibur-srm": {
    id: "sibur-srm",
    label_ru: "СИБУР SRM",
    logo: "/platforms/sibur-srm.png",
    initials: "СИБ",
  },
  "tender-pro": {
    id: "tender-pro",
    label_ru: "Tender.Pro",
    logo: "/platforms/tender-pro.png",
    initials: "TP",
  },
  "tektorg-kim": {
    id: "tektorg-kim",
    label_ru: "ТЭК-Торг КИМ",
    logo: "/platforms/tektorg-kim.png",
    initials: "ТЭК",
  },
  astgoz: {
    id: "astgoz",
    label_ru: "АСТ ГОЗ",
    logo: "/platforms/astgoz.png",
    initials: "АСТ",
  },
  roseltorg: {
    id: "roseltorg",
    label_ru: "Росэлторг",
    logo: "/platforms/roseltorg.png",
    initials: "РЭ",
  },
  oilb2bcs: {
    id: "oilb2bcs",
    label_ru: "OilB2B",
    logo: "/platforms/oilb2bcs.png",
    initials: "OIL",
  },
  "gpb-etp": {
    id: "gpb-etp",
    label_ru: "ЭТП ГПБ",
    logo: "/platforms/gpb-etp.png",
    initials: "ГПБ",
  },
  tmk: {
    id: "tmk",
    label_ru: "ТМК закупки",
    logo: "/platforms/tmk.png",
    initials: "ТМК",
  },
  severstal: {
    id: "severstal",
    label_ru: "Северсталь",
    logo: "/platforms/severstal.png",
    initials: "СЕВ",
  },
};

export function getPlatform(id: string | undefined | null): PlatformMeta {
  if (id && id in PLATFORMS) return PLATFORMS[id as PlatformId];
  return PLATFORMS.rostender;
}
