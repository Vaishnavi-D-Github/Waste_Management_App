import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { LogIn } from "lucide-react";
import { useState, type FormEvent } from "react";
import { postForm } from "@/lib/api";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    setMessage(null);
    setLoading(true);
    try {
      await postForm("/api/login", formData);
      navigate({ to: "/dashboard" });
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-4 py-10">
      <section className="w-full rounded-2xl border bg-card p-8 shadow-xl">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
          <LogIn className="h-6 w-6 text-primary" />
          Welcome back
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign in to open the waste routing dashboard.
        </p>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              autoComplete="username"
              placeholder="Enter username"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              autoComplete="current-password"
              placeholder="Enter password"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-primary/20 transition focus:ring-4"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {message ? (
          <p className="mt-3 text-sm text-destructive" role="alert">
            {message}
          </p>
        ) : null}

        <p className="mt-6 text-center text-sm text-muted-foreground">
          New here?{" "}
          <Link to="/register" className="font-semibold text-primary hover:underline">
            Create account
          </Link>
        </p>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          <Link to="/" className="text-primary hover:underline">
            Home
          </Link>
        </p>
      </section>
    </main>
  );
}
