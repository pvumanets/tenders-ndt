import { useEffect } from "react";
import {
  Box,
  Button,
  FormControlLabel,
  IconButton,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";
import DetailDrawerShell from "../../vendor/personal/people/DetailDrawerShell";

export type SearchDraft = {
  id?: string;
  name: string;
  platform_id: string;
  queriesText: string;
  excludeText: string;
  limit_n: number;
  in_queue: boolean;
  sort_order: number;
};

export function emptySearchDraft(sortOrder: number): SearchDraft {
  return {
    name: "",
    platform_id: "rostender",
    queriesText: "",
    excludeText: "",
    limit_n: 0,
    in_queue: false,
    sort_order: sortOrder,
  };
}

export function draftFromNamedSearch(search: {
  id: string;
  name: string;
  platform_id: string;
  queries: string[];
  exclude?: string[];
  limit_n: number;
  in_queue: boolean;
  sort_order: number;
}): SearchDraft {
  return {
    id: search.id,
    name: search.name,
    platform_id: search.platform_id,
    queriesText: search.queries.join("\n"),
    excludeText: (search.exclude ?? []).join("\n"),
    limit_n: search.limit_n,
    in_queue: search.in_queue,
    sort_order: search.sort_order,
  };
}

export function parseSearchQueries(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export default function SearchSettingsDrawer({
  draft,
  saving,
  onChange,
  onSave,
  onClose,
}: {
  draft: SearchDraft;
  saving: boolean;
  onChange: (next: SearchDraft) => void;
  onSave: () => void;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const canSave = draft.name.trim().length > 0 && parseSearchQueries(draft.queriesText).length > 0;

  return (
    <DetailDrawerShell open onClose={onClose}>
      <Box sx={{ p: 2.5, borderBottom: `1px solid ${stripe.border}` }}>
        <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "flex-start" }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="caption" color="text.secondary">
              {copy.searches_drawer_title}
            </Typography>
            <Typography component="h2" sx={{ mt: 0.5, fontWeight: 600, color: stripe.navy }}>
              {draft.name.trim() || copy.searches_add}
            </Typography>
          </Box>
          <IconButton size="small" aria-label={copy.searches_drawer_close_aria} onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      </Box>

      <Box sx={{ p: 2.5, flex: 1, overflow: "auto" }}>
        <Stack spacing={1.5}>
          <TextField
            size="small"
            label={copy.searches_name}
            value={draft.name}
            onChange={(e) => onChange({ ...draft, name: e.target.value })}
            fullWidth
          />
          <TextField
            size="small"
            select
            label={copy.searches_platform}
            value={draft.platform_id}
            onChange={(e) => onChange({ ...draft, platform_id: e.target.value })}
            fullWidth
          >
            <MenuItem value="rostender">{copy.platform_rostender}</MenuItem>
            <MenuItem value="tender-pro">{copy.platform_tender_pro}</MenuItem>
          </TextField>
          <TextField
            size="small"
            label={copy.searches_queries}
            value={draft.queriesText}
            onChange={(e) => onChange({ ...draft, queriesText: e.target.value })}
            multiline
            minRows={4}
            fullWidth
          />
          <TextField
            size="small"
            label={copy.searches_exclude}
            value={draft.excludeText}
            onChange={(e) => onChange({ ...draft, excludeText: e.target.value })}
            helperText={copy.searches_exclude_hint}
            multiline
            minRows={3}
            fullWidth
          />
          {draft.platform_id === "tender-pro" ? (
            <Typography variant="caption" color="text.secondary">
              {copy.searches_tender_pro_docs}
            </Typography>
          ) : null}
          <TextField
            size="small"
            type="number"
            label={copy.searches_limit}
            value={draft.limit_n}
            onChange={(e) => onChange({ ...draft, limit_n: Number(e.target.value) })}
            helperText={copy.searches_limit_hint}
            slotProps={{ htmlInput: { min: 0 } }}
            fullWidth
          />
          <FormControlLabel
            control={
              <Switch
                checked={draft.in_queue}
                onChange={(_, checked) => onChange({ ...draft, in_queue: checked })}
              />
            }
            label={copy.searches_queue}
          />
        </Stack>
      </Box>

      <Box sx={{ p: 2.5, borderTop: `1px solid ${stripe.border}` }}>
        <Stack direction="row" spacing={1}>
          <Button variant="contained" size="small" disabled={saving || !canSave} onClick={onSave}>
            {copy.searches_save}
          </Button>
          <Button size="small" disabled={saving} onClick={onClose}>
            {copy.searches_cancel}
          </Button>
        </Stack>
      </Box>
    </DetailDrawerShell>
  );
}
