import { Box } from "@mui/material";
import type { InboxLot, SalesTier } from "../../types";
import { copy } from "../../copy";
import { effectiveTier } from "../../lib/format";
import BoardColumn from "../../vendor/personal/dispatch/BoardColumn";
import LotMiniCard from "./LotMiniCard";

const COLUMNS: { tier: SalesTier; title: string }[] = [
  { tier: "L1", title: copy.chip_hot },
  { tier: "L2", title: copy.chip_strong },
  { tier: "L3", title: copy.chip_watch },
];

export default function LotBoard({
  lots,
  selectedId,
  onOpen,
}: {
  lots: InboxLot[];
  selectedId: string | null;
  onOpen: (id: string) => void;
}) {
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
      }}
    >
      {COLUMNS.map((col) => {
        const items = lots.filter((l) => effectiveTier(l) === col.tier);
        return (
          <BoardColumn
            key={col.tier}
            city={col.title}
            headerVariant="specialTask"
            peopleCount={items.length}
            countLabel={`${items.length}`}
            emptyMessage="Нет лотов"
            fluid
          >
            {items.map((lot) => (
              <LotMiniCard
                key={lot.tender_id}
                lot={lot}
                selected={selectedId === lot.tender_id}
                onOpen={onOpen}
              />
            ))}
          </BoardColumn>
        );
      })}
    </Box>
  );
}
