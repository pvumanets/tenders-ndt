import type { MouseEvent } from "react";
import { Box, Chip, Paper, Stack, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import type { InboxLot } from "../../types";
import { copy } from "../../copy";
import { formatDate, formatPrice, formatTierMove, rulesBoardTier, tierMoved } from "../../lib/format";
import { stripe } from "../../theme/palette";
import { stripeShadows } from "../../theme/shadows";
import CardTextButton from "../../vendor/personal/dispatch/CardTextButton";
import PlatformIcon from "./PlatformIcon";

/** Reserved right column so PlatformIcon stays put across cards. */
const PLATFORM_RAIL_PX = 24;

/** Lot card — visual structure from personal PersonMiniCard, tender fields. */
export default function LotMiniCard({
  lot,
  selected,
  onOpen,
  showTierMove = false,
  showAiHint = false,
}: {
  lot: InboxLot;
  selected?: boolean;
  onOpen: (id: string) => void;
  showTierMove?: boolean;
  showAiHint?: boolean;
}) {
  const theme = useTheme();
  const pmc = theme.density.personMiniCard;
  const hasManual = lot.manual_tier != null;
  const rules = rulesBoardTier(lot);
  const moveLabel =
    showTierMove && tierMoved(lot) && lot.ai_tier ? formatTierMove(rules, lot.ai_tier) : null;
  const aiHint =
    showAiHint && tierMoved(lot) && lot.ai_tier
      ? copy.chip_ai_tier_hint.replace("{tier}", lot.ai_tier)
      : null;

  return (
    <Paper
      elevation={0}
      onClick={() => onOpen(lot.tender_id)}
      sx={{
        p: 1.25,
        width: "100%",
        minWidth: 0,
        border: `1px solid ${selected ? stripe.blurple : stripe.border}`,
        borderRadius: `${theme.density.radius.sm}px`,
        bgcolor: stripe.surface,
        cursor: "pointer",
        boxShadow: "none",
        boxSizing: "border-box",
        borderLeft: lot.viewed ? undefined : `3px solid ${stripe.blurple}`,
        "&:hover": {
          borderColor: selected ? stripe.blurple : stripe.borderHover,
          boxShadow: stripeShadows.sm,
        },
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "stretch",
          gap: 1,
          minWidth: 0,
        }}
      >
        <Stack spacing={0} sx={{ flex: 1, minWidth: 0 }}>
          {hasManual ? (
            <Chip
              size="small"
              label={copy.chip_overridden_suffix}
              variant="outlined"
              sx={{
                alignSelf: "flex-start",
                height: theme.density.chip.height,
                fontSize: `${theme.density.chip.fontSize}px`,
                borderColor: stripe.border,
                color: stripe.textMuted,
              }}
            />
          ) : null}
          {moveLabel ? (
            <Chip
              size="small"
              label={moveLabel}
              variant="outlined"
              sx={{
                alignSelf: "flex-start",
                mt: hasManual ? 0.5 : 0,
                height: theme.density.chip.height,
                fontSize: `${theme.density.chip.fontSize}px`,
                borderColor: stripe.blurple,
                color: stripe.blurple,
              }}
            />
          ) : null}
          {aiHint ? (
            <Chip
              size="small"
              label={aiHint}
              variant="outlined"
              sx={{
                alignSelf: "flex-start",
                mt: hasManual || moveLabel ? 0.5 : 0,
                height: theme.density.chip.height,
                fontSize: `${theme.density.chip.fontSize}px`,
                borderColor: stripe.border,
                color: stripe.textMuted,
              }}
            />
          ) : null}
          {lot.deadline_expired ? (
            <Chip
              size="small"
              label={copy.badge_deadline_expired}
              variant="outlined"
              sx={{
                alignSelf: "flex-start",
                mt: hasManual ? 0.5 : 0,
                height: theme.density.chip.height,
                fontSize: `${theme.density.chip.fontSize}px`,
                borderColor: stripe.border,
                color: stripe.textMuted,
              }}
            />
          ) : null}

          <Box sx={{ mt: hasManual || moveLabel || aiHint || lot.deadline_expired ? `${pmc.headerToBody}px` : 0 }}>
            <Typography
              sx={{
                fontSize: `${theme.density.font.md}px`,
                fontWeight: theme.density.weight.medium,
                color: stripe.navy,
                lineHeight: 1.35,
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {lot.title}
            </Typography>
            {lot.customer_name ? (
              <Typography
                sx={{
                  mt: 0.5,
                  fontSize: `${theme.density.font.sm}px`,
                  fontWeight: theme.density.weight.medium,
                  color: stripe.navy,
                  display: "-webkit-box",
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                }}
              >
                {lot.customer_name}
              </Typography>
            ) : null}
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mt: 0.75 }}
            >
              {copy.card_location}
            </Typography>
            <Typography
              sx={{
                fontSize: `${theme.density.font.sm}px`,
                fontWeight: theme.density.weight.medium,
                color: lot.location ? stripe.navy : stripe.textMuted,
                fontStyle: lot.location ? "normal" : "italic",
              }}
            >
              {lot.location || copy.field_empty}
            </Typography>
          </Box>

          <Box sx={{ mt: `${pmc.factToIntent}px` }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
              {copy.col_deadline}
            </Typography>
            <Typography sx={{ fontSize: `${theme.density.font.sm}px`, color: stripe.text }}>
              {formatDate(lot.deadline_msk)}
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mt: 0.75 }}
            >
              {copy.col_price}
            </Typography>
            <Typography sx={{ fontSize: `${theme.density.font.sm}px`, color: stripe.text }}>
              {formatPrice(lot.price_rub)}
            </Typography>
          </Box>

          <Box sx={{ mt: `${pmc.toAction}px` }}>
            <CardTextButton
              emphasis="primary"
              onClick={(e: MouseEvent) => {
                e.stopPropagation();
                onOpen(lot.tender_id);
              }}
            >
              Открыть
            </CardTextButton>
          </Box>
        </Stack>

        <Box
          sx={{
            width: PLATFORM_RAIL_PX,
            flexShrink: 0,
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "flex-start",
          }}
        >
          <PlatformIcon platformId={lot.source_platform_id} size={18} />
        </Box>
      </Box>
    </Paper>
  );
}
