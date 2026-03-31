"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import type { CurrentUserProfile } from "@/lib/auth";
import { navigation } from "@/lib/dashboard-data";
import { SHELL_TOAST_EVENT, type ShellToastPayload } from "@/lib/ui-feedback";

type AppShellProps = {
  children: React.ReactNode;
  currentUser?: CurrentUserProfile;
};

type UiDensity = "comfortable" | "compact";

type ShellToast = ShellToastPayload & {
  id: number;
};

const QUICK_ADD_ACTIONS = [
  {
    href: "/accounts",
    title: "Add account",
    description: "Create a new checking or savings account.",
  },
  {
    href: "/transactions",
    title: "Add transaction",
    description: "Post a new income or expense entry.",
  },
  {
    href: "/budget",
    title: "Add budget",
    description: "Create a category spending guardrail.",
  },
  {
    href: "/recurring",
    title: "Add recurring expense",
    description: "Schedule repeating expenses with preview.",
  },
] as const;

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  const tagName = target.tagName.toLowerCase();
  return (
    tagName === "input" ||
    tagName === "textarea" ||
    tagName === "select" ||
    target.isContentEditable
  );
}

function isActivePath(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children, currentUser }: AppShellProps) {
  const pathname = usePathname();
  const [density, setDensity] = useState<UiDensity>("comfortable");
  const [isQuickAddOpen, setIsQuickAddOpen] = useState(false);
  const [toasts, setToasts] = useState<ShellToast[]>([]);

  useEffect(() => {
    const storedDensity = window.localStorage.getItem("spendflow-ui-density");
    if (storedDensity === "compact" || storedDensity === "comfortable") {
      setDensity(storedDensity);
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-density", density);
    window.localStorage.setItem("spendflow-ui-density", density);
  }, [density]);

  useEffect(() => {
    const handleToast = (event: Event) => {
      const customEvent = event as CustomEvent<ShellToastPayload>;
      const detail = customEvent.detail;
      if (!detail) {
        return;
      }

      const id = Date.now() + Math.floor(Math.random() * 1000);
      const nextToast: ShellToast = {
        id,
        level: detail.level,
        title: detail.title,
        description: detail.description,
        durationMs: detail.durationMs,
      };

      setToasts((currentToasts) => [...currentToasts, nextToast].slice(-4));

      window.setTimeout(() => {
        setToasts((currentToasts) =>
          currentToasts.filter((toast) => toast.id !== id),
        );
      }, detail.durationMs ?? 4500);
    };

    window.addEventListener(SHELL_TOAST_EVENT, handleToast as EventListener);

    return () => {
      window.removeEventListener(
        SHELL_TOAST_EVENT,
        handleToast as EventListener,
      );
    };
  }, []);

  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsQuickAddOpen(false);
        return;
      }

      if (
        event.key.toLowerCase() !== "n" ||
        event.metaKey ||
        event.ctrlKey ||
        event.altKey ||
        isTypingTarget(event.target)
      ) {
        return;
      }

      event.preventDefault();
      setIsQuickAddOpen(true);
    };

    window.addEventListener("keydown", handleKeydown);

    return () => {
      window.removeEventListener("keydown", handleKeydown);
    };
  }, []);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">SF</div>
          <div>
            <p className="eyebrow">SpendFlow</p>
            <h1>Money with intent</h1>
          </div>
        </div>

        <nav className="nav-list" aria-label="Primary">
          {navigation.map((item) => {
            const active = isActivePath(pathname, item.href);

            return (
              <a
                key={item.label}
                className={active ? "nav-link active" : "nav-link"}
                href={item.href}
              >
                <span>{item.label}</span>
                {item.badge ? <strong>{item.badge}</strong> : null}
              </a>
            );
          })}
        </nav>

        <button
          type="button"
          className="sidebar-quick-add"
          onClick={() => setIsQuickAddOpen(true)}
        >
          <span>Quick add</span>
          <strong>N</strong>
        </button>

        <section className="sidebar-card">
          <p className="eyebrow">This month</p>
          <h2>{currentUser ? currentUser.username : "Strong rhythm"}</h2>
          <p>
            {currentUser
              ? `${currentUser.email} · ${currentUser.currency} · ${currentUser.timezone}`
              : "Planned money, overdue visibility, and faster confirmation flows are in place. The next step is wiring real data into these screens."}
          </p>
          <a className="sidebar-signout" href="/logout">
            Sign out
          </a>

          <div className="sidebar-density-toggle">
            <span>Layout density</span>
            <button
              type="button"
              className="density-switch"
              onClick={() => {
                setDensity((currentDensity) =>
                  currentDensity === "comfortable" ? "compact" : "comfortable",
                );
              }}
            >
              {density === "comfortable" ? "Comfortable" : "Compact"}
            </button>
          </div>
        </section>
      </aside>

      <main className="content">{children}</main>

      <button
        type="button"
        className="quick-add-fab"
        onClick={() => setIsQuickAddOpen(true)}
      >
        + Quick add
      </button>

      {isQuickAddOpen ? (
        <div
          className="quick-add-backdrop"
          role="presentation"
          onClick={() => setIsQuickAddOpen(false)}
        >
          <section
            className="quick-add-panel"
            role="dialog"
            aria-modal="true"
            aria-label="Quick add"
            onClick={(event) => {
              event.stopPropagation();
            }}
          >
            <div className="quick-add-header">
              <div>
                <p className="eyebrow">Quick add</p>
                <h2>Create in one step</h2>
              </div>
              <button
                type="button"
                className="day-tray-close"
                onClick={() => setIsQuickAddOpen(false)}
              >
                Close
              </button>
            </div>

            <div className="quick-add-grid">
              {QUICK_ADD_ACTIONS.map((action) => (
                <a
                  key={action.href}
                  className="quick-add-link"
                  href={action.href}
                  onClick={() => {
                    setIsQuickAddOpen(false);
                  }}
                >
                  <strong>{action.title}</strong>
                  <span>{action.description}</span>
                </a>
              ))}
            </div>
          </section>
        </div>
      ) : null}

      <div className="toast-stack" aria-live="polite" aria-atomic="false">
        {toasts.map((toast) => (
          <article key={toast.id} className={`toast-card ${toast.level}`}>
            <div>
              <strong>{toast.title}</strong>
              {toast.description ? <p>{toast.description}</p> : null}
            </div>
            <button
              type="button"
              className="toast-dismiss"
              onClick={() => {
                setToasts((currentToasts) =>
                  currentToasts.filter((item) => item.id !== toast.id),
                );
              }}
            >
              Dismiss
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}