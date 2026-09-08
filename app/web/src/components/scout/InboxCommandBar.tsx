import { useState, type ReactNode } from "react";
import {
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Link,
  Popover,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import ViewWeekOutlinedIcon from "@mui/icons-material/ViewWeekOutlined";
import TableRowsOutlinedIcon from "@mui/icons-material/TableRowsOutlined";
import type {
  DeadlinePreset,
  IngestedPreset,
  InboxSort,
  PriorityFilter,
  SalesTier,
  ViewMode,
  PlatformRow,
  BitrixFilter,
} from "../../types";
import { copy } from "../../copy";
import { formatPrice } from "../../lib/format";
import { stripe } from "../../theme/palette";
import { viewCommandBarLayout } from "../../vendor/personal/layout/view-command-bar";
import FilterTriggerButton from "../../vendor/personal/shell/FilterTriggerButton";
import ViewCommandBar from "../../vendor/personal/shell/ViewCommandBar";

const MENU_WIDTH = 340;

const PRIORITY_OPTIONS: { id: SalesTier; label: string }[] = [
  { id: "L1", label: copy.filter_priority_hot },
  { id: "L2", label: copy.filter_priority_strong },
  { id: "L3", label: copy.filter_priority_watch },
];

function deadlinePresetLabel(preset: DeadlinePreset): string {
  switch (preset) {
    case "d7":
      return copy.filter_deadline_7;
    case "d14":
      return copy.filter_deadline_14;
    case "d30":
      return copy.filter_deadline_30;
    case "custom":
      return copy.filter_date_custom;
    default:
      return copy.filter_date_any;
  }
}

function ingestedPresetLabel(preset: IngestedPreset): string {
  switch (preset) {
    case "today":
      return copy.filter_ingested_today;
    case "d3":
      return copy.filter_ingested_3;
    case "d7":
      return copy.filter_ingested_7;
    case "custom":
      return copy.filter_date_custom;
    default:
      return copy.filter_date_any_f;
  }
}

function bitrixLabel(filter: BitrixFilter): string {
  if (filter === "in") return copy.filter_bitrix_in;
  if (filter === "out") return copy.filter_bitrix_out;
  return copy.filter_bitrix_any;
}

export type ActiveFilterChip = {
  id: string;
  label: string;
};

/** Grouped-filter axes that contribute to badge + chips (not unread/sort/view). */
export function countActiveGroupedFilters(args: {
  priority: PriorityFilter;
  deadlinePreset: DeadlinePreset;
  ingestedPreset: IngestedPreset;
  priceMinRub: number | null;
  platformsSelected: string[];
  bitrixFilter: BitrixFilter;
  showAiReviewedFilter: boolean;
  aiReviewedOnly: boolean;
}): number {
  let n = 0;
  if (args.priority.length > 0) n += 1;
  if (args.deadlinePreset !== "any") n += 1;
  if (args.ingestedPreset !== "any") n += 1;
  if (args.priceMinRub != null && args.priceMinRub > 0) n += 1;
  if (args.platformsSelected.length > 0) n += 1;
  if (args.bitrixFilter !== "any") n += 1;
  if (args.showAiReviewedFilter && args.aiReviewedOnly) n += 1;
  return n;
}

export function buildActiveFilterChips(args: {
  priority: PriorityFilter;
  deadlinePreset: DeadlinePreset;
  ingestedPreset: IngestedPreset;
  priceMinRub: number | null;
  platformsSelected: string[];
  bitrixFilter: BitrixFilter;
  showAiReviewedFilter: boolean;
  aiReviewedOnly: boolean;
}): ActiveFilterChip[] {
  const chips: ActiveFilterChip[] = [];
  if (args.priority.length > 0) {
    const names = PRIORITY_OPTIONS.filter((o) => args.priority.includes(o.id))
      .map((o) => o.label)
      .join(", ");
    chips.push({
      id: "priority",
      label: copy.filter_chip_priority.replace("{value}", names),
    });
  }
  if (args.deadlinePreset !== "any") {
    chips.push({
      id: "deadline",
      label: copy.filter_chip_deadline.replace("{value}", deadlinePresetLabel(args.deadlinePreset)),
    });
  }
  if (args.ingestedPreset !== "any") {
    chips.push({
      id: "ingested",
      label: copy.filter_chip_ingested.replace("{value}", ingestedPresetLabel(args.ingestedPreset)),
    });
  }
  if (args.priceMinRub != null && args.priceMinRub > 0) {
    chips.push({
      id: "price",
      label: copy.filter_chip_price.replace("{price}", formatPrice(args.priceMinRub)),
    });
  }
  if (args.platformsSelected.length > 0) {
    chips.push({
      id: "platform",
      label: copy.filter_chip_platform.replace("{n}", String(args.platformsSelected.length)),
    });
  }
  if (args.bitrixFilter !== "any") {
    chips.push({
      id: "bitrix",
      label: copy.filter_chip_bitrix.replace("{value}", bitrixLabel(args.bitrixFilter)),
    });
  }
  if (args.showAiReviewedFilter && args.aiReviewedOnly) {
    chips.push({ id: "ai", label: copy.filter_chip_ai });
  }
  return chips;
}

function menuPaperSx() {
  return {
    width: MENU_WIDTH,
    maxWidth: "calc(100vw - 32px)",
    maxHeight: "min(70vh, 560px)",
    overflowY: "auto",
    p: 1.5,
    mt: 0.5,
    border: `1px solid ${stripe.border}`,
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
  };
}

function SectionTitle({ children }: { children: ReactNode }) {
  const theme = useTheme();
  return (
    <Typography
      variant="caption"
      sx={{
        display: "block",
        color: stripe.textMuted,
        fontWeight: theme.density.weight.medium,
        mb: 0.75,
        px: 0.5,
        textTransform: "uppercase",
        letterSpacing: "0.04em",
      }}
    >
      {children}
    </Typography>
  );
}

function FieldTitle({ children }: { children: ReactNode }) {
  return (
    <Typography variant="body2" sx={{ px: 0.5, pt: 0.5, pb: 0.25, color: stripe.navy, fontWeight: 600 }}>
      {children}
    </Typography>
  );
}

function CheckRow({
  checked,
  label,
  onToggle,
}: {
  checked: boolean;
  label: string;
  onToggle: () => void;
}) {
  return (
    <FormControlLabel
      labelPlacement="start"
      control={
        <Checkbox size="small" checked={checked} onChange={onToggle} sx={{ ml: "auto" }} />
      }
      label={
        <Typography variant="body2" sx={{ color: stripe.navy }}>
          {label}
        </Typography>
      }
      sx={{
        mx: 0,
        width: "100%",
        py: 0.75,
        px: 0.5,
        gap: 1,
        justifyContent: "space-between",
      }}
    />
  );
}

function RadioRow({ value, label }: { value: string; label: string }) {
  return (
    <FormControlLabel
      value={value}
      control={<Radio size="small" />}
      label={
        <Typography variant="body2" sx={{ color: stripe.navy }}>
          {label}
        </Typography>
      }
      sx={{ mx: 0, width: "100%", py: 0.5, px: 0.5 }}
    />
  );
}

function DateRangeFields({
  from,
  to,
  onFrom,
  onTo,
}: {
  from: string;
  to: string;
  onFrom: (v: string) => void;
  onTo: (v: string) => void;
}) {
  return (
    <Stack spacing={1} sx={{ pt: 1, px: 0.5 }}>
      <TextField
        type="date"
        size="small"
        fullWidth
        label={copy.filter_date_from}
        value={from}
        onChange={(e) => onFrom(e.target.value)}
        slotProps={{ inputLabel: { shrink: true } }}
      />
      <TextField
        type="date"
        size="small"
        fullWidth
        label={copy.filter_date_to}
        value={to}
        onChange={(e) => onTo(e.target.value)}
        slotProps={{ inputLabel: { shrink: true } }}
      />
    </Stack>
  );
}

export default function InboxCommandBar({
  unreadOnly,
  onUnreadOnly,
  onCountUnreadInTab,
  onMarkAllUnreadInTab,
  priority,
  onPriority,
  search,
  onSearch,
  deadlinePreset,
  onDeadlinePreset,
  deadlineFrom,
  onDeadlineFrom,
  deadlineTo,
  onDeadlineTo,
  ingestedPreset,
  onIngestedPreset,
  ingestedFrom,
  onIngestedFrom,
  ingestedTo,
  onIngestedTo,
  view,
  onView,
  sort = "relevance",
  onSort,
  showAiReviewedFilter = false,
  aiReviewedOnly = false,
  onAiReviewedOnly,
  priceMinRub = null,
  onPriceMinRub,
  settingsMinPrice = 100_000,
  onOpenSettings,
  platforms = [],
  platformsSelected = [],
  onPlatformsSelected,
  bitrixFilter = "any",
  onBitrixFilter,
}: {
  unreadOnly: boolean;
  onUnreadOnly: (v: boolean) => void;
  /** dry_run count of unread on current tab. */
  onCountUnreadInTab?: () => Promise<number>;
  /** Mark all unread on current tab; returns updated count. */
  onMarkAllUnreadInTab?: () => Promise<number>;
  priority: PriorityFilter;
  onPriority: (v: PriorityFilter) => void;
  search: string;
  onSearch: (v: string) => void;
  deadlinePreset: DeadlinePreset;
  onDeadlinePreset: (v: DeadlinePreset) => void;
  deadlineFrom: string;
  onDeadlineFrom: (v: string) => void;
  deadlineTo: string;
  onDeadlineTo: (v: string) => void;
  ingestedPreset: IngestedPreset;
  onIngestedPreset: (v: IngestedPreset) => void;
  ingestedFrom: string;
  onIngestedFrom: (v: string) => void;
  ingestedTo: string;
  onIngestedTo: (v: string) => void;
  view: ViewMode;
  onView: (v: ViewMode) => void;
  sort?: InboxSort;
  onSort?: (v: InboxSort) => void;
  showAiReviewedFilter?: boolean;
  aiReviewedOnly?: boolean;
  onAiReviewedOnly?: (v: boolean) => void;
  priceMinRub?: number | null;
  onPriceMinRub?: (v: number | null) => void;
  settingsMinPrice?: number;
  onOpenSettings?: () => void;
  platforms?: PlatformRow[];
  platformsSelected?: string[];
  onPlatformsSelected?: (v: string[]) => void;
  bitrixFilter?: BitrixFilter;
  onBitrixFilter?: (v: BitrixFilter) => void;
}) {
  const [filtersEl, setFiltersEl] = useState<HTMLElement | null>(null);
  const [markAllOpen, setMarkAllOpen] = useState(false);
  const [markAllCount, setMarkAllCount] = useState<number | null>(null);
  const [markAllBusy, setMarkAllBusy] = useState(false);

  async function openMarkAllDialog() {
    if (!onCountUnreadInTab || markAllBusy) return;
    setMarkAllBusy(true);
    try {
      const n = await onCountUnreadInTab();
      setMarkAllCount(n);
      setMarkAllOpen(true);
    } catch {
      /* toast from App */
    } finally {
      setMarkAllBusy(false);
    }
  }

  async function confirmMarkAll() {
    if (!onMarkAllUnreadInTab || markAllBusy) return;
    setMarkAllBusy(true);
    try {
      await onMarkAllUnreadInTab();
      setMarkAllOpen(false);
      setMarkAllCount(null);
    } catch {
      /* toast from App */
    } finally {
      setMarkAllBusy(false);
    }
  }

  function togglePriority(tier: SalesTier) {
    onPriority(priority.includes(tier) ? priority.filter((t) => t !== tier) : [...priority, tier]);
  }

  function setDeadline(next: DeadlinePreset) {
    onDeadlinePreset(next);
    if (next !== "custom") {
      onDeadlineFrom("");
      onDeadlineTo("");
    }
  }

  function setIngested(next: IngestedPreset) {
    onIngestedPreset(next);
    if (next !== "custom") {
      onIngestedFrom("");
      onIngestedTo("");
    }
  }

  function togglePlatform(platformId: string) {
    if (!onPlatformsSelected) return;
    onPlatformsSelected(
      platformsSelected.includes(platformId)
        ? platformsSelected.filter((id) => id !== platformId)
        : [...platformsSelected, platformId],
    );
  }

  const priceActive = priceMinRub != null && priceMinRub > 0;
  const groupedArgs = {
    priority,
    deadlinePreset,
    ingestedPreset,
    priceMinRub,
    platformsSelected,
    bitrixFilter,
    showAiReviewedFilter,
    aiReviewedOnly,
  };
  const activeCount = countActiveGroupedFilters(groupedArgs);
  const chips = buildActiveFilterChips(groupedArgs);

  function clearChip(id: string) {
    switch (id) {
      case "priority":
        onPriority([]);
        break;
      case "deadline":
        setDeadline("any");
        break;
      case "ingested":
        setIngested("any");
        break;
      case "price":
        onPriceMinRub?.(null);
        break;
      case "platform":
        onPlatformsSelected?.([]);
        break;
      case "bitrix":
        onBitrixFilter?.("any");
        break;
      case "ai":
        onAiReviewedOnly?.(false);
        break;
      default:
        break;
    }
  }

  function clearAllGrouped() {
    onPriority([]);
    setDeadline("any");
    setIngested("any");
    onPriceMinRub?.(null);
    onPlatformsSelected?.([]);
    onBitrixFilter?.("any");
    onAiReviewedOnly?.(false);
  }

  return (
    <Box
      sx={{
        position: "sticky",
        top: 0,
        zIndex: 3,
        mb: viewCommandBarLayout.marginBottom,
        bgcolor: "background.default",
        pt: 0.25,
        pb: 1,
      }}
    >
      <ViewCommandBar
        sx={{
          flexWrap: "wrap",
          gridTemplateColumns: { xs: "1fr", md: "1fr auto" },
          mb: 1,
        }}
      >
        <ViewCommandBar.Start
          sx={{
            display: { xs: "grid", md: "flex" },
            gridTemplateColumns: { xs: "1fr 1fr", md: "none" },
            flexWrap: { md: "nowrap" },
            gap: 1,
            width: "100%",
            "& > *": { minWidth: 0, width: { xs: "100%", md: "auto" } },
            "& .MuiButton-root": { width: { xs: "100%", md: "auto" } },
          }}
        >
          <Button
            variant="outlined"
            size="small"
            onClick={() => onUnreadOnly(!unreadOnly)}
            startIcon={
              <Checkbox
                checked={unreadOnly}
                size="small"
                tabIndex={-1}
                disableRipple
                sx={{ p: 0, pointerEvents: "none", "& .MuiSvgIcon-root": { fontSize: 16 } }}
              />
            }
            sx={{
              flexShrink: 0,
              width: { xs: "100%", md: "auto" },
              bgcolor: unreadOnly ? stripe.blurpleSoft : stripe.surface,
              color: unreadOnly ? stripe.blurple : stripe.text,
            }}
          >
            {copy.filter_unread}
          </Button>
          {onCountUnreadInTab && onMarkAllUnreadInTab ? (
            <Button
              variant="text"
              size="small"
              disabled={markAllBusy}
              onClick={() => void openMarkAllDialog()}
              sx={{ flexShrink: 0, color: stripe.blurple, width: { xs: "100%", md: "auto" } }}
            >
              {copy.action_mark_all_viewed}
            </Button>
          ) : null}
          <FilterTriggerButton
            label={copy.filter_menu}
            badgeContent={activeCount}
            onClick={(e) => setFiltersEl(e.currentTarget)}
          />
        </ViewCommandBar.Start>

        <ViewCommandBar.End
          sx={{ width: { xs: "100%", md: "auto" }, justifyContent: "flex-end", gap: 1, flexWrap: "wrap" }}
        >
          {onSort ? (
            <ToggleButtonGroup
              exclusive
              size="small"
              value={sort}
              aria-label={copy.sort_group_aria}
              onChange={(_, v: InboxSort | null) => {
                if (v) onSort(v);
              }}
            >
              <ToggleButton value="relevance">{copy.sort_relevance}</ToggleButton>
              <ToggleButton value="appeared">{copy.sort_appeared}</ToggleButton>
              <ToggleButton value="deadline">{copy.sort_deadline}</ToggleButton>
            </ToggleButtonGroup>
          ) : null}
          <ToggleButtonGroup
            exclusive
            size="small"
            value={view}
            onChange={(_, v: ViewMode | null) => {
              if (v) onView(v);
            }}
          >
            <ToggleButton value="cards">
              <ViewWeekOutlinedIcon sx={{ mr: 0.5, fontSize: 16 }} />
              {copy.view_cards}
            </ToggleButton>
            <ToggleButton value="table">
              <TableRowsOutlinedIcon sx={{ mr: 0.5, fontSize: 16 }} />
              {copy.view_table}
            </ToggleButton>
          </ToggleButtonGroup>
        </ViewCommandBar.End>
      </ViewCommandBar>

      {chips.length > 0 ? (
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: 0.75,
            mb: 1,
          }}
        >
          {chips.map((chip) => (
            <Chip
              key={chip.id}
              size="small"
              label={chip.label}
              onDelete={() => clearChip(chip.id)}
              sx={{
                borderColor: stripe.border,
                bgcolor: stripe.surface,
                color: stripe.navy,
              }}
              variant="outlined"
            />
          ))}
          <Link
            component="button"
            variant="caption"
            underline="hover"
            onClick={clearAllGrouped}
            sx={{ cursor: "pointer", border: "none", background: "none", ml: 0.5 }}
          >
            {copy.filter_chips_clear_all}
          </Link>
        </Box>
      ) : null}

      <Popover
        open={Boolean(filtersEl)}
        anchorEl={filtersEl}
        onClose={() => setFiltersEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
        transformOrigin={{ vertical: "top", horizontal: "left" }}
        slotProps={{ paper: { sx: menuPaperSx() } }}
      >
        <Stack spacing={1.5}>
          <Box>
            <SectionTitle>{copy.filter_section_dates}</SectionTitle>
            <FieldTitle>{copy.filter_deadline}</FieldTitle>
            <RadioGroup
              value={deadlinePreset}
              onChange={(_, v) => setDeadline(v as DeadlinePreset)}
            >
              <RadioRow value="any" label={copy.filter_date_any} />
              <RadioRow value="d7" label={copy.filter_deadline_7} />
              <RadioRow value="d14" label={copy.filter_deadline_14} />
              <RadioRow value="d30" label={copy.filter_deadline_30} />
              <RadioRow value="custom" label={copy.filter_date_custom} />
            </RadioGroup>
            {deadlinePreset === "custom" ? (
              <DateRangeFields
                from={deadlineFrom}
                to={deadlineTo}
                onFrom={onDeadlineFrom}
                onTo={onDeadlineTo}
              />
            ) : null}
            <FieldTitle>{copy.filter_ingested}</FieldTitle>
            <RadioGroup
              value={ingestedPreset}
              onChange={(_, v) => setIngested(v as IngestedPreset)}
            >
              <RadioRow value="any" label={copy.filter_date_any_f} />
              <RadioRow value="today" label={copy.filter_ingested_today} />
              <RadioRow value="d3" label={copy.filter_ingested_3} />
              <RadioRow value="d7" label={copy.filter_ingested_7} />
              <RadioRow value="custom" label={copy.filter_date_custom} />
            </RadioGroup>
            {ingestedPreset === "custom" ? (
              <DateRangeFields
                from={ingestedFrom}
                to={ingestedTo}
                onFrom={onIngestedFrom}
                onTo={onIngestedTo}
              />
            ) : null}
          </Box>

          <Divider />

          <Box>
            <SectionTitle>{copy.filter_section_class}</SectionTitle>
            <FieldTitle>{copy.filter_priority_title}</FieldTitle>
            <Stack spacing={0} divider={<Divider flexItem />}>
              {PRIORITY_OPTIONS.map((opt) => (
                <CheckRow
                  key={opt.id}
                  checked={priority.includes(opt.id)}
                  label={opt.label}
                  onToggle={() => togglePriority(opt.id)}
                />
              ))}
            </Stack>
            {onPriceMinRub ? (
              <>
                <FieldTitle>{copy.filter_price}</FieldTitle>
                <Typography variant="body2" sx={{ px: 0.5, py: 0.5, color: stripe.navy }}>
                  {priceActive
                    ? copy.filter_price_from.replace("{price}", formatPrice(priceMinRub))
                    : copy.filter_date_any_f}
                </Typography>
                <Stack spacing={0.5} sx={{ px: 0.5, pt: 0.25 }}>
                  <Button
                    size="small"
                    variant="text"
                    onClick={() => onPriceMinRub(null)}
                    sx={{ justifyContent: "flex-start" }}
                  >
                    {copy.filter_price_show_all}
                  </Button>
                  <Button
                    size="small"
                    variant="text"
                    onClick={() => onPriceMinRub(settingsMinPrice)}
                    sx={{ justifyContent: "flex-start" }}
                  >
                    {copy.filter_price_from.replace("{price}", formatPrice(settingsMinPrice))}
                  </Button>
                  {onOpenSettings ? (
                    <Link
                      component="button"
                      variant="caption"
                      underline="hover"
                      onClick={() => {
                        setFiltersEl(null);
                        onOpenSettings();
                      }}
                      sx={{
                        cursor: "pointer",
                        border: "none",
                        background: "none",
                        textAlign: "left",
                      }}
                    >
                      {copy.filter_price_settings_link}
                    </Link>
                  ) : null}
                </Stack>
              </>
            ) : null}
          </Box>

          <Divider />

          <Box>
            <SectionTitle>{copy.filter_section_source}</SectionTitle>
            {onPlatformsSelected ? (
              <>
                <FieldTitle>{copy.filter_platform}</FieldTitle>
                <Stack spacing={0} divider={<Divider flexItem />}>
                  {platforms.map((platform) => (
                    <CheckRow
                      key={platform.platform_id}
                      checked={platformsSelected.includes(platform.platform_id)}
                      label={platform.name}
                      onToggle={() => togglePlatform(platform.platform_id)}
                    />
                  ))}
                </Stack>
              </>
            ) : null}
            {onBitrixFilter ? (
              <>
                <FieldTitle>{copy.filter_bitrix}</FieldTitle>
                <RadioGroup
                  value={bitrixFilter}
                  onChange={(_, v) => onBitrixFilter(v as BitrixFilter)}
                >
                  <RadioRow value="any" label={copy.filter_bitrix_any} />
                  <RadioRow value="in" label={copy.filter_bitrix_in} />
                  <RadioRow value="out" label={copy.filter_bitrix_out} />
                </RadioGroup>
              </>
            ) : null}
            {showAiReviewedFilter && onAiReviewedOnly ? (
              <>
                <FieldTitle>{copy.filter_ai_reviewed_menu_title}</FieldTitle>
                <CheckRow
                  checked={aiReviewedOnly}
                  label={copy.filter_ai_reviewed}
                  onToggle={() => onAiReviewedOnly(!aiReviewedOnly)}
                />
              </>
            ) : null}
          </Box>

          {activeCount > 0 ? (
            <>
              <Divider />
              <Box sx={{ textAlign: "right", px: 0.5 }}>
                <Link
                  component="button"
                  variant="caption"
                  underline="hover"
                  onClick={clearAllGrouped}
                  sx={{ cursor: "pointer", border: "none", background: "none" }}
                >
                  {copy.filter_menu_reset}
                </Link>
              </Box>
            </>
          ) : null}
        </Stack>
      </Popover>

      <Dialog
        open={markAllOpen}
        onClose={() => {
          if (markAllBusy) return;
          setMarkAllOpen(false);
        }}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>{copy.mark_all_viewed_confirm_title}</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            {markAllCount != null && markAllCount > 0
              ? copy.mark_all_viewed_confirm_body.replace("{n}", String(markAllCount))
              : copy.mark_all_viewed_none}
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setMarkAllOpen(false)}
            disabled={markAllBusy}
          >
            {copy.mark_all_viewed_cancel}
          </Button>
          {markAllCount != null && markAllCount > 0 ? (
            <Button
              variant="contained"
              disabled={markAllBusy}
              onClick={() => void confirmMarkAll()}
            >
              {copy.mark_all_viewed_confirm}
            </Button>
          ) : null}
        </DialogActions>
      </Dialog>

      <TextField
        fullWidth
        size="small"
        placeholder={copy.search_placeholder}
        value={search}
        onChange={(e) => onSearch(e.target.value)}
        slotProps={{ htmlInput: { "aria-label": copy.search_placeholder } }}
        sx={{
          bgcolor: stripe.surface,
          "& .MuiOutlinedInput-root": {
            borderRadius: `${viewCommandBarLayout.borderRadius}px`,
          },
        }}
      />
    </Box>
  );
}
