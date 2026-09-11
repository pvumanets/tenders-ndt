import { Typography } from "@mui/material";
import type { ScheduleSettings, TechStatus } from "../../types";
import { stripe } from "../../theme/palette";
import { slotStatusText } from "../../lib/slot-status";

export default function AutoSlotStatus({
  schedule,
  status,
}: {
  schedule: ScheduleSettings;
  status: TechStatus;
}) {
  return (
    <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block", mb: 1 }}>
      {slotStatusText(schedule, status)}
    </Typography>
  );
}
