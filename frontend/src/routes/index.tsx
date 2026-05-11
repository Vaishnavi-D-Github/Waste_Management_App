import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Leaf, LogIn } from "lucide-react";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  return (
    <main className="relative mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-10">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.20),_transparent_45%),radial-gradient(circle_at_bottom,_rgba(34,197,94,0.18),_transparent_40%)]" />
      <section className="mx-auto w-full max-w-3xl rounded-3xl border border-emerald-200/80 bg-card/95 p-10 text-center shadow-2xl backdrop-blur">
        <p className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-4 py-1 text-xs font-semibold text-emerald-800">
          <Leaf className="h-4 w-4" />
          Smart Waste Routing
        </p>
        <h1 className="mt-5 text-3xl font-bold tracking-tight text-foreground md:text-5xl">
          Waste Management, getting ready for the future
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-6 text-muted-foreground md:text-base">
          Plan cleaner, greener collection workflows with data-driven decision support built for
          next-generation urban waste management.
        </p>
        <div className="mt-8">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-700"
          >
            <LogIn className="h-4 w-4" />
            Sign in
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </main>
  );
}
