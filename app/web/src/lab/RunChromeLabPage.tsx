import { useMemo, useState } from "react";
import {
  Box,
  Button,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import ThemeRegistry from "../theme/ThemeRegistry";
import { stripe } from "../theme/palette";
import { labCopy as t } from "./labCopy";
import { LAB_PRESETS, type LabPresetId, type LabMockState } from "./labMocks";
import RunChromeVariantA from "./variants/RunChromeVariantA";
import RunChromeVariantB from "./variants/RunChromeVariantB";
import RunChromeVariantC from "./variants/RunChromeVariantC";

type VariantId = "A" | "B" | "C";

const VARIANT_META: Record<VariantId, { title: string; blurb: string }> = {
  A: { title: t.a_title, blurb: t.a_blurb },
  B: { title: t.b_title, blurb: t.b_blurb },
  C: { title: t.c_title, blurb: t.c_blurb },
};

const PRESET_ORDER: LabPresetId[] = ["idle", "running", "done", "ai_busy", "ai_done"];

const PRESET_LABEL: Record<LabPresetId, string> = {
  idle: t.preset_idle,
  running: t.preset_running,
  done: t.preset_done,
  ai_busy: t.preset_ai_busy,
  ai_done: t.preset_ai_done,
};

export default function RunChromeLabPage() {
  const [variant, setVariant] = useState<VariantId>("A");
  const [preset, setPreset] = useState<LabPresetId>("idle");
  const state: LabMockState = useMemo(() => LAB_PRESETS[preset], [preset]);

  function applyPreset(id: LabPresetId) {
    setPreset(id);
  }

  function onStart() {
    setPreset("running");
  }
  function onStop() {
    setPreset("idle");
  }
  function onAi() {
    setPreset("ai_busy");
  }
  function onPrimary() {
    setPreset("ai_busy");
  }
  function onOnlyRun() {
    setPreset("running");
  }
  function onOnlyAi() {
    setPreset("ai_busy");
  }

  const meta = VARIANT_META[variant];

  return (
    <ThemeRegistry>
      <Box
        sx={{
          minHeight: "100vh",
          bgcolor: stripe.surfaceSubtle,
          px: { xs: 2, md: 4 },
          py: 3,
        }}
      >
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1}
          sx={{ alignItems: { sm: "center" }, mb: 1, flexWrap: "wrap" }}
        >
          <Typography variant="h2" sx={{ flexGrow: 1 }}>
            {t.page_title}
          </Typography>
          <Button
            size="small"
            variant="text"
            href="/"
            sx={{ color: stripe.blurple, textTransform: "none" }}
          >
            {t.back_to_app}
          </Button>
        </Stack>
        <Typography variant="body2" sx={{ color: stripe.textMuted, mb: 2 }}>
          {t.page_hint}
        </Typography>

        <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block", mb: 0.75 }}>
          {t.variant_label}
        </Typography>
        <ToggleButtonGroup
          exclusive
          size="small"
          value={variant}
          onChange={(_, v: VariantId | null) => {
            if (v) setVariant(v);
          }}
          sx={{ mb: 2, bgcolor: stripe.surface }}
        >
          {(["A", "B", "C"] as VariantId[]).map((id) => (
            <ToggleButton key={id} value={id} sx={{ px: 2, textTransform: "none" }}>
              {id}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>

        <Box sx={{ mb: 2.5 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, color: stripe.navy }}>
            {meta.title}
          </Typography>
          <Typography variant="body2" sx={{ color: stripe.textMuted }}>
            {meta.blurb}
          </Typography>
        </Box>

        <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block", mb: 0.75 }}>
          {t.preset_label}
        </Typography>
        <ToggleButtonGroup
          exclusive
          size="small"
          value={preset}
          onChange={(_, v: LabPresetId | null) => {
            if (v) applyPreset(v);
          }}
          sx={{ mb: 3, flexWrap: "wrap", bgcolor: stripe.surface }}
        >
          {PRESET_ORDER.map((id) => (
            <ToggleButton key={id} value={id} sx={{ px: 1.5, textTransform: "none" }}>
              {PRESET_LABEL[id]}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>

        <Box sx={{ maxWidth: 720 }}>
          {variant === "A" ? (
            <RunChromeVariantA state={state} onStart={onStart} onStop={onStop} onAi={onAi} />
          ) : null}
          {variant === "B" ? (
            <RunChromeVariantB
              state={state}
              onPrimary={onPrimary}
              onOnlyRun={onOnlyRun}
              onOnlyAi={onOnlyAi}
              onStop={onStop}
            />
          ) : null}
          {variant === "C" ? (
            <RunChromeVariantC state={state} onStart={onStart} onStop={onStop} onAi={onAi} />
          ) : null}
        </Box>

        {/* Ghost board chrome so the block sits in context */}
        <Box
          sx={{
            mt: 2,
            maxWidth: 720,
            height: 72,
            borderRadius: 1,
            border: `1px dashed ${stripe.border}`,
            bgcolor: stripe.surface,
            display: "flex",
            alignItems: "center",
            px: 2,
          }}
        >
          <Typography variant="caption" sx={{ color: stripe.textMuted }}>
            Дальше на «Лоты»: фильтры и доска (вне lab)
          </Typography>
        </Box>
      </Box>
    </ThemeRegistry>
  );
}
