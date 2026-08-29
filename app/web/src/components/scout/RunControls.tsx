import { Button, Stack } from "@mui/material";
import { copy } from "../../copy";

export default function RunControls({
  canStart,
  canStop,
  busy,
  running,
  onStart,
  onStop,
}: {
  canStart: boolean;
  canStop: boolean;
  busy: boolean;
  running: boolean;
  onStart: () => void;
  onStop: () => void;
}) {
  return (
    <Stack direction="row" spacing={1}>
      <Button variant="contained" disabled={!canStart} onClick={onStart}>
        {busy && !running ? copy.run_start_busy : copy.run_start}
      </Button>
      <Button variant="outlined" disabled={!canStop} onClick={onStop}>
        {copy.run_stop}
      </Button>
    </Stack>
  );
}
