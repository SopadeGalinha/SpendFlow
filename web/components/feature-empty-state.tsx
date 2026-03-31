type FeatureEmptyStateProps = {
  eyebrow: string;
  title: string;
  description: string;
};

export function FeatureEmptyState({
  eyebrow,
  title,
  description,
}: FeatureEmptyStateProps) {
  return (
    <article className="panel empty-state-card">
      <p className="eyebrow">{eyebrow}</p>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}