import { Box, Button, ToggleButton, ToggleButtonGroup } from "@mui/material";
import ViewWeekOutlinedIcon from "@mui/icons-material/ViewWeekOutlined";
import TableRowsOutlinedIcon from "@mui/icons-material/TableRowsOutlined";
import type { ViewMode } from "../../types";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";
import { viewCommandBarLayout } from "../../vendor/personal/layout/view-command-bar";
import ViewCommandBar from "../../vendor/personal/shell/ViewCommandBar";

export default function AiReviewCommandBar({
  view,
  onView,
  onAiReview,
  aiBusy = false,
}: {
  view: ViewMode;
  onView: (v: ViewMode) => void;
  onAiReview: () => void;
  aiBusy?: boolean;
}) {
  return (
    <Box sx={{ mb: viewCommandBarLayout.marginBottom }}>
      <ViewCommandBar
        sticky
        sx={{
          flexWrap: "wrap",
          gridTemplateColumns: { xs: "1fr", md: "1fr auto" },
          mb: 1,
        }}
      >
        <ViewCommandBar.Start sx={{ flex: 1, minWidth: 0 }} />
        <ViewCommandBar.End sx={{ width: { xs: "100%", md: "auto" }, justifyContent: "flex-end", gap: 1 }}>
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
          <Button
            variant="contained"
            size="small"
            disabled={aiBusy}
            onClick={onAiReview}
            sx={{ flexShrink: 0, bgcolor: stripe.blurple }}
          >
            {aiBusy ? copy.action_ai_review_busy : copy.action_ai_review}
          </Button>
        </ViewCommandBar.End>
      </ViewCommandBar>
    </Box>
  );
}
