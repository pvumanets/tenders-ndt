import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../copy";
import {
  UnauthorizedError,
  apiTierParam,
  buildInboxSearchParams,
  documentDownloadUrl,
  fetchInbox,
  mapRunStatus,
  runControlMessage,
  startRun,
  stopRun,
} from "./inbox";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiTierParam", () => {
  it("sends fit when none or many selected", () => {
    expect(apiTierParam([])).toBe("fit");
    expect(apiTierParam(["L1", "L2"])).toBe("fit");
  });

  it("sends the single selected tier", () => {
    expect(apiTierParam(["L2"])).toBe("L2");
  });
});

describe("buildInboxSearchParams", () => {
  it("omits optional empty filters", () => {
    const params = buildInboxSearchParams({ tier: "fit" });
    expect(params.get("tier")).toBe("fit");
    expect(params.get("unread")).toBeNull();
    expect(params.get("q")).toBeNull();
    expect(params.get("deadline_from")).toBeNull();
  });

  it("sets unread, q and dates", () => {
    const params = buildInboxSearchParams({
      unread: true,
      tier: "L1",
      q: "узк",
      deadline_from: "2026-08-13",
      deadline_to: "2026-08-20",
    });
    expect(params.get("unread")).toBe("true");
    expect(params.get("tier")).toBe("L1");
    expect(params.get("q")).toBe("узк");
    expect(params.get("deadline_from")).toBe("2026-08-13");
    expect(params.get("deadline_to")).toBe("2026-08-20");
  });
});

describe("mapRunStatus", () => {
  it("maps list_n/list_limit and missing_cookies", () => {
    const status = mapRunStatus({
      phase: "P1",
      running: true,
      list_n: 12,
      list_limit: 1000,
      cards_done: 0,
      cards_total: 18,
      session: "missing_cookies",
      run_dir: "/data/runs",
      counters: { L1: 1, L2: 2, L3: 3, noise: 4 },
      run_report: { new: 2, already: 5, updated: 1, expired: 3 },
      queue: [{ id: "s1", name: "РосТендер НК", platform_id: "rostender", status: "running" }],
      queue_index: 0,
      queue_total: 1,
      current_search_name: "РосТендер НК",
      log: [],
    });
    expect(status.list_done).toBe(12);
    expect(status.list_total).toBe(1000);
    expect(status.session).toBe("missing");
    expect(status.phase_label).toBe(copy.phase_list);
    expect(status.queue).toHaveLength(1);
    expect(status.current_search_name).toBe("РосТендер НК");
    expect(status.run_report).toEqual({ new: 2, already: 5, updated: 1, expired: 3 });
  });

  it("defaults run_report when missing", () => {
    const status = mapRunStatus({ phase: "done", running: false });
    expect(status.run_report).toEqual({ new: 0, already: 0, updated: 0, expired: 0 });
  });

  it("maps group×platform queue fields", () => {
    const status = mapRunStatus({
      phase: "P1",
      running: true,
      queue: [
        {
          id: "step-1",
          name: "методы",
          group_id: "g1",
          group_name: "методы",
          platform_id: "tender-pro",
          status: "running",
        },
      ],
      queue_index: 0,
      queue_total: 1,
      current_group_id: "g1",
      current_platform_id: "tender-pro",
      current_search_name: "методы",
    });
    expect(status.queue[0].group_name).toBe("методы");
    expect(status.queue[0].platform_id).toBe("tender-pro");
    expect(status.current_group_id).toBe("g1");
    expect(status.current_platform_id).toBe("tender-pro");
  });
});

describe("documentDownloadUrl", () => {
  it("encodes id and filename", () => {
    expect(documentDownloadUrl("45289101", "ТЗ.pdf")).toBe(
      "/api/inbox/45289101/documents/%D0%A2%D0%97.pdf",
    );
  });
});

describe("fetchInbox", () => {
  it("throws UnauthorizedError on 401", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ status: 401, ok: false, json: async () => ({}) }),
    );
    await expect(fetchInbox({ tier: "fit" })).rejects.toBeInstanceOf(UnauthorizedError);
  });

  it("normalizes list items without documents", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 200,
        ok: true,
        json: async () => ({
          items: [
            {
              tender_id: "1",
              title: "УЗК",
              customer_name: null,
              score: 7,
              tier: "L1",
              viewed: false,
            },
          ],
          total: 1,
        }),
      }),
    );
    const items = await fetchInbox({ tier: "fit" });
    expect(items).toHaveLength(1);
    expect(items[0].customer_name).toBe("");
    expect(items[0].documents).toEqual([]);
    expect(items[0].source_platform_id).toBe("rostender");
  });
});

describe("startRun / stopRun", () => {
  it("posts empty json to start", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ status: 200, ok: true, json: async () => ({ ok: true }) });
    vi.stubGlobal("fetch", fetchMock);
    await startRun();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/run/start",
      expect.objectContaining({ method: "POST", credentials: "include", body: "{}" }),
    );
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({});
  });

  it("maps already_running and missing_cookies", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 409,
        ok: false,
        json: async () => ({ detail: "already_running" }),
      }),
    );
    await expect(startRun()).rejects.toMatchObject({ code: "already_running" });

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 400,
        ok: false,
        json: async () => ({ detail: "missing_cookies" }),
      }),
    );
    await expect(startRun()).rejects.toMatchObject({ code: "missing_cookies" });

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 400,
        ok: false,
        json: async () => ({ detail: "empty_queue" }),
      }),
    );
    await expect(startRun()).rejects.toMatchObject({ code: "empty_queue" });
    expect(runControlMessage("empty_queue")).toBe(copy.run_error_empty_queue);
  });

  it("posts stop", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ status: 200, ok: true, json: async () => ({ ok: true }) });
    vi.stubGlobal("fetch", fetchMock);
    await stopRun();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/run/stop",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });
});
