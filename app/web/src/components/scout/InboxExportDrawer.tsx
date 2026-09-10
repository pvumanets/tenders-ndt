import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  IconButton,
  Link,
  Radio,
  RadioGroup,
  Stack,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { copy } from "../../copy";
import {
  AI_REVIEW_EXPORT_PRESET,
  ALL_EXPORT_COLUMNS,
  EXPORT_COLUMN_GROUPS,
  EXPORT_COLUMN_LABELS,
  type ExportColumnKey,
  type ExportFormat,
} from "../../lib/inbox-export";
import {
  fetchInboxTotal,
  postInboxExport,
  type InboxListQuery,
  UnauthorizedError,
} from "../../lib/inbox";
import { stripe } from "../../theme/palette";
import DetailDrawerShell from "../../vendor/personal/people/DetailDrawerShell";

export type ExportPrefill = InboxListQuery & {
  /** Local filter: only lots marked AI-wrong. */
  ai_wrong?: boolean;
};

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function SectionTitle({ children }: { children: string }) {
  return (
    <Typography variant="subtitle2" sx={{ fontWeight: 600, color: stripe.navy, mb: 0.5 }}>
      {children}
    </Typography>
  );
}

export default function InboxExportDrawer({
  open,
  onClose,
  prefill,
  onUnauthorized,
  onError,
}: {
  open: boolean;
  onClose: () => void;
  prefill: ExportPrefill;
  onUnauthorized?: () => void;
  onError?: (message: string) => void;
}) {
  const [format, setFormat] = useState<ExportFormat>("csv");
  const [columns, setColumns] = useState<ExportColumnKey[]>([...AI_REVIEW_EXPORT_PRESET]);
  const [filters, setFilters] = useState<ExportPrefill>(prefill);
  const [count, setCount] = useState<number | null>(null);
  const [countState, setCountState] = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    setFormat("csv");
    setColumns([...AI_REVIEW_EXPORT_PRESET]);
    setFilters(prefill);
    setCount(null);
    setCountState("idle");
    setBusy(false);
    // Init once when drawer opens; prefill is snapshotted by App.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- open edge only
  }, [open]);

  const listQuery: InboxListQuery = useMemo(
    () => ({
      unread: filters.unread,
      tier: filters.tier ?? "fit",
      q: filters.q,
      deadline_from: filters.deadline_from,
      deadline_to: filters.deadline_to,
      ingested_from: filters.ingested_from,
      ingested_to: filters.ingested_to,
      ai_reviewed: filters.ai_reviewed,
      ai_trigger: filters.ai_trigger,
      ai_wrong: filters.ai_wrong,
      price_min_rub: filters.price_min_rub,
      platform: filters.platform,
      bitrix: filters.bitrix,
      sort: filters.sort,
    }),
    [filters],
  );

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setCountState("loading");
    fetchInboxTotal(listQuery)
      .then((n) => {
        if (cancelled) return;
        setCount(n);
        setCountState("ok");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) {
          onUnauthorized?.();
          return;
        }
        setCountState("error");
        setCount(null);
      });
    return () => {
      cancelled = true;
    };
  }, [open, listQuery, onUnauthorized]);

  const selected = useMemo(() => new Set(columns), [columns]);
  const n = count ?? 0;
  const canDownload = countState === "ok" && n > 0 && columns.length > 0 && !busy;

  function toggleColumn(key: ExportColumnKey) {
    setColumns((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
    );
  }

  function applyPreset() {
    setColumns([...AI_REVIEW_EXPORT_PRESET]);
  }

  function applyAllColumns() {
    setColumns([...ALL_EXPORT_COLUMNS]);
  }

  async function onDownload() {
    if (!canDownload) return;
    setBusy(true);
    try {
      const { blob, filename } = await postInboxExport({
        ...listQuery,
        format,
        columns,
      });
      downloadBlob(blob, filename);
      onClose();
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized?.();
        return;
      }
      onError?.(copy.export_error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <DetailDrawerShell open={open} onClose={onClose} width={520}>
      <Box sx={{ p: 2.5, borderBottom: `1px solid ${stripe.border}` }}>
        <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "flex-start" }}>
          <Typography component="h2" sx={{ fontWeight: 600, color: stripe.navy }}>
            {copy.export_drawer_title}
          </Typography>
          <IconButton size="small" aria-label={copy.export_drawer_close_aria} onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      </Box>

      <Box sx={{ p: 2.5, flex: 1, overflow: "auto" }}>
        <Stack spacing={2.5}>
          <Box>
            <SectionTitle>{copy.export_section_format}</SectionTitle>
            <RadioGroup
              value={format}
              onChange={(_, v) => setFormat(v as ExportFormat)}
            >
              <FormControlLabel value="csv" control={<Radio size="small" />} label={copy.export_format_csv} />
              <FormControlLabel value="xlsx" control={<Radio size="small" />} label={copy.export_format_xlsx} />
            </RadioGroup>
          </Box>

          <Box>
            <SectionTitle>{copy.export_section_columns}</SectionTitle>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {copy.export_columns_helper}
            </Typography>
            <Stack direction="row" spacing={1.5} sx={{ mb: 1, flexWrap: "wrap" }}>
              <Link component="button" type="button" variant="body2" onClick={applyPreset} underline="hover">
                {copy.export_preset_ai}
              </Link>
              <Link component="button" type="button" variant="body2" onClick={applyAllColumns} underline="hover">
                {copy.export_columns_all}
              </Link>
            </Stack>
            <Stack spacing={0.25}>
              {EXPORT_COLUMN_GROUPS.flatMap((group) =>
                group.keys.map((key) => (
                  <FormControlLabel
                    key={key}
                    control={
                      <Checkbox
                        size="small"
                        checked={selected.has(key)}
                        onChange={() => toggleColumn(key)}
                      />
                    }
                    label={EXPORT_COLUMN_LABELS[key]}
                  />
                )),
              )}
            </Stack>
          </Box>

          <Box>
            <SectionTitle>{copy.export_section_lots}</SectionTitle>
            <Stack spacing={0.5}>
              <Typography variant="caption" color="text.secondary">
                {copy.filter_section_class}
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    checked={Boolean(filters.unread)}
                    onChange={(_, checked) => setFilters((f) => ({ ...f, unread: checked || undefined }))}
                  />
                }
                label={copy.filter_unread}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    checked={Boolean(filters.ai_reviewed)}
                    onChange={(_, checked) =>
                      setFilters((f) => ({
                        ...f,
                        ai_reviewed: checked || undefined,
                        ai_trigger: checked ? f.ai_trigger : undefined,
                      }))
                    }
                  />
                }
                label={copy.filter_ai_reviewed}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    checked={Boolean(filters.ai_wrong)}
                    onChange={(_, checked) => setFilters((f) => ({ ...f, ai_wrong: checked || undefined }))}
                  />
                }
                label={copy.export_filter_ai_wrong}
              />
              <Typography variant="caption" color="text.secondary" sx={{ pt: 0.5 }}>
                {copy.filter_section_source}
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    checked={filters.bitrix === "in"}
                    onChange={(_, checked) =>
                      setFilters((f) => ({
                        ...f,
                        bitrix: checked ? "in" : undefined,
                      }))
                    }
                  />
                }
                label={copy.filter_bitrix_in}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    checked={filters.bitrix === "out"}
                    onChange={(_, checked) =>
                      setFilters((f) => ({
                        ...f,
                        bitrix: checked ? "out" : undefined,
                      }))
                    }
                  />
                }
                label={copy.filter_bitrix_out}
              />
              <Typography variant="caption" color="text.secondary" sx={{ pt: 0.5 }}>
                {copy.filter_section_dates}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {[
                  filters.deadline_from || filters.deadline_to
                    ? `${copy.filter_deadline}: ${filters.deadline_from || "…"} — ${filters.deadline_to || "…"}`
                    : null,
                  filters.ingested_from || filters.ingested_to
                    ? `${copy.filter_ingested}: ${filters.ingested_from || "…"} — ${filters.ingested_to || "…"}`
                    : null,
                  filters.tier && filters.tier !== "fit" ? `${copy.filter_priority_title}: ${filters.tier}` : null,
                  filters.platform ? `${copy.filter_chip_platform.replace("{n}", "…")}: ${filters.platform}` : null,
                  filters.price_min_rub
                    ? copy.filter_chip_price.replace("{price}", String(filters.price_min_rub))
                    : null,
                  filters.q ? `q: ${filters.q}` : null,
                  filters.sort && filters.sort !== "relevance" ? `sort: ${filters.sort}` : null,
                ]
                  .filter(Boolean)
                  .join(" · ") || copy.filter_date_any}
              </Typography>
            </Stack>
          </Box>
        </Stack>
      </Box>

      <Box sx={{ p: 2.5, borderTop: `1px solid ${stripe.border}` }}>
        {countState === "ok" && n === 0 ? (
          <Box sx={{ mb: 1.5 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {copy.export_empty_title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {copy.export_empty_body}
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" sx={{ mb: 1.5 }} color="text.secondary">
            {copy.export_count.replace("{n}", countState === "ok" ? String(n) : "…")}
          </Typography>
        )}
        <Button
          fullWidth
          variant="contained"
          disabled={!canDownload}
          onClick={() => void onDownload()}
        >
          {busy ? copy.export_download_busy : copy.export_download}
        </Button>
      </Box>
    </DetailDrawerShell>
  );
}

/** Build export prefill from the same inputs as App.inboxQuery(). */
export function buildExportPrefill(args: {
  query: InboxListQuery;
  ai_wrong?: boolean;
}): ExportPrefill {
  return {
    ...args.query,
    tier: args.query.tier ?? "fit",
    ai_wrong: args.ai_wrong,
  };
}
