import { createFileRoute, Link } from "@tanstack/react-router";
import { Crosshair, MapPinned } from "lucide-react";
import { useCallback, useState } from "react";

export const Route = createFileRoute("/map")({
  component: MapTemplate,
});

function MapTemplate() {
  const [lat, setLat] = useState(12.9716);
  const [lon, setLon] = useState(77.5946);
  const [status, setStatus] = useState(
    "Tip: adjust coordinates below to match your location, then confirm.",
  );

  const setMarkerFromNumbers = useCallback((nextLat: number, nextLon: number, message?: string) => {
    setLat(nextLat);
    setLon(nextLon);
    setStatus(
      message
        ? `${message} Coordinates: ${nextLat.toFixed(6)}, ${nextLon.toFixed(6)}`
        : `Selected coordinates: ${nextLat.toFixed(6)}, ${nextLon.toFixed(6)}`,
    );
  }, []);

  function confirmLocation() {
    if (!window.opener) {
      setStatus("Open this map from registration (Choose on map).");
      return;
    }

    window.opener.postMessage(
      {
        lat,
        lon,
      },
      window.location.origin,
    );

    window.close();
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setStatus("Geolocation not supported.");
      return;
    }
    setStatus("Fetching your current location…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const glat = position.coords.latitude;
        const glon = position.coords.longitude;
        setMarkerFromNumbers(glat, glon, "Current location detected.");
      },
      () => setStatus("Could not access location. Adjust coordinates manually."),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-5xl px-4 py-8">
      <section className="rounded-2xl border bg-card p-5 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h1 className="flex items-center gap-2 text-xl font-semibold text-foreground">
            <MapPinned className="h-5 w-5 text-primary" />
            Select your location
          </h1>
          <Link to="/register" className="text-sm font-medium text-primary hover:underline">
            Back to register
          </Link>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-md border bg-muted px-3 py-2 text-sm font-semibold text-foreground hover:bg-muted/80"
            onClick={useCurrentLocation}
          >
            Use my current location
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm font-medium text-foreground hover:bg-accent"
            onClick={() => setMarkerFromNumbers(12.9716, 77.5946, "Default Bengaluru center.")}
          >
            <Crosshair className="h-4 w-4 text-primary" />
            Use Bengaluru default
          </button>
          <button
            type="button"
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
            onClick={confirmLocation}
          >
            Confirm location
          </button>
        </div>

        <div className="mt-4 grid gap-4 rounded-xl border bg-muted/35 p-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Latitude</label>
            <input
              type="number"
              step="0.000001"
              value={lat}
              onChange={(event) => {
                const next = Number(event.target.value);
                setLat(Number.isFinite(next) ? next : lat);
              }}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Longitude</label>
            <input
              type="number"
              step="0.000001"
              value={lon}
              onChange={(event) => {
                const next = Number(event.target.value);
                setLon(Number.isFinite(next) ? next : lon);
              }}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
            />
          </div>
        </div>

        <div className="mt-4 overflow-hidden rounded-xl border bg-background">
          <iframe
            title="Map preview"
            className="h-[420px] w-full"
            src={`https://www.openstreetmap.org/export/embed.html?bbox=${lon - 0.04}%2C${lat - 0.04}%2C${lon + 0.04}%2C${lat + 0.04}&layer=mapnik&marker=${lat}%2C${lon}`}
          />
        </div>

        <p
          id="status"
          className="mt-3 rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground"
        >
          {status}
        </p>
      </section>
    </main>
  );
}
