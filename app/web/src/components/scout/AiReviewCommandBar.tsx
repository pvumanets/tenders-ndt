import { Alert, Box, Button, Typography } from "@mui/material";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";

export default function AiReviewCommandBar({
  onAiReview,
  onRetryErrors,
  aiBusy = false,
  aiDone = 0,
  aiTotal = 0,
  aiFailures = 0,
}: {
  onAiReview: () => void;
  onRetryErrors?: () => void;
  aiBusy?: boolean;
  aiDone?: number;
  aiTotal?: number;
  aiFailures?: number;
}) {
  const inProgress = aiTotal > 0 && aiDone < aiTotal;
  const showRetry = aiFailures > 0 && Boolean(onRetryErrors);

  return (
    <Box
      sx={{
        mb: 1.5,
        display: "flex",
        flexDirection: "column",
        gap: 1,
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          flexWrap: "wrap",
        }}
      >
        <Button
          variant="outlined"
          size="small"
          disabled={aiBusy || inProgress}
          onClick={onAiReview}
          sx={{ flexShrink: 0 }}
        >
          {aiBusy && !inProgress ? copy.action_ai_review_busy : copy.action_ai_review}
        </Button>
        {showRetry ? (
          <Button
            variant="outlined"
            size="small"
            disabled={aiBusy || inProgress}
            onClick={onRetryErrors}
            sx={{ flexShrink: 0 }}
          >
            {copy.action_ai_retry_errors}
          </Button>
        ) : null}
        {inProgress ? (
          <Typography variant="body2" sx={{ color: stripe.textMuted }}>
            {copy.ai_eta_progress.replace("{n}", String(aiDone)).replace("{m}", String(aiTotal))}
          </Typography>
        ) : aiTotal > 0 && aiDone >= aiTotal ? (
          <Typography variant="body2" sx={{ color: stripe.textMuted }}>
            {copy.ai_eta_done}
          </Typography>
        ) : (
          <Typography variant="body2" sx={{ color: stripe.textMuted }}>
            {copy.ai_review_cap_hint}
          </Typography>
        )}
      </Box>
      {showRetry ? (
        <Alert severity="warning" sx={{ py: 0.5 }}>
          {copy.ai_banner_failures.replace("{n}", String(aiFailures))}
        </Alert>
      ) : null}
    </Box>
  );
}
