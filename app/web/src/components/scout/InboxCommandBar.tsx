import { useState, type ReactNode } from "react";
import {
  Box,
  Button,
  Checkbox,
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
import type { DeadlinePreset, IngestedPreset, PriorityFilter, SalesTier, ViewMode } from "../../types";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";
import { viewCommandBarLayout } from "../../vendor/personal/layout/view-command-bar";
import FilterTriggerButton from "../../vendor/personal/shell/FilterTriggerButton";
import ViewCommandBar from "../../vendor/personal/shell/ViewCommandBar";

const MENU_WIDTH = 280;

function menuPaperSx() {
  return {
    width: MENU_WIDTH,
    maxWidth: "calc(100vw - 32px)",
    p: 1.5,
    mt: 0.5,
    border: `1px solid ${stripe.border}`,
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
  };
}

function FilterMenuPopover({
  open,
  anchorEl,
  onClose,
  title,
  children,
  resetVisible,
  onReset,
}: {
  open: boolean;
  anchorEl: HTMLElement | null;
  onClose: () => void;
  title: string;
  children: ReactNode;
  resetVisible: boolean;
  onReset: () => void;
}) {
  const theme = useTheme();
  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
      transformOrigin={{ vertical: "top", horizontal: "left" }}
      slotProps={{ paper: { sx: menuPaperSx() } }}
    >
      <Typography
        variant="caption"
        sx={{
          display: "block",
          color: stripe.textMuted,
          fontWeight: theme.density.weight.medium,
          mb: 1,
          px: 0.5,
        }}
      >
        {title}
      </Typography>
      {children}
      {resetVisible ? (
        <>
          <Divider sx={{ my: 1 }} />
          <Box sx={{ textAlign: "right", px: 0.5 }}>
            <Link
              component="button"
              variant="caption"
              underline="hover"
              onClick={onReset}
              sx={{ cursor: "pointer", border: "none", background: "none" }}
            >
              {copy.filter_menu_reset}
            </Link>
          </Box>
        </>
      ) : null}
    </Popover>
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

const PRIORITY_OPTIONS: { id: SalesTier; label: string }[] = [
  { id: "L1", label: copy.filter_priority_hot },
  { id: "L2", label: copy.filter_priority_strong },
  { id: "L3", label: copy.filter_priority_watch },
];

export default function InboxCommandBar({
  unreadOnly,
  onUnreadOnly,
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
  showAiReviewedFilter = false,
  aiReviewedOnly = false,
  onAiReviewedOnly,
}: {
  unreadOnly: boolean;
  onUnreadOnly: (v: boolean) => void;
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
  showAiReviewedFilter?: boolean;
  aiReviewedOnly?: boolean;
  onAiReviewedOnly?: (v: boolean) => void;
}) {
  const [priorityEl, setPriorityEl] = useState<HTMLElement | null>(null);
  const [deadlineEl, setDeadlineEl] = useState<HTMLElement | null>(null);
  const [ingestedEl, setIngestedEl] = useState<HTMLElement | null>(null);
  const [aiEl, setAiEl] = useState<HTMLElement | null>(null);

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
          <FilterTriggerButton
            label={copy.filter_menu}
            badgeContent={priority.length}
            onClick={(e) => setPriorityEl(e.currentTarget)}
          />
          <FilterTriggerButton
            label={copy.filter_deadline}
            badgeContent={deadlinePreset === "any" ? 0 : 1}
            onClick={(e) => setDeadlineEl(e.currentTarget)}
          />
          <FilterTriggerButton
            label={copy.filter_ingested}
            badgeContent={ingestedPreset === "any" ? 0 : 1}
            onClick={(e) => setIngestedEl(e.currentTarget)}
          />
          {showAiReviewedFilter ? (
            <FilterTriggerButton
              label={copy.filter_ai_reviewed_trigger}
              badgeContent={aiReviewedOnly ? 1 : 0}
              onClick={(e) => setAiEl(e.currentTarget)}
            />
          ) : null}
        </ViewCommandBar.Start>

        <ViewCommandBar.End sx={{ width: { xs: "100%", md: "auto" }, justifyContent: "flex-end" }}>
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

      <FilterMenuPopover
        open={Boolean(priorityEl)}
        anchorEl={priorityEl}
        onClose={() => setPriorityEl(null)}
        title={copy.col_priority}
        resetVisible={priority.length > 0}
        onReset={() => onPriority([])}
      >
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
      </FilterMenuPopover>

      <FilterMenuPopover
        open={Boolean(deadlineEl)}
        anchorEl={deadlineEl}
        onClose={() => setDeadlineEl(null)}
        title={copy.filter_deadline}
        resetVisible={deadlinePreset !== "any"}
        onReset={() => setDeadline("any")}
      >
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
      </FilterMenuPopover>

      <FilterMenuPopover
        open={Boolean(ingestedEl)}
        anchorEl={ingestedEl}
        onClose={() => setIngestedEl(null)}
        title={copy.filter_ingested}
        resetVisible={ingestedPreset !== "any"}
        onReset={() => setIngested("any")}
      >
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
      </FilterMenuPopover>

      {showAiReviewedFilter && onAiReviewedOnly ? (
        <FilterMenuPopover
          open={Boolean(aiEl)}
          anchorEl={aiEl}
          onClose={() => setAiEl(null)}
          title={copy.filter_ai_reviewed_trigger}
          resetVisible={aiReviewedOnly}
          onReset={() => onAiReviewedOnly(false)}
        >
          <CheckRow
            checked={aiReviewedOnly}
            label={copy.filter_ai_reviewed_trigger}
            onToggle={() => onAiReviewedOnly(!aiReviewedOnly)}
          />
        </FilterMenuPopover>
      ) : null}

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
