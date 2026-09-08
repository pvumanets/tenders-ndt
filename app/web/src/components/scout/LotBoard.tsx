import { useMemo, useState } from "react";
import { Box } from "@mui/material";
import type { InboxLot, InboxSort, SalesTier, TeachBucket } from "../../types";
import { copy } from "../../copy";
import BoardColumn from "../../vendor/personal/dispatch/BoardColumn";
import LotMiniCard from "./LotMiniCard";
import TierTeachDialog, { type TierTeachPending } from "./TierTeachDialog";

const LIVE_COLUMNS: { tier: SalesTier; title: string }[] = [
  { tier: "L1", title: copy.chip_hot },
  { tier: "L2", title: copy.chip_strong },
  { tier: "L3", title: copy.chip_watch },
];

export function boardBucket(lot: InboxLot, boardTier: (lot: InboxLot) => SalesTier): TeachBucket {
  if (lot.deadline_expired) return "expired";
  return boardTier(lot);
}

function applyOptimistic(lot: InboxLot, pending: TierTeachPending): InboxLot {
  if (lot.tender_id !== pending.tender_id) return lot;
  if (pending.to_bucket === "expired") {
    return { ...lot, deadline_expired: true };
  }
  return {
    ...lot,
    deadline_expired: false,
    manual_tier: pending.to_bucket,
    effective_tier: pending.to_bucket,
  };
}

export default function LotBoard({
  lots,
  selectedId,
  onOpen,
  boardTier,
  showTierMove = false,
  showAiHint = false,
  sort = "relevance",
  onTeachSubmit,
}: {
  lots: InboxLot[];
  selectedId: string | null;
  onOpen: (id: string) => void;
  boardTier: (lot: InboxLot) => SalesTier;
  showTierMove?: boolean;
  showAiHint?: boolean;
  sort?: InboxSort;
  onTeachSubmit?: (args: {
    tender_id: string;
    from_bucket: TeachBucket;
    to_bucket: TeachBucket;
    drop_tier_correct: boolean;
    reason_ru: string;
  }) => Promise<void>;
}) {
  const [pending, setPending] = useState<TierTeachPending | null>(null);
  const [teachBusy, setTeachBusy] = useState(false);

  const displayLots = useMemo(
    () => (pending ? lots.map((l) => applyOptimistic(l, pending)) : lots),
    [lots, pending],
  );

  const visible = displayLots.filter((l) => !l.board_hidden);
  const live = visible.filter((l) => !l.deadline_expired);
  const expiredRaw = visible.filter((l) => l.deadline_expired);
  const expired =
    sort === "appeared"
      ? expiredRaw
      : expiredRaw
          .slice()
          .sort(
            (a, b) =>
              b.deadline_msk.localeCompare(a.deadline_msk) || a.tender_id.localeCompare(b.tender_id),
          );

  const teachEnabled = Boolean(onTeachSubmit);

  function onDropLot(tenderId: string, to: TeachBucket) {
    if (pending || !onTeachSubmit) return;
    const lot = lots.find((l) => l.tender_id === tenderId);
    if (!lot) return;
    const from = boardBucket(lot, boardTier);
    if (from === to) return;
    setPending({ tender_id: tenderId, from_bucket: from, to_bucket: to });
  }

  function onTeachCancel() {
    if (teachBusy) return;
    setPending(null);
  }

  async function onTeachConfirm(payload: { drop_tier_correct: boolean; reason_ru: string }) {
    if (!pending || !onTeachSubmit) return;
    setTeachBusy(true);
    try {
      await onTeachSubmit({
        tender_id: pending.tender_id,
        from_bucket: pending.from_bucket,
        to_bucket: pending.to_bucket,
        drop_tier_correct: payload.drop_tier_correct,
        reason_ru: payload.reason_ru,
      });
      setPending(null);
    } finally {
      setTeachBusy(false);
    }
  }

  return (
    <>
      <Box
        sx={{
          display: "flex",
          flexDirection: { xs: "column", md: "row" },
          gap: 1.25,
          alignItems: "stretch",
          overflowX: { xs: "hidden", md: "auto" },
          flex: 1,
          minHeight: { xs: 0, md: 420 },
          pb: 1,
          minWidth: 0,
        }}
      >
        {LIVE_COLUMNS.map((col) => {
          const items = live.filter((l) => boardTier(l) === col.tier);
          return (
            <BoardColumn
              key={col.tier}
              city={col.title}
              headerVariant="specialTask"
              peopleCount={items.length}
              countLabel={`${items.length}`}
              emptyMessage={copy.empty_board_column}
              fluid
              dropBucket={teachEnabled ? col.tier : undefined}
              onDropLot={teachEnabled ? onDropLot : undefined}
            >
              {items.map((lot) => (
                <LotMiniCard
                  key={lot.tender_id}
                  lot={lot}
                  selected={selectedId === lot.tender_id}
                  onOpen={onOpen}
                  showTierMove={showTierMove}
                  showAiHint={showAiHint}
                  draggable={teachEnabled}
                />
              ))}
            </BoardColumn>
          );
        })}
        <BoardColumn
          key="expired"
          city={copy.chip_expired}
          headerVariant="specialTask"
          peopleCount={expired.length}
          countLabel={`${expired.length}`}
          emptyMessage={copy.empty_board_column}
          fluid
          dropBucket={teachEnabled ? "expired" : undefined}
          onDropLot={teachEnabled ? onDropLot : undefined}
        >
          {expired.map((lot) => (
            <LotMiniCard
              key={lot.tender_id}
              lot={lot}
              selected={selectedId === lot.tender_id}
              onOpen={onOpen}
              showTierMove={showTierMove}
              showAiHint={showAiHint}
              draggable={teachEnabled}
            />
          ))}
        </BoardColumn>
      </Box>
      {teachEnabled ? (
        <TierTeachDialog
          key={pending ? `${pending.tender_id}-${pending.to_bucket}` : "closed"}
          pending={pending}
          busy={teachBusy}
          onCancel={onTeachCancel}
          onSubmit={(p) => void onTeachConfirm(p)}
        />
      ) : null}
    </>
  );
}
