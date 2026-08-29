import { useEffect } from "react";
import {
  Box,
  Button,
  FormControlLabel,
  IconButton,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";
import DetailDrawerShell from "../../vendor/personal/people/DetailDrawerShell";
import type { SearchGroup } from "../../types";

export type GroupDraft = {
  id?: string;
  name: string;
  queriesText: string;
  excludeText: string;
  limit_n: number;
  in_queue: boolean;
  sort_order: number;
};

export function emptyGroupDraft(sortOrder: number): GroupDraft {
  return {
    name: "",
    queriesText: "",
    excludeText: "",
    limit_n: 0,
    in_queue: false,
    sort_order: sortOrder,
  };
}

export function draftFromSearchGroup(group: SearchGroup): GroupDraft {
  return {
    id: group.id,
    name: group.name,
    queriesText: group.queries.join("\n"),
    excludeText: (group.exclude ?? []).join("\n"),
    limit_n: group.limit_n,
    in_queue: group.in_queue,
    sort_order: group.sort_order,
  };
}

export function parseGroupLines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export default function SearchGroupDrawer({
  draft,
  saving,
  onChange,
  onSave,
  onClose,
}: {
  draft: GroupDraft;
  saving: boolean;
  onChange: (next: GroupDraft) => void;
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

  const canSave =
    draft.name.trim().length > 0 && parseGroupLines(draft.queriesText).length > 0;

  return (
    <DetailDrawerShell open onClose={onClose}>
      <Box sx={{ p: 2.5, borderBottom: `1px solid ${stripe.border}` }}>
        <Stack
          direction="row"
          spacing={1}
          sx={{ justifyContent: "space-between", alignItems: "flex-start" }}
        >
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="caption" color="text.secondary">
              {copy.groups_drawer_title}
            </Typography>
            <Typography component="h2" sx={{ mt: 0.5, fontWeight: 600, color: stripe.navy }}>
              {draft.name.trim() || copy.groups_add}
            </Typography>
          </Box>
          <IconButton size="small" aria-label={copy.groups_drawer_close_aria} onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      </Box>

      <Box sx={{ p: 2.5, flex: 1, overflow: "auto" }}>
        <Stack spacing={1.5}>
          <TextField
            size="small"
            label={copy.groups_name}
            value={draft.name}
            onChange={(e) => onChange({ ...draft, name: e.target.value })}
            fullWidth
          />
          <TextField
            size="small"
            label={copy.groups_queries}
            value={draft.queriesText}
            onChange={(e) => onChange({ ...draft, queriesText: e.target.value })}
            multiline
            minRows={4}
            fullWidth
          />
          <TextField
            size="small"
            label={copy.groups_exclude}
            value={draft.excludeText}
            onChange={(e) => onChange({ ...draft, excludeText: e.target.value })}
            helperText={copy.groups_exclude_hint}
            multiline
            minRows={3}
            fullWidth
          />
          <TextField
            size="small"
            type="number"
            label={copy.groups_limit}
            value={draft.limit_n}
            onChange={(e) => onChange({ ...draft, limit_n: Number(e.target.value) })}
            helperText={copy.groups_limit_hint}
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
            label={copy.groups_queue}
          />
        </Stack>
      </Box>

      <Box sx={{ p: 2.5, borderTop: `1px solid ${stripe.border}` }}>
        <Stack direction="row" spacing={1}>
          <Button variant="contained" size="small" disabled={saving || !canSave} onClick={onSave}>
            {copy.groups_save}
          </Button>
          <Button size="small" disabled={saving} onClick={onClose}>
            {copy.groups_cancel}
          </Button>
        </Stack>
      </Box>
    </DetailDrawerShell>
  );
}
