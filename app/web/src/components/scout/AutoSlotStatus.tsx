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
    <Typography variant="body2" sx={{ color: stripe.textMuted, mb: 0.5 }}>
      {slotStatusText(schedule, status)}
    </Typography>
  );
}
