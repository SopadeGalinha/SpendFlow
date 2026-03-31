type FeaturePlaceholderProps = {
  eyebrow: string;
  title: string;
  description: string;
  primaryMetric: string;
  secondaryMetric: string;
};

export function FeaturePlaceholder({
  eyebrow,
  title,
  description,
  primaryMetric,
  secondaryMetric,
}: FeaturePlaceholderProps) {
  return (
    <>
      <section className="hero-panel placeholder-hero">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
          <p className="hero-copy">{description}</p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Primary signal</span>
            <strong>{primaryMetric}</strong>
          </div>
          <div>
            <span>Secondary signal</span>
            <strong>{secondaryMetric}</strong>
          </div>
        </div>
      </section>

      <section className="placeholder-grid">
        <article className="panel placeholder-card">
          <p className="eyebrow">Structure</p>
          <h3>Route is ready</h3>
          <p>
            This page now has a real Next.js route and shared app shell, so the
            next step is replacing the placeholder with API-backed content.
          </p>
        </article>

        <article className="panel placeholder-card">
          <p className="eyebrow">Next build step</p>
          <h3>Connect backend data</h3>
          <p>
            Keep presentation separate from data loading. This route is ready
            for a dedicated query layer and focused components.
          </p>
        </article>
      </section>
    </>
  );
}