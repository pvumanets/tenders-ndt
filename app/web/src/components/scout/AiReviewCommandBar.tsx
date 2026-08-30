import { Box, Button, Typography } from "@mui/material";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";

export default function AiReviewCommandBar({
  onAiReview,
  aiBusy = false,
  aiDone = 0,
  aiTotal = 0,
}: {
  onAiReview: () => void;
  aiBusy?: boolean;
  aiDone?: number;
  aiTotal?: number;
}) {
  const inProgress = aiTotal > 0 && aiDone < aiTotal;

  return (
    <Box
      sx={{
        mb: 1.5,
        display: "flex",
        alignItems: "center",
        gap: 1.5,
        flexWrap: "wrap",
      }}
    >
      <Button
        variant="contained"
        size="small"
        disabled={aiBusy || inProgress}
        onClick={onAiReview}
        sx={{ flexShrink: 0, bgcolor: stripe.blurple }}
      >
        {aiBusy && !inProgress ? copy.action_ai_review_busy : copy.action_ai_review}
      </Button>
      {inProgress ? (
        <Typography variant="body2" sx={{ color: stripe.textMuted }}>
          {copy.ai_eta_progress.replace("{n}", String(aiDone)).replace("{m}", String(aiTotal))}
        </Typography>
      ) : aiTotal > 0 && aiDone >= aiTotal ? (
        <Typography variant="body2" sx={{ color: stripe.textMuted }}>
          {copy.ai_eta_done}
        </Typography>
      ) : null}
    </Box>
  );
}
