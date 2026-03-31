import { AppShell } from "@/components/app-shell";

export default function Loading() {
  return (
    <AppShell>
      <section className="hero-panel placeholder-hero loading-panel">
        <div className="loading-block large" />
        <div className="loading-stats">
          <div className="loading-block medium" />
          <div className="loading-block medium" />
        </div>
      </section>

      <section className="placeholder-grid">
        <article className="panel loading-panel">
          <div className="loading-block medium" />
          <div className="loading-block small" />
          <div className="loading-block small" />
        </article>
        <article className="panel loading-panel">
          <div className="loading-block medium" />
          <div className="loading-block small" />
          <div className="loading-block small" />
        </article>
      </section>
    </AppShell>
  );
}