import { createFileRoute, Link } from "@tanstack/react-router";
import { Building2, RefreshCw } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { apiUrl, postForm } from "@/lib/api";

type RequestStatus = "PENDING" | "ASSIGNED" | "IN_PROGRESS" | "COMPLETED" | "SKIPPED";

type MunicipalRequest = {
  id: number;
  decision: string;
  waste: number;
  delay: number;
  density: number;
  area: number;
  lat: number;
  lon: number;
  bin_lat: number | null;
  bin_lon: number | null;
  status: RequestStatus;
  priority: string;
  notes: string | null;
};

const STATUS_OPTIONS: RequestStatus[] = [
  "PENDING",
  "ASSIGNED",
  "IN_PROGRESS",
  "COMPLETED",
  "SKIPPED",
];

export const Route = createFileRoute("/municipal")({
  component: MunicipalDashboard,
});

function MunicipalDashboard() {
  const [requests, setRequests] = useState<MunicipalRequest[]>([]);
  const [filter, setFilter] = useState<"ALL" | RequestStatus>("ALL");
  const [loading, setLoading] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [statusDrafts, setStatusDrafts] = useState<Record<number, RequestStatus>>({});
  const [noteDrafts, setNoteDrafts] = useState<Record<number, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function fetchRequests() {
    setLoading(true);
    setError(null);
    try {
      const query = filter === "ALL" ? "" : `?status=${encodeURIComponent(filter)}`;
      const response = await fetch(apiUrl(`/api/municipal/requests${query}`), {
        headers: { Accept: "application/json" },
      });
      const data = (await response.json()) as unknown;
      if (!response.ok) {
        throw new Error("Failed to fetch municipal requests.");
      }
      if (!Array.isArray(data)) {
        throw new Error("Unexpected response for municipal requests.");
      }
      const parsed = data.filter(
        (row): row is MunicipalRequest =>
          typeof row === "object" &&
          row !== null &&
          typeof (row as { id?: unknown }).id === "number" &&
          typeof (row as { status?: unknown }).status === "string",
      );
      setRequests(parsed);
      const nextStatusDrafts: Record<number, RequestStatus> = {};
      const nextNoteDrafts: Record<number, string> = {};
      for (const req of parsed) {
        nextStatusDrafts[req.id] = req.status;
        nextNoteDrafts[req.id] = req.notes ?? "";
      }
      setStatusDrafts(nextStatusDrafts);
      setNoteDrafts(nextNoteDrafts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load requests.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchRequests();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function onUpdateStatus(event: FormEvent<HTMLFormElement>, requestId: number) {
    event.preventDefault();
    const nextStatus = statusDrafts[requestId];
    if (!nextStatus) {
      setError("Please choose a valid status.");
      return;
    }

    setSavingId(requestId);
    setError(null);
    setMessage(null);
    try {
      const formData = new FormData();
      formData.set("status", nextStatus);
      formData.set("notes", noteDrafts[requestId] ?? "");
      await postForm(`/api/municipal/requests/${requestId}/status`, formData);
      setMessage(`Request #${requestId} updated to ${nextStatus}.`);
      await fetchRequests();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-4 py-8">
      <div className="mb-4 flex justify-end gap-4">
        <Link to="/dashboard" className="text-sm text-muted-foreground hover:text-foreground hover:underline">
          User dashboard
        </Link>
        <Link to="/login" className="text-sm font-medium text-primary hover:underline">
          Sign out
        </Link>
      </div>

      <section className="rounded-2xl border bg-card p-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
              <Building2 className="h-5 w-5 text-primary" />
              Municipal dashboard
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Review auto-generated pickup tasks and update field execution status.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void fetchRequests()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium hover:bg-muted disabled:opacity-60"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-foreground" htmlFor="status-filter">
            Filter by status
          </label>
          <select
            id="status-filter"
            value={filter}
            onChange={(event) => setFilter(event.target.value as "ALL" | RequestStatus)}
            className="rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
          >
            <option value="ALL">All</option>
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {message ? (
          <p className="mt-4 rounded-md border bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p>
        ) : null}
        {error ? (
          <p className="mt-4 rounded-md border bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        ) : null}

        <div className="mt-6 overflow-x-auto rounded-xl border">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-muted/40">
              <tr className="text-left">
                <th className="px-3 py-3 font-semibold text-foreground">ID</th>
                <th className="px-3 py-3 font-semibold text-foreground">Decision</th>
                <th className="px-3 py-3 font-semibold text-foreground">Priority</th>
                <th className="px-3 py-3 font-semibold text-foreground">Inputs</th>
                <th className="px-3 py-3 font-semibold text-foreground">Coordinates</th>
                <th className="px-3 py-3 font-semibold text-foreground">Update status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-background">
              {loading ? (
                <tr>
                  <td className="px-3 py-4 text-muted-foreground" colSpan={6}>
                    Loading requests...
                  </td>
                </tr>
              ) : requests.length === 0 ? (
                <tr>
                  <td className="px-3 py-4 text-muted-foreground" colSpan={6}>
                    No municipal requests available.
                  </td>
                </tr>
              ) : (
                requests.map((req) => (
                  <tr key={req.id}>
                    <td className="px-3 py-3 font-medium text-foreground">#{req.id}</td>
                    <td className="px-3 py-3 text-foreground">{req.decision}</td>
                    <td className="px-3 py-3 text-foreground">{req.priority}</td>
                    <td className="px-3 py-3 text-muted-foreground">
                      W:{req.waste} D:{req.delay} PD:{req.density} A:{req.area}
                    </td>
                    <td className="px-3 py-3 text-muted-foreground">
                      <div>Input: {req.lat}, {req.lon}</div>
                      <div>
                        Bin:{" "}
                        {req.bin_lat !== null && req.bin_lon !== null
                          ? `${req.bin_lat}, ${req.bin_lon}`
                          : "Not available"}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <form
                        onSubmit={(event) => void onUpdateStatus(event, req.id)}
                        className="flex flex-col gap-2"
                      >
                        <select
                          value={statusDrafts[req.id] ?? req.status}
                          onChange={(event) =>
                            setStatusDrafts((prev) => ({
                              ...prev,
                              [req.id]: event.target.value as RequestStatus,
                            }))
                          }
                          className="rounded-md border bg-background px-2 py-1 text-xs"
                        >
                          {STATUS_OPTIONS.map((status) => (
                            <option key={status} value={status}>
                              {status}
                            </option>
                          ))}
                        </select>
                        <input
                          type="text"
                          placeholder="Notes (optional)"
                          value={noteDrafts[req.id] ?? ""}
                          onChange={(event) =>
                            setNoteDrafts((prev) => ({
                              ...prev,
                              [req.id]: event.target.value,
                            }))
                          }
                          className="rounded-md border bg-background px-2 py-1 text-xs"
                        />
                        <button
                          type="submit"
                          disabled={savingId === req.id}
                          className="rounded-md bg-primary px-2 py-1 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                        >
                          {savingId === req.id ? "Saving..." : "Save"}
                        </button>
                      </form>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
