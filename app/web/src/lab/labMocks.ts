export type LabPhase = "idle" | "running" | "done";
export type LabAiPhase = "idle" | "busy" | "done";

export type LabMockState = {
  phase: LabPhase;
  ai: LabAiPhase;
  groups: number;
  platforms: number;
  steps: number;
  listDone: number;
  listTotal: number;
  cardsDone: number;
  cardsTotal: number;
  counters: { L1: number; L2: number; L3: number; noise: number };
  pendingAi: number;
  manualSend: number;
  slotWhen: string;
};

export const LAB_IDLE: LabMockState = {
  phase: "idle",
  ai: "idle",
  groups: 6,
  platforms: 6,
  steps: 36,
  listDone: 0,
  listTotal: 0,
  cardsDone: 0,
  cardsTotal: 0,
  counters: { L1: 0, L2: 0, L3: 0, noise: 0 },
  pendingAi: 48,
  manualSend: 12,
  slotWhen: "пн, 14.09.2026, 14:30",
};

export const LAB_RUNNING: LabMockState = {
  ...LAB_IDLE,
  phase: "running",
  listDone: 14,
  listTotal: 36,
  cardsDone: 8,
  cardsTotal: 22,
  counters: { L1: 3, L2: 5, L3: 2, noise: 4 },
};

export const LAB_DONE: LabMockState = {
  ...LAB_IDLE,
  phase: "done",
  listDone: 36,
  listTotal: 36,
  cardsDone: 28,
  cardsTotal: 28,
  counters: { L1: 7, L2: 11, L3: 6, noise: 4 },
  pendingAi: 28,
  manualSend: 9,
};

export const LAB_AI_BUSY: LabMockState = {
  ...LAB_DONE,
  ai: "busy",
};

export const LAB_AI_DONE: LabMockState = {
  ...LAB_DONE,
  ai: "done",
  pendingAi: 0,
  counters: { L1: 7, L2: 11, L3: 6, noise: 4 },
};

export type LabPresetId = "idle" | "running" | "done" | "ai_busy" | "ai_done";

export const LAB_PRESETS: Record<LabPresetId, LabMockState> = {
  idle: LAB_IDLE,
  running: LAB_RUNNING,
  done: LAB_DONE,
  ai_busy: LAB_AI_BUSY,
  ai_done: LAB_AI_DONE,
};
