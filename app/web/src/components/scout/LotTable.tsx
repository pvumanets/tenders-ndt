import {
  Chip,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import type { InboxLot } from "../../types";
import { copy } from "../../copy";
import { effectiveTier, formatDate, formatPrice, tierLabel } from "../../lib/format";
import { stripe } from "../../theme/palette";
import PlatformIcon from "./PlatformIcon";

export default function LotTable({
  lots,
  selectedId,
  onOpen,
}: {
  lots: InboxLot[];
  selectedId: string | null;
  onOpen: (id: string) => void;
}) {
  return (
    <Paper
      elevation={0}
      sx={{ border: `1px solid ${stripe.border}`, borderRadius: 1, overflow: "auto" }}
    >
      <Table size="small" sx={{ minWidth: 720 }}>
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell>{copy.col_platform}</TableCell>
            <TableCell>{copy.col_priority}</TableCell>
            <TableCell>{copy.col_title}</TableCell>
            <TableCell>{copy.col_customer}</TableCell>
            <TableCell>{copy.col_location}</TableCell>
            <TableCell>{copy.col_deadline}</TableCell>
            <TableCell>{copy.col_price}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {lots.map((lot) => {
            const tier = effectiveTier(lot);
            const selected = selectedId === lot.tender_id;
            return (
              <TableRow
                key={lot.tender_id}
                hover
                selected={selected}
                onClick={() => onOpen(lot.tender_id)}
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
                  <PlatformIcon platformId={lot.source_platform_id} size={16} />
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
                    <Chip size="small" label={tierLabel(tier)} />
                    {lot.manual_tier != null ? (
                      <Typography variant="caption" color="text.secondary">
                        {copy.chip_overridden_suffix}
                      </Typography>
                    ) : null}
                  </Stack>
                </TableCell>
                <TableCell>
                  <Typography
                    noWrap
                    sx={{ maxWidth: 320, fontWeight: 500, color: stripe.navy }}
                    title={lot.title}
                  >
                    {lot.title}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    noWrap
                    sx={{
                      maxWidth: 240,
                      color: lot.customer_name ? stripe.navy : stripe.textMuted,
                    }}
                    title={lot.customer_name || undefined}
                  >
                    {lot.customer_name || copy.field_empty}
                  </Typography>
                </TableCell>
                <TableCell>{lot.location || copy.field_empty}</TableCell>
                <TableCell>{formatDate(lot.deadline_msk)}</TableCell>
                <TableCell>{formatPrice(lot.price_rub)}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Paper>
  );
}
