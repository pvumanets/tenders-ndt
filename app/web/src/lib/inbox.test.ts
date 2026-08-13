import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../copy";
import {
  UnauthorizedError,
  apiTierParam,
  buildInboxSearchParams,
  documentDownloadUrl,
  fetchInbox,
  mapRunStatus,
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
      log: [],
    });
    expect(status.list_done).toBe(12);
    expect(status.list_total).toBe(1000);
    expect(status.session).toBe("missing");
    expect(status.phase_label).toBe(copy.phase_list);
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
