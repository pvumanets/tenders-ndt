import { useState } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { copy } from "../../copy";
import type { TeachBucket } from "../../types";
import { stripe } from "../../theme/palette";

export type TierTeachPending = {
  tender_id: string;
  from_bucket: TeachBucket;
  to_bucket: TeachBucket;
};

export default function TierTeachDialog({
  pending,
  busy,
  onCancel,
  onSubmit,
}: {
  pending: TierTeachPending | null;
  busy?: boolean;
  onCancel: () => void;
  onSubmit: (payload: { drop_tier_correct: boolean; reason_ru: string }) => void;
}) {
  const open = pending != null;
  const [correct, setCorrect] = useState<"yes" | "no">("yes");
  const [reason, setReason] = useState("");
  const involvesExpired =
    pending != null && (pending.from_bucket === "expired" || pending.to_bucket === "expired");
  const canSubmit = reason.trim().length > 0 && !busy;

  function handleClose() {
    if (busy) return;
    setCorrect("yes");
    setReason("");
    onCancel();
  }

  function handleSubmit() {
    const text = reason.trim();
    if (!text || busy) return;
    onSubmit({ drop_tier_correct: correct === "yes", reason_ru: text });
  }

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>{copy.teach_dialog_title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 0.5 }}>
          {involvesExpired ? (
            <Typography variant="body2" sx={{ color: stripe.textMuted }}>
              {copy.teach_expired_hint}
            </Typography>
          ) : null}
          <FormControl>
            <FormLabel>{copy.teach_drop_correct}</FormLabel>
            <RadioGroup
              row
              value={correct}
              onChange={(_, v) => setCorrect(v === "no" ? "no" : "yes")}
            >
              <FormControlLabel value="yes" control={<Radio />} label={copy.teach_yes} />
              <FormControlLabel value="no" control={<Radio />} label={copy.teach_no} />
            </RadioGroup>
          </FormControl>
          <TextField
            label={copy.teach_reason_label}
            placeholder={copy.teach_reason_placeholder}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            multiline
            minRows={3}
            fullWidth
            required
            slotProps={{ htmlInput: { maxLength: 2000 } }}
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} disabled={busy}>
          {copy.teach_cancel}
        </Button>
        <Button variant="contained" onClick={handleSubmit} disabled={!canSubmit}>
          {copy.teach_submit}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
