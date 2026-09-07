import {
  Chip,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableSortLabel,
  Typography,
} from "@mui/material";
import type { InboxLot, InboxSort, SalesTier } from "../../types";
import { copy } from "../../copy";
import { formatDate, formatPrice, formatTierMove, rulesBoardTier, tierLabel, tierMoved } from "../../lib/format";
import { stripe } from "../../theme/palette";
import PlatformIcon from "./PlatformIcon";

function SortHeader({
  label,
  mode,
  active,
  onSort,
}: {
  label: string;
  mode: InboxSort;
  active: InboxSort;
  onSort?: (v: InboxSort) => void;
}) {
  if (!onSort) {
    return <>{label}</>;
  }
  const selected = active === mode;
  const direction = mode === "deadline" ? "asc" : "desc";
  return (
    <TableSortLabel
      active={selected}
      direction={direction}
      hideSortIcon={!selected}
      onClick={(e) => {
        e.stopPropagation();
        onSort(mode);
      }}
    >
      {label}
    </TableSortLabel>
  );
}

export default function LotTable({
  lots,
  selectedId,
  onOpen,
  boardTier,
  showTierMove = false,
  sort = "relevance",
  onSort,
}: {
  lots: InboxLot[];
  selectedId: string | null;
  onOpen: (id: string) => void;
  boardTier: (lot: InboxLot) => SalesTier;
  showTierMove?: boolean;
  sort?: InboxSort;
  onSort?: (v: InboxSort) => void;
}) {
  return (
    <Paper
      elevation={0}
      sx={{ border: `1px solid ${stripe.border}`, borderRadius: 1, overflow: "auto" }}
    >
      <Table size="small" sx={{ minWidth: 820 }}>
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell>{copy.col_platform}</TableCell>
            <TableCell aria-sort={sort === "relevance" ? "descending" : undefined}>
              <SortHeader
                label={copy.col_priority}
                mode="relevance"
                active={sort}
                onSort={onSort}
              />
            </TableCell>
            <TableCell>{copy.col_title}</TableCell>
            <TableCell>{copy.col_customer}</TableCell>
            <TableCell>{copy.col_location}</TableCell>
            <TableCell aria-sort={sort === "deadline" ? "ascending" : undefined}>
              <SortHeader label={copy.col_deadline} mode="deadline" active={sort} onSort={onSort} />
            </TableCell>
            <TableCell>{copy.col_published}</TableCell>
            <TableCell aria-sort={sort === "appeared" ? "descending" : undefined}>
              <SortHeader
                label={copy.col_ingested}
                mode="appeared"
                active={sort}
                onSort={onSort}
              />
            </TableCell>
            <TableCell>{copy.col_price}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {lots.map((lot) => {
            const tier = boardTier(lot);
            const selected = selectedId === lot.tender_id;
            const rules = rulesBoardTier(lot);
            const moved =
              showTierMove && tierMoved(lot) && lot.ai_tier
                ? formatTierMove(rules, lot.ai_tier)
                : null;
            return (
              <TableRow
                key={lot.tender_id}
                hover
                selected={selected}
                tabIndex={0}
                role="button"
                aria-label={lot.title}
                onClick={() => onOpen(lot.tender_id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onOpen(lot.tender_id);
                  }
                }}
                sx={{ cursor: "pointer" }}
              >
                <TableCell sx={{ width: 24 }}>
                  {!lot.viewed ? (
                    <Typography component="span" sx={{ color: stripe.blurple, fontSize: 18, lineHeight: 1 }}>
                      •
                    </Typography>
                  ) : null}
                </TableCell>
                <TableCell sx={{ width: 40 }}>
                  <PlatformIcon platformId={lot.source_platform_id} size={18} />
                </TableCell>
                <TableCell>
                  <Stack
                    direction="row"
                    spacing={0.5}
                    useFlexGap
                    sx={{ alignItems: "center", flexWrap: "wrap" }}
                  >
                    <Chip size="small" label={tierLabel(tier)} variant="outlined" />
                    {moved ? <Chip size="small" label={moved} variant="outlined" color="primary" /> : null}
                    {lot.deadline_expired ? (
                      <Chip size="small" label={copy.badge_deadline_expired} variant="outlined" />
                    ) : null}
                  </Stack>
                </TableCell>
                <TableCell>{lot.title}</TableCell>
                <TableCell>{lot.customer_name || copy.field_empty}</TableCell>
                <TableCell>{lot.location || copy.field_empty}</TableCell>
                <TableCell>{formatDate(lot.deadline_msk)}</TableCell>
                <TableCell>{formatDate(lot.published_msk) || copy.field_empty}</TableCell>
                <TableCell>{formatDate(lot.ingested_at)}</TableCell>
                <TableCell>{formatPrice(lot.price_rub)}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Paper>
  );
}
