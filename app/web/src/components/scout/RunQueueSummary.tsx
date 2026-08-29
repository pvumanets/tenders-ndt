import { Typography } from "@mui/material";
import { copy } from "../../copy";
import {
  formatQueueStepLine,
  formatQueueSummary,
  platformLabel,
} from "../../lib/inbox";
import type { TechStatus } from "../../types";

export default function RunQueueSummary({
  status,
  queuedGroups,
  enabledPlatforms,
}: {
  status: TechStatus;
  queuedGroups: number;
  enabledPlatforms: number;
}) {
  if (status.running && status.queue_total > 0) {
    const current = Math.min(
      status.queue_index + 1,
      Math.max(status.queue_total, status.queue.length),
    );
    const step = status.queue[status.queue_index];
    const group =
      step?.group_name || step?.name || status.current_search_name || "—";
    const platform = platformLabel(
      step?.platform_id || status.current_platform_id || "",
    );
    return (
      <Typography variant="body2" color="text.secondary">
        {formatQueueStepLine(current, status.queue_total, group, platform)}
      </Typography>
    );
  }

  const steps = queuedGroups * enabledPlatforms;
  if (steps === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {copy.run_queue_empty}
      </Typography>
    );
  }

  return (
    <Typography variant="body2" color="text.secondary">
      {formatQueueSummary(queuedGroups, enabledPlatforms, steps)}
    </Typography>
  );
}
