import { Box, Button, FormControlLabel, Stack, Switch, Typography } from "@mui/material";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";
import type { SearchGroup } from "../../types";

export default function SearchGroupList({
  groups,
  locked,
  draftOpen,
  onAdd,
  onEdit,
  onDelete,
  onToggleQueue,
}: {
  groups: SearchGroup[];
  locked: boolean;
  draftOpen: boolean;
  onAdd: () => void;
  onEdit: (group: SearchGroup) => void;
  onDelete: (group: SearchGroup) => void;
  onToggleQueue: (group: SearchGroup, inQueue: boolean) => void;
}) {
  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 1, alignItems: "center", justifyContent: "flex-end" }}>
        <Button
          size="small"
          variant="outlined"
          disabled={locked || draftOpen}
          onClick={onAdd}
        >
          {copy.groups_add}
        </Button>
      </Stack>
      {groups.length === 0 ? (
        <Box>
          <Typography variant="body2" color="text.secondary">
            {copy.groups_empty}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            {copy.groups_empty_body}
          </Typography>
        </Box>
      ) : (
        <Stack spacing={1}>
          {groups.map((group) => (
            <Box
              key={group.id}
              sx={{
                py: 0.75,
                px: 0.5,
                borderBottom: `1px solid ${stripe.border}`,
              }}
            >
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Typography sx={{ flex: 1, minWidth: 0 }} noWrap>
                  {group.name}
                </Typography>
                <FormControlLabel
                  sx={{ mr: 0, flexShrink: 0 }}
                  control={
                    <Switch
                      size="small"
                      checked={group.in_queue}
                      disabled={locked}
                      onChange={(_, checked) => onToggleQueue(group, checked)}
                      slotProps={{
                        input: { "aria-label": `${copy.groups_queue}: ${group.name}` },
                      }}
                    />
                  }
                  label={copy.groups_queue}
                />
                <Button size="small" disabled={locked} onClick={() => onEdit(group)}>
                  {copy.groups_edit}
                </Button>
                <Button
                  size="small"
                  color="error"
                  disabled={locked}
                  onClick={() => {
                    if (window.confirm(copy.groups_delete_confirm)) onDelete(group);
                  }}
                >
                  {copy.groups_delete}
                </Button>
              </Stack>
              <Typography variant="caption" color="text.secondary" noWrap display="block">
                {group.queries.join(", ")}
                {group.limit_n > 0 ? ` · ${copy.groups_limit} ${group.limit_n}` : ""}
              </Typography>
            </Box>
          ))}
        </Stack>
      )}
    </Box>
  );
}
