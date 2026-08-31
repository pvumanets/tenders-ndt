import type { ReactNode } from "react";
import { useState } from "react";
import { Alert, Box, FormControlLabel, Paper, Stack, Switch, Typography } from "@mui/material";
import type { PlatformRow, PlatformSession, ScheduleSettings, SearchGroup, TechStatus } from "../../types";
import { copy } from "../../copy";
import type { SearchGroupWrite } from "../../lib/inbox";
import { stripe } from "../../theme/palette";
import CookieJarUpload from "./CookieJarUpload";
import SearchGroupDrawer, {
  draftFromSearchGroup,
  emptyGroupDraft,
  parseGroupLines,
  type GroupDraft,
} from "./SearchGroupDrawer";
import SearchGroupList from "./SearchGroupList";
import SettingsSchedule from "./SettingsSchedule";
import TechDiagnostics from "./TechDiagnostics";
import { formatPlatformSessionLine } from "../../lib/inbox";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Box
      sx={{
        pb: 2.5,
        mb: 0.5,
        borderBottom: `1px solid ${stripe.border}`,
      }}
    >
      <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
        {title}
      </Typography>
      {children}
    </Box>
  );
}

export default function SettingsPanel({
  status,
  schedule,
  groups,
  platforms,
  locked = false,
  groupError = null,
  highlightSessions = false,
  onScheduleSaved,
  onToggleQueue,
  onTogglePlatform,
  onSaveGroup,
  onDeleteGroup,
  onCookieSession,
}: {
  status: TechStatus;
  schedule: ScheduleSettings;
  groups: SearchGroup[];
  platforms: PlatformRow[];
  locked?: boolean;
  groupError?: string | null;
  highlightSessions?: boolean;
  onScheduleSaved: (next: ScheduleSettings) => void;
  onToggleQueue: (group: SearchGroup, inQueue: boolean) => void;
  onTogglePlatform: (platform: PlatformRow, enabled: boolean) => void;
  onSaveGroup: (id: string | undefined, body: SearchGroupWrite) => Promise<void>;
  onDeleteGroup: (group: SearchGroup) => void;
  onCookieSession: (platformId: string, session: PlatformSession) => void;
}) {
  const [draft, setDraft] = useState<GroupDraft | null>(null);
  const [saving, setSaving] = useState(false);
  const configLocked = locked || saving;
  const queuedGroups = groups.filter((row) => row.in_queue).length;
  const enabledPlatforms = platforms.filter((row) => row.enabled).length;
  const nextSort = groups.reduce((max, row) => Math.max(max, row.sort_order), -1) + 1;
  const diagnosticsForceOpen = status.phase === "error";
  const emptyPriority =
    groups.length === 0
      ? "groups"
      : enabledPlatforms === 0
        ? "platforms"
        : queuedGroups === 0
          ? "queued"
          : null;

  async function submitDraft() {
    if (!draft) return;
    const queries = parseGroupLines(draft.queriesText);
    if (!draft.name.trim() || queries.length === 0) return;
    setSaving(true);
    try {
      await onSaveGroup(draft.id, {
        name: draft.name.trim(),
        queries,
        exclude: parseGroupLines(draft.excludeText),
        limit_n: Math.max(0, Number(draft.limit_n) || 0),
        in_queue: draft.in_queue,
        sort_order: draft.sort_order,
      });
      setDraft(null);
    } catch {
      /* parent sets groupError */
    } finally {
      setSaving(false);
    }
  }

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        border: `1px solid ${stripe.border}`,
        borderRadius: 1,
        maxWidth: 840,
      }}
    >
      <Stack spacing={0}>
        <Section title={copy.settings_section_schedule}>
          <SettingsSchedule
            schedule={schedule}
            status={status}
            locked={configLocked}
            onSaved={onScheduleSaved}
          />
        </Section>

        <Section title={copy.settings_section_platforms}>
          {emptyPriority === "platforms" ? (
            <Alert severity="info" sx={{ mb: 1 }}>
              <Typography variant="body2">{copy.platforms_none_enabled}</Typography>
              <Typography variant="caption" sx={{ display: "block" }}>
                {copy.platforms_none_enabled_body}
              </Typography>
            </Alert>
          ) : null}
          {platforms.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {copy.platforms_none_enabled}
            </Typography>
          ) : (
            <Stack spacing={1}>
              {platforms.map((platform) => {
                const badSession =
                  platform.enabled &&
                  (platform.session === "missing" || platform.session === "expired");
                return (
                  <Box
                    key={platform.platform_id}
                    sx={{
                      py: 0.75,
                      px: 0.5,
                      borderBottom: `1px solid ${stripe.border}`,
                      bgcolor:
                        highlightSessions && badSession ? stripe.blurpleSoft : undefined,
                    }}
                  >
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                      <Typography sx={{ flex: 1, minWidth: 0 }} noWrap>
                        {platform.name}
                      </Typography>
                      <FormControlLabel
                        sx={{ mr: 0, flexShrink: 0 }}
                        control={
                          <Switch
                            size="small"
                            checked={platform.enabled}
                            disabled={configLocked}
                            onChange={(_, checked) => onTogglePlatform(platform, checked)}
                            slotProps={{
                              input: {
                                "aria-label": `${copy.platform_participate}: ${platform.name}`,
                              },
                            }}
                          />
                        }
                        label={copy.platform_participate}
                      />
                    </Stack>
                    <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                      {formatPlatformSessionLine(platform)}
                    </Typography>
                    <CookieJarUpload
                      platformId={platform.platform_id}
                      locked={configLocked}
                      session={platform.session}
                      onUploaded={(session) => onCookieSession(platform.platform_id, session)}
                    />
                  </Box>
                );
              })}
            </Stack>
          )}
        </Section>

        <Section title={copy.settings_section_groups}>
          {groupError ? (
            <Alert severity="error" sx={{ mb: 1 }}>
              {groupError}
            </Alert>
          ) : null}
          {emptyPriority === "queued" ? (
            <Alert severity="info" sx={{ mb: 1 }}>
              <Typography variant="body2">{copy.groups_none_queued}</Typography>
              <Typography variant="caption" sx={{ display: "block" }}>
                {copy.groups_none_queued_body}
              </Typography>
            </Alert>
          ) : null}
          <SearchGroupList
            groups={groups}
            locked={configLocked}
            draftOpen={draft !== null}
            onAdd={() => setDraft(emptyGroupDraft(nextSort))}
            onEdit={(group) => setDraft(draftFromSearchGroup(group))}
            onDelete={onDeleteGroup}
            onToggleQueue={onToggleQueue}
          />
          {draft ? (
            <SearchGroupDrawer
              draft={draft}
              saving={saving}
              onChange={setDraft}
              onSave={() => void submitDraft()}
              onClose={() => setDraft(null)}
            />
          ) : null}
        </Section>

        <Box sx={{ pt: 2 }}>
          <TechDiagnostics
            status={status}
            forceOpen={diagnosticsForceOpen}
            title={copy.settings_section_diagnostics}
          />
        </Box>
      </Stack>
    </Paper>
  );
}
