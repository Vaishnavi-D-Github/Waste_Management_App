import { createFileRoute, Link } from "@tanstack/react-router";
import { BarChart3, MapPin } from "lucide-react";
import { useState, type FormEvent, type ReactNode } from "react";
import { postForm } from "@/lib/api";

type Decision = "WAIT" | "MONITOR" | "DISPOSE" | null;

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
      const bl = typeof blRaw === "number" ? blRaw : blRaw !== null ? Number(blRaw) : null;
      const br = typeof brRaw === "number" ? brRaw : brRaw !== null ? Number(brRaw) : null;

      setDecision(d === "WAIT" || d === "MONITOR" || d === "DISPOSE" ? d : null);
      setBinLat(bl !== null && Number.isFinite(bl) ? bl : null);
      setBinLon(br !== null && Number.isFinite(br) ? br : null);

      if (!d) {
        setError("Unexpected response from server.");
      }
    } catch (err) {
      setDecision(null);
      setBinLat(null);
      setBinLon(null);
      setError(err instanceof Error ? err.message : "Prediction failed.");
    } finally {
      setLoading(false);
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
          </aside>
        </div>
      </section>
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
