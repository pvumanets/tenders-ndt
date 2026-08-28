import { Box } from "@mui/material";
import type { InboxLot, SalesTier } from "../../types";
import { copy } from "../../copy";
import BoardColumn from "../../vendor/personal/dispatch/BoardColumn";
import LotMiniCard from "./LotMiniCard";

const LIVE_COLUMNS: { tier: SalesTier; title: string }[] = [
  { tier: "L1", title: copy.chip_hot },
  { tier: "L2", title: copy.chip_strong },
  { tier: "L3", title: copy.chip_watch },
];

export default function LotBoard({
  lots,
  selectedId,
  onOpen,
  boardTier,
  showTierMove = false,
  showAiHint = false,
}: {
  lots: InboxLot[];
  selectedId: string | null;
  onOpen: (id: string) => void;
  boardTier: (lot: InboxLot) => SalesTier;
  showTierMove?: boolean;
  showAiHint?: boolean;
}) {
  const visible = lots.filter((l) => !l.board_hidden);
  const live = visible.filter((l) => !l.deadline_expired);
  const expired = visible
    .filter((l) => l.deadline_expired)
    .slice()
    .sort((a, b) => b.deadline_msk.localeCompare(a.deadline_msk) || a.tender_id.localeCompare(b.tender_id));

  return (
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
          >
            {items.map((lot) => (
              <LotMiniCard
                key={lot.tender_id}
                lot={lot}
                selected={selectedId === lot.tender_id}
                onOpen={onOpen}
                showTierMove={showTierMove}
                showAiHint={showAiHint}
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
      >
        {expired.map((lot) => (
          <LotMiniCard
            key={lot.tender_id}
            lot={lot}
            selected={selectedId === lot.tender_id}
            onOpen={onOpen}
            showTierMove={showTierMove}
            showAiHint={showAiHint}
          />
        ))}
      </BoardColumn>
    </Box>
  );
}
