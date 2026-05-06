import { createFileRoute, Link } from "@tanstack/react-router";
import { MapPin, UserPlus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { postForm } from "@/lib/api";

export const Route = createFileRoute("/register")({
  component: RegisterTemplate,
});

function RegisterTemplate() {
  const [lat, setLat] = useState<string>("");
  const [lon, setLon] = useState<string>("");
  const [coordsHint, setCoordsHint] = useState("No location selected yet.");
  const [feedback, setFeedback] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) return;
      const data = event.data as { lat?: unknown; lon?: unknown };
      if (typeof data.lat === "number" && typeof data.lon === "number") {
        const la = data.lat.toFixed(6);
        const lo = data.lon.toFixed(6);
        setLat(la);
        setLon(lo);
        setCoordsHint(`Selected coordinates: ${la}, ${lo}`);
        setFeedback({ kind: "ok", text: "Location selected successfully." });
      }
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  function openMap() {
    window.open("/map", "Map", "width=950,height=650,resizable=yes");
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    const form = event.currentTarget;
    const username = String(new FormData(form).get("username") || "").trim();
    const password = String(new FormData(form).get("password") || "");

    if (!username || !password) {
      setFeedback({ kind: "err", text: "Username and password are required." });
      return;
    }
    if (!lat || !lon) {
      setFeedback({ kind: "err", text: "Please choose your location from the map." });
      return;
    }

    const formData = new FormData();
    formData.set("username", username);
    formData.set("password", password);
    formData.set("latitude", lat);
    formData.set("longitude", lon);

    setLoading(true);
    try {
      await postForm("/api/register", formData);
      setFeedback({ kind: "ok", text: "Registered successfully. You can now sign in." });
      form.reset();
      setLat("");
      setLon("");
      setCoordsHint("No location selected yet.");
    } catch (err) {
      setFeedback({
        kind: "err",
        text: err instanceof Error ? err.message : "Registration failed.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl items-center px-4 py-10">
      <section className="w-full rounded-2xl border bg-card p-8 shadow-xl">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
          <UserPlus className="h-5 w-5 text-primary" />
          Create your account
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Register and attach a location for pickup coordination.
        </p>

        <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
          <div className="md:col-span-1">
            <label className="mb-1 block text-sm font-medium text-foreground" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              name="username"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
              placeholder="Choose username"
              type="text"
              required
              autoComplete="username"
            />
          </div>
          <div className="md:col-span-1">
            <label className="mb-1 block text-sm font-medium text-foreground" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              name="password"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
              placeholder="Choose password"
              type="password"
              required
              autoComplete="new-password"
            />
          </div>
          <div className="rounded-xl border bg-muted/40 p-4 md:col-span-2">
            <p className="mb-3 text-sm font-medium text-foreground">Location</p>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={openMap}
                className="inline-flex items-center gap-2 rounded-md border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-accent"
              >
                <MapPin className="h-4 w-4 text-primary" />
                Choose on map
              </button>
            </div>
            <p className="mt-3 text-sm text-muted-foreground">{coordsHint}</p>
          </div>
          <div className="md:col-span-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
            >
              {loading ? "Registering…" : "Register"}
            </button>
          </div>
        </form>

        {feedback ? (
          <p
            className={`mt-3 text-sm ${feedback.kind === "err" ? "text-destructive" : "text-green-700"}`}
            role="status"
          >
            {feedback.text}
          </p>
        ) : null}

        <p className="mt-5 text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
