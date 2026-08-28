import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Divider,
  FormControlLabel,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import type { InboxLot, SalesTier } from "../../types";
import { copy } from "../../copy";
import { aiBoardTier, formatDate, formatPrice, rulesBoardTier, tierLabel, tierMoved } from "../../lib/format";
import { personProfileTokens } from "../../theme/person-profile";
import { stripe } from "../../theme/palette";
import DetailDrawerShell from "../../vendor/personal/people/DetailDrawerShell";
import FieldRow from "../../vendor/personal/people/FieldRow";
import FileTypeIcon from "./FileTypeIcon";
import PlatformIcon from "./PlatformIcon";
import { documentDownloadUrl } from "../../lib/inbox";

export default function TenderDrawer({
  lot,
  onClose,
  onToggleViewed,
  onSetPriority,
  onSetBoardHidden,
  onAiWrong,
  drawerMode = "rules",
}: {
  lot: InboxLot;
  onClose: () => void;
  onToggleViewed: (id: string) => void;
  onSetPriority: (id: string, tier: SalesTier | null) => void;
  onSetBoardHidden: (id: string, hidden: boolean) => void;
  onAiWrong?: (id: string) => void;
  drawerMode?: "rules" | "ai";
}) {
  const [menuEl, setMenuEl] = useState<null | HTMLElement>(null);
  const tier = drawerMode === "ai" ? aiBoardTier(lot) : rulesBoardTier(lot);
  const rulesTier = lot.rules_tier ?? lot.tier;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const contactBits = [lot.contact_name, lot.contact_phone, lot.contact_email]
    .filter(Boolean)
    .join(" · ");

  return (
    <DetailDrawerShell open onClose={onClose}>
      <Box sx={{ p: 2.5, borderBottom: `1px solid ${stripe.border}` }}>
        <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "flex-start" }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="caption" color="text.secondary">
              {tierLabel(tier)}
              {lot.manual_tier != null ? ` · ${copy.chip_overridden_suffix}` : ""}
              {lot.deadline_expired ? ` · ${copy.badge_deadline_expired}` : ""}
            </Typography>
            {drawerMode === "rules" && lot.ai_reviewed && lot.ai_tier && tierMoved(lot) ? (
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.25 }}>
                {copy.drawer_ai_suggested
                  .replace("{ai}", tierLabel(lot.ai_tier))
                  .replace("{rules}", tierLabel(rulesTier))}
              </Typography>
            ) : null}
            {drawerMode === "ai" && lot.ai_reviewed ? (
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.25 }}>
                {copy.drawer_rules_was.replace("{tier}", tierLabel(rulesTier))}
              </Typography>
            ) : null}
            <Typography component="h2" sx={{ ...personProfileTokens.sectionTitle, mt: 0.5 }}>
              {lot.title}
            </Typography>
            <Typography sx={{ mt: 1, fontWeight: 600, color: stripe.navy }}>
              {lot.customer_name || copy.field_empty}
            </Typography>
            <Stack
              direction="row"
              spacing={0.75}
              sx={{ alignItems: "center", mt: 0.75 }}
            >
              <PlatformIcon platformId={lot.source_platform_id} size={16} />
              <Link
                href={lot.url}
                target="_blank"
                rel="noreferrer"
                underline="hover"
                sx={{ fontSize: 13 }}
              >
                {copy.link_on_site}
              </Link>
            </Stack>
          </Box>
          <IconButton size="small" aria-label={copy.drawer_close_aria} onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      </Box>

      <Box sx={{ flex: 1, overflow: "auto", p: 2.5 }}>
        <FieldRow label={copy.field_price}>
          <Typography>{formatPrice(lot.price_rub)}</Typography>
        </FieldRow>
        <FieldRow label={copy.field_deadline}>
          <Typography>
            {formatDate(lot.deadline_msk)}
            {lot.deadline_expired ? ` · ${copy.badge_deadline_expired}` : ""}
          </Typography>
        </FieldRow>
        <FieldRow label={copy.field_region}>
          <Typography>{lot.location || copy.field_empty}</Typography>
        </FieldRow>
        <FieldRow label={copy.field_status}>
          <Typography>{lot.status || copy.field_empty}</Typography>
        </FieldRow>

        <Typography sx={{ ...personProfileTokens.fieldLabel, mt: 1, mb: 0.5 }}>
          {copy.section_fit}
        </Typography>
        <Typography sx={{ mb: 2 }}>{lot.fit_reason || copy.field_empty}</Typography>
        {lot.ai_reason_ru ? (
          <>
            <Typography sx={{ ...personProfileTokens.fieldLabel, mb: 0.5 }}>
              {copy.section_ai_reason}
            </Typography>
            <Typography sx={{ mb: 2 }}>{lot.ai_reason_ru}</Typography>
          </>
        ) : null}
        {lot.ai_error ? (
          <Typography sx={{ mb: 2 }} color="error">
            {copy.ai_error_label}: {lot.ai_error}
          </Typography>
        ) : null}

        <Typography sx={{ ...personProfileTokens.fieldLabel, mb: 0.5 }}>
          {copy.section_contacts}
        </Typography>
        <Typography sx={{ mb: 2 }} color={contactBits ? "text.primary" : "text.secondary"}>
          {contactBits || copy.field_empty}
        </Typography>

        <Typography sx={{ ...personProfileTokens.fieldLabel, mb: 0.5 }}>
          {copy.section_docs}
        </Typography>
        {lot.documents.length === 0 ? (
          <Typography color="text.secondary">{copy.docs_empty_none}</Typography>
        ) : (
          <List dense disablePadding>
            {lot.documents.map((d) => (
              <ListItem
                key={d.name}
                disableGutters
                sx={{ borderBottom: `1px solid ${stripe.border}`, gap: 1 }}
              >
                <ListItemIcon sx={{ minWidth: 22 }}>
                  <FileTypeIcon fileName={d.name} size={18} />
                </ListItemIcon>
                <ListItemText
                  primary={d.name}
                  secondary={d.size_kb != null ? `${d.size_kb} КБ` : undefined}
                />
                <Button
                  size="small"
                  href={documentDownloadUrl(lot.tender_id, d.name)}
                >
                  {copy.docs_download}
                </Button>
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      <Divider />
      <Stack
        direction="row"
        spacing={1.5}
        useFlexGap
        sx={{ p: 2.5, flexWrap: "wrap", alignItems: "center" }}
      >
        <FormControlLabel
          control={
            <Switch
              checked={lot.viewed}
              onChange={() => onToggleViewed(lot.tender_id)}
              slotProps={{ input: { "aria-label": copy.action_viewed_done } }}
            />
          }
          label={copy.action_viewed_done}
        />
        <Button size="small" variant="outlined" onClick={(e) => setMenuEl(e.currentTarget)}>
          {copy.action_change_priority}
        </Button>
        <Button
          size="small"
          variant="outlined"
          onClick={() => onSetBoardHidden(lot.tender_id, !lot.board_hidden)}
        >
          {lot.board_hidden ? copy.action_restore_board : copy.action_archive}
        </Button>
        {lot.ai_reviewed && onAiWrong ? (
          <Button
            size="small"
            variant="outlined"
            color="warning"
            disabled={lot.ai_wrong}
            onClick={() => onAiWrong(lot.tender_id)}
          >
            {copy.action_ai_wrong}
          </Button>
        ) : null}
        <Menu anchorEl={menuEl} open={Boolean(menuEl)} onClose={() => setMenuEl(null)}>
          <MenuItem
            onClick={() => {
              onSetPriority(lot.tender_id, "L1");
              setMenuEl(null);
            }}
          >
            {copy.chip_hot}
          </MenuItem>
          <MenuItem
            onClick={() => {
              onSetPriority(lot.tender_id, "L2");
              setMenuEl(null);
            }}
          >
            {copy.chip_strong}
          </MenuItem>
          <MenuItem
            onClick={() => {
              onSetPriority(lot.tender_id, "L3");
              setMenuEl(null);
            }}
          >
            {copy.chip_watch}
          </MenuItem>
          <MenuItem
            onClick={() => {
              onSetPriority(lot.tender_id, null);
              setMenuEl(null);
            }}
          >
            {copy.action_reset_priority}
          </MenuItem>
        </Menu>
      </Stack>
    </DetailDrawerShell>
  );
}
