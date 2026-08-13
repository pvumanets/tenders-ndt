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
import { effectiveTier, formatDate, formatPrice, tierLabel } from "../../lib/format";
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
}: {
  lot: InboxLot;
  onClose: () => void;
  onToggleViewed: (id: string) => void;
  onSetPriority: (id: string, tier: SalesTier | null) => void;
}) {
  const [menuEl, setMenuEl] = useState<null | HTMLElement>(null);
  const tier = effectiveTier(lot);

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
            </Typography>
            <Typography component="h2" sx={{ ...personProfileTokens.sectionTitle, mt: 0.5 }}>
              {lot.title}
            </Typography>
            <Typography sx={{ mt: 1, fontWeight: 600, color: stripe.navy }}>
              {lot.customer_name}
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
          <Typography>{formatDate(lot.deadline_msk)}</Typography>
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
        <Typography sx={{ mb: 2 }}>{lot.fit_reason}</Typography>

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
