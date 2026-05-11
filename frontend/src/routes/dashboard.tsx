import { createFileRoute, Link } from "@tanstack/react-router";
import { BarChart3, Clock3, MapPin } from "lucide-react";
import { useState, type FormEvent, type ReactNode } from "react";
import { apiUrl, postForm } from "@/lib/api";

type Decision = "WAIT" | "MONITOR" | "DISPOSE" | null;
type Recommendation = { en: string; kn: string };
type LanguageMode = "en" | "kn" | "both";
type MunicipalRequestSummary = {
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
  status: string;
  priority: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export const Route = createFileRoute("/dashboard")({
  component: DashboardTemplate,
});

function DashboardTemplate() {
  const [waste, setWaste] = useState("1");
  const [delay, setDelay] = useState("0");
  const [density, setDensity] = useState("2");
  const [area, setArea] = useState("0");
  const [lat, setLat] = useState("12.9716");
  const [lon, setLon] = useState("77.5946");

  const [decision, setDecision] = useState<Decision>(null);
  const [binLat, setBinLat] = useState<number | null>(null);
  const [binLon, setBinLon] = useState<number | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [municipalRequestId, setMunicipalRequestId] = useState<number | null>(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [showMunicipalQueue, setShowMunicipalQueue] = useState(false);
  const [languageMode, setLanguageMode] = useState<LanguageMode>("both");
  const [municipalRequests, setMunicipalRequests] = useState<MunicipalRequestSummary[]>([]);
  const [municipalLoading, setMunicipalLoading] = useState(false);
  const [municipalError, setMunicipalError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData();
    formData.set("waste", waste);
    formData.set("delay", delay);
    formData.set("density", density);
    formData.set("area", area);
    formData.set("lat", lat);
    formData.set("lon", lon);

    try {
      const data = await postForm("/api/predict", formData);
      const obj = data && typeof data === "object" ? (data as Record<string, unknown>) : null;
      const d = typeof obj?.decision === "string" ? obj.decision : null;
      const blRaw = obj?.bin_lat;
      const brRaw = obj?.bin_lon;
      const recRaw = obj?.recommendations;
      const municipalRaw = obj?.municipal_request_id;
      const bl = typeof blRaw === "number" ? blRaw : blRaw !== null ? Number(blRaw) : null;
      const br = typeof brRaw === "number" ? brRaw : brRaw !== null ? Number(brRaw) : null;
      const municipalId =
        typeof municipalRaw === "number"
          ? municipalRaw
          : municipalRaw !== null && municipalRaw !== undefined
            ? Number(municipalRaw)
            : null;
      const recs = Array.isArray(recRaw)
        ? recRaw.filter(
            (entry): entry is Recommendation =>
              typeof entry === "object" &&
              entry !== null &&
              typeof (entry as { en?: unknown }).en === "string" &&
              typeof (entry as { kn?: unknown }).kn === "string",
          )
        : [];

      setDecision(d === "WAIT" || d === "MONITOR" || d === "DISPOSE" ? d : null);
      setBinLat(bl !== null && Number.isFinite(bl) ? bl : null);
      setBinLon(br !== null && Number.isFinite(br) ? br : null);
      setRecommendations(recs);
      setMunicipalRequestId(
        municipalId !== null && Number.isFinite(municipalId) ? Math.trunc(municipalId) : null,
      );
      setLanguageMode("both");
      setShowRecommendations(recs.length > 0);

      if (!d) {
        setError("Unexpected response from server.");
      }
    } catch (err) {
      setDecision(null);
      setBinLat(null);
      setBinLon(null);
      setRecommendations([]);
      setMunicipalRequestId(null);
      setShowRecommendations(false);
      setError(err instanceof Error ? err.message : "Prediction failed.");
    } finally {
      setLoading(false);
    }
  }

  async function openMunicipalQueue() {
    setShowMunicipalQueue(true);
    setMunicipalLoading(true);
    setMunicipalError(null);

    try {
      const response = await fetch(apiUrl("/api/municipal/requests"), {
        headers: { Accept: "application/json" },
      });
      const data = (await response.json()) as unknown;
      if (!response.ok) {
        throw new Error("Failed to load municipal queue.");
      }
      if (!Array.isArray(data)) {
        throw new Error("Unexpected response for municipal queue.");
      }
      const parsed = data.filter(
        (row): row is MunicipalRequestSummary =>
          typeof row === "object" &&
          row !== null &&
          typeof (row as { id?: unknown }).id === "number" &&
          typeof (row as { status?: unknown }).status === "string" &&
          typeof (row as { created_at?: unknown }).created_at === "string" &&
          typeof (row as { updated_at?: unknown }).updated_at === "string",
      );
      setMunicipalRequests(parsed);
    } catch (err) {
      setMunicipalRequests([]);
      setMunicipalError(err instanceof Error ? err.message : "Unable to load municipal queue.");
    } finally {
      setMunicipalLoading(false);
    }
  }

  const badgeClass =
    decision === "DISPOSE"
      ? "bg-red-100 text-red-700"
      : decision === "MONITOR"
        ? "bg-amber-100 text-amber-700"
        : decision === "WAIT"
          ? "bg-sky-100 text-sky-700"
          : "";

  const mapEmbedSrc =
    decision === "DISPOSE" && binLat !== null && binLon !== null
      ? `https://www.openstreetmap.org/export/embed.html?bbox=${binLon - 0.03}%2C${binLat - 0.03}%2C${binLon + 0.03}%2C${binLat + 0.03}&layer=mapnik&marker=${binLat}%2C${binLon}`
      : null;

  return (
    <main className="mx-auto min-h-screen w-full max-w-5xl px-4 py-8">
      <div className="mb-4 flex justify-end gap-4">
        <Link
          to="/register"
          className="text-sm text-muted-foreground hover:text-foreground hover:underline"
        >
          Register
        </Link>
        <Link to="/login" className="text-sm font-medium text-primary hover:underline">
          Sign out
        </Link>
      </div>

      <section className="rounded-2xl border bg-card p-6 shadow-xl">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
          <BarChart3 className="h-5 w-5 text-primary" />
          Waste routing dashboard
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Submit situational inputs — results come from your FastAPI Apriori engine.
        </p>

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <form className="space-y-4 rounded-xl border bg-muted/35 p-4" onSubmit={onSubmit}>
            <FieldLabel label="Waste level">
              <select
                value={waste}
                onChange={(event) => setWaste(event.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
                required
              >
                <option value="0">Low</option>
                <option value="1">Medium</option>
                <option value="2">High</option>
              </select>
            </FieldLabel>

            <FieldLabel label="Delay (days)">
              <input
                type="number"
                min={0}
                value={delay}
                onChange={(event) => setDelay(event.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
                required
              />
            </FieldLabel>

            <FieldLabel label="Population density">
              <select
                value={density}
                onChange={(event) => setDensity(event.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
                required
              >
                <option value="0">Low</option>
                <option value="1">Medium</option>
                <option value="2">High</option>
              </select>
            </FieldLabel>

            <FieldLabel label="Area type">
              <select
                value={area}
                onChange={(event) => setArea(event.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
                required
              >
                <option value="0">Residential</option>
                <option value="1">Commercial</option>
              </select>
            </FieldLabel>

            <div className="grid gap-4 sm:grid-cols-2">
              <FieldLabel label="Latitude">
                <input
                  type="text"
                  inputMode="decimal"
                  value={lat}
                  onChange={(event) => setLat(event.target.value)}
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
                  required
                />
              </FieldLabel>
              <FieldLabel label="Longitude">
                <input
                  type="text"
                  inputMode="decimal"
                  value={lon}
                  onChange={(event) => setLon(event.target.value)}
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
                  required
                />
              </FieldLabel>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
            >
              {loading ? "Running analysis…" : "Run analysis"}
            </button>
          </form>

          <aside className="rounded-xl border bg-background p-5">
            <p className="text-sm font-medium text-muted-foreground">Apriori routing result</p>

            {error ? (
              <p className="mt-3 text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}

            {!decision && !error ? (
              <p className="mt-3 text-sm text-muted-foreground">
                Submit the form to get a WAIT / MONITOR / DISPOSE decision.
              </p>
            ) : null}

            {decision ? (
              <>
                <div
                  className={`mt-3 inline-flex rounded-full px-3 py-1 text-sm font-bold ${badgeClass}`}
                >
                  {decision}
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  {decision === "DISPOSE" && "Nearest disposal point is shown on the map below."}
                  {decision === "MONITOR" &&
                    "Schedule monitoring before scheduling collection operations."}
                  {decision === "WAIT" && "No immediate action required under current rules."}
                </p>
              </>
            ) : null}

            {decision === "DISPOSE" && binLat !== null && binLon !== null && mapEmbedSrc ? (
              <div className="mt-4 rounded-lg border bg-muted/30 p-3">
                <p className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <MapPin className="h-4 w-4 text-primary" />
                  Nearest disposal site
                </p>
                <div className="mt-3 overflow-hidden rounded-md border bg-background">
                  <iframe
                    title="Nearest disposal location"
                    className="h-[280px] w-full"
                    src={mapEmbedSrc}
                  />
                </div>
              </div>
            ) : null}

            {decision === "DISPOSE" && (binLat === null || binLon === null) && !loading ? (
              <p className="mt-3 text-sm text-destructive">
                No disposal locations available in the dataset.
              </p>
            ) : null}

            {municipalRequestId !== null ? (
              <p className="mt-3 rounded-md border bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-700">
                Disposal request saved to the municipal queue: #{municipalRequestId}
              </p>
            ) : null}

            <button
              type="button"
              onClick={() => void openMunicipalQueue()}
              className="mt-3 w-full rounded-md border bg-background px-4 py-2 text-sm font-semibold text-foreground hover:bg-muted/40"
            >
              View municipal queue and delays
            </button>

            {recommendations.length > 0 ? (
              <button
                type="button"
                onClick={() => setShowRecommendations(true)}
                className="mt-4 w-full rounded-md border bg-muted/30 px-4 py-2 text-sm font-semibold text-foreground hover:bg-muted/50"
              >
                View best-practice recommendations
              </button>
            ) : null}
          </aside>
        </div>
      </section>

      {showRecommendations ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-2xl rounded-xl border bg-background p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-foreground">Recommended best practices</h2>
                <p className="text-sm text-muted-foreground">
                  English and Kannada guidance based on your current inputs and result.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowRecommendations(false)}
                className="rounded-md border px-3 py-1 text-sm font-medium hover:bg-muted"
              >
                Close
              </button>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setLanguageMode("en")}
                className={`rounded-md border px-3 py-1 text-sm font-medium ${
                  languageMode === "en" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setLanguageMode("kn")}
                className={`rounded-md border px-3 py-1 text-sm font-medium ${
                  languageMode === "kn" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                }`}
              >
                Kannada
              </button>
              <button
                type="button"
                onClick={() => setLanguageMode("both")}
                className={`rounded-md border px-3 py-1 text-sm font-medium ${
                  languageMode === "both"
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
              >
                Both
              </button>
            </div>

            <ul className="mt-4 max-h-[55vh] space-y-3 overflow-y-auto pr-1">
              {recommendations.map((tip, index) => (
                <li key={`${tip.en}-${index}`} className="rounded-md border bg-muted/20 p-3">
                  {languageMode === "en" || languageMode === "both" ? (
                    <p className="text-sm font-medium text-foreground">{tip.en}</p>
                  ) : null}
                  {languageMode === "kn" || languageMode === "both" ? (
                    <p
                      className={`text-sm text-muted-foreground ${
                        languageMode === "both" ? "mt-1" : ""
                      }`}
                    >
                      {tip.kn}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}

      {showMunicipalQueue ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-4xl rounded-xl border bg-background p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-foreground">Municipal queue visibility</h2>
                <p className="text-sm text-muted-foreground">
                  Users can see generated municipal tasks and spot which requests are still delayed.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowMunicipalQueue(false)}
                className="rounded-md border px-3 py-1 text-sm font-medium hover:bg-muted"
              >
                Close
              </button>
            </div>

            {municipalError ? (
              <p className="mt-4 rounded-md border bg-red-50 px-3 py-2 text-sm text-red-700">
                {municipalError}
              </p>
            ) : null}

            <div className="mt-4 max-h-[65vh] space-y-3 overflow-y-auto pr-1">
              {municipalLoading ? (
                <p className="rounded-md border bg-muted/20 px-3 py-4 text-sm text-muted-foreground">
                  Loading municipal queue...
                </p>
              ) : municipalRequests.length === 0 ? (
                <p className="rounded-md border bg-muted/20 px-3 py-4 text-sm text-muted-foreground">
                  No municipal tasks have been created yet.
                </p>
              ) : (
                municipalRequests.map((request) => {
                  const isDelayed =
                    request.status !== "COMPLETED" &&
                    request.status !== "SKIPPED" &&
                    request.delay >= 2;

                  return (
                    <article
                      key={request.id}
                      className="rounded-lg border bg-muted/15 p-4 shadow-sm"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-foreground">
                            Request #{request.id}
                          </p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            Created {formatDateTime(request.created_at)} • Last updated{" "}
                            {formatDateTime(request.updated_at)}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Badge>{request.status}</Badge>
                          <Badge tone={request.priority === "HIGH" ? "danger" : "neutral"}>
                            {request.priority} priority
                          </Badge>
                          <Badge tone={isDelayed ? "warning" : "success"}>
                            {isDelayed ? "Delay hotspot" : "Moving normally"}
                          </Badge>
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3 text-sm text-muted-foreground md:grid-cols-2">
                        <div className="rounded-md border bg-background p-3">
                          <p className="font-medium text-foreground">Operational inputs</p>
                          <p className="mt-2">
                            Decision: {request.decision} • Waste: {wasteLabel(request.waste)} •
                            Density: {densityLabel(request.density)}
                          </p>
                          <p className="mt-1">
                            Area: {areaLabel(request.area)} • Reported delay: {request.delay} day
                            {request.delay === 1 ? "" : "s"}
                          </p>
                        </div>

                        <div className="rounded-md border bg-background p-3">
                          <p className="font-medium text-foreground">Location trace</p>
                          <p className="mt-2">User point: {request.lat}, {request.lon}</p>
                          <p className="mt-1">
                            Assigned bin:{" "}
                            {request.bin_lat !== null && request.bin_lon !== null
                              ? `${request.bin_lat}, ${request.bin_lon}`
                              : "Not assigned"}
                          </p>
                        </div>
                      </div>

                      {request.notes ? (
                        <p className="mt-3 rounded-md border bg-amber-50 px-3 py-2 text-xs text-amber-800">
                          Municipal note: {request.notes}
                        </p>
                      ) : null}

                      {isDelayed ? (
                        <p className="mt-3 flex items-center gap-2 text-sm font-medium text-amber-700">
                          <Clock3 className="h-4 w-4" />
                          This request is still open after a reported delay of {request.delay} days.
                        </p>
                      ) : null}
                    </article>
                  );
                })
              )}
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}

function FieldLabel({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-foreground">{label}</span>
      {children}
    </label>
  );
}

function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
}) {
  const toneClass =
    tone === "danger"
      ? "bg-red-100 text-red-700"
      : tone === "warning"
        ? "bg-amber-100 text-amber-700"
        : tone === "success"
          ? "bg-emerald-100 text-emerald-700"
          : "bg-slate-100 text-slate-700";

  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${toneClass}`}>{children}</span>
  );
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function wasteLabel(value: number) {
  return value === 2 ? "High" : value === 1 ? "Medium" : "Low";
}

function densityLabel(value: number) {
  return value === 2 ? "High" : value === 1 ? "Medium" : "Low";
}

function areaLabel(value: number) {
  return value === 1 ? "Commercial" : "Residential";
}
