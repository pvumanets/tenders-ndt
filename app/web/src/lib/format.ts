import type { InboxLot, SalesTier } from "../types";
import { copy } from "../copy";

export function rulesBoardTier(lot: InboxLot): SalesTier {
  if (lot.manual_tier) return lot.manual_tier;
  return lot.rules_tier ?? lot.tier;
}

export function aiBoardTier(lot: InboxLot): SalesTier {
  if (lot.effective_tier === "L1" || lot.effective_tier === "L2" || lot.effective_tier === "L3") {
    return lot.effective_tier;
  }
  if (lot.manual_tier) return lot.manual_tier;
  if (lot.ai_reviewed && lot.ai_tier) return lot.ai_tier;
  return lot.rules_tier ?? lot.tier;
}

/** @deprecated use rulesBoardTier or aiBoardTier */
export function effectiveTier(lot: InboxLot): SalesTier {
  return rulesBoardTier(lot);
}

export function tierMoved(lot: InboxLot): boolean {
  if (!lot.ai_reviewed || !lot.ai_tier) return false;
  const rules = lot.rules_tier ?? lot.tier;
  return lot.ai_tier !== rules;
}

export function formatTierMove(rules: SalesTier, ai: SalesTier): string {
  return `${rules} → ${ai}`;
}

export function tierLabel(tier: SalesTier): string {
  if (tier === "L1") return copy.chip_hot;
  if (tier === "L2") return copy.chip_strong;
  return copy.chip_watch;
}

export function formatPrice(n: number | null): string {
  if (n == null) return copy.field_empty;
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatDate(iso: string): string {
  if (!iso) return copy.field_empty;
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}.${m}.${y}`;
}
