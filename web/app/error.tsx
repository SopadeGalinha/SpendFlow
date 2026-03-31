"use client";

import { useEffect } from "react";

import { AppShell } from "@/components/app-shell";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <AppShell>
      <section className="panel error-state-card">
        <p className="eyebrow">Data error</p>
        <h2>Something failed while preparing this screen.</h2>
        <p>
          The route is already structured to handle backend failures gracefully. You can retry the load without leaving the page.
        </p>
        <button type="button" className="pay-button" onClick={reset}>
          Retry
        </button>
      </section>
    </AppShell>
  );
}