import { useState } from "react";
import { NavLink } from "react-router-dom";
import clsx from "clsx";

const navLinks = [
  { to: "/", label: "Home" },
  { to: "/register", label: "Register" },
  { to: "/check-tin", label: "Check TIN" },
  { to: "/help", label: "Help" },
];

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="bg-cu-red text-white shadow-md" role="banner">
      {/* Top identity strip */}
      <div className="flex items-center gap-3 px-4 sm:px-6 py-3">
        {/* Ghana coat of arms placeholder */}
        <div
          className="h-10 w-10 rounded-full bg-white/20 border-2 border-white/60 flex items-center justify-center shrink-0"
          aria-hidden
        >
          <svg viewBox="0 0 40 40" className="h-7 w-7 text-white" fill="currentColor">
            <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" strokeWidth="2" />
            <polygon points="20,6 23.5,15 33,15 25.5,21 28.5,30 20,24.5 11.5,30 14.5,21 7,15 16.5,15" opacity="0.9" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-sm sm:text-base tracking-wide leading-tight">
            DISTRICT ASSEMBLY – REVENUE UNIT
          </p>
          <p className="text-white/70 text-xs">Digital Taxation &amp; Revenue Tracking System</p>
        </div>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
          {navLinks.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                clsx(
                  "px-3 py-1.5 rounded text-sm font-medium transition-colors",
                  isActive
                    ? "bg-white/20 text-white"
                    : "text-white/80 hover:bg-white/10 hover:text-white"
                )
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 rounded hover:bg-white/10 transition-colors"
          onClick={() => setMenuOpen((v) => !v)}
          aria-expanded={menuOpen}
          aria-label="Toggle navigation"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile nav dropdown */}
      {menuOpen && (
        <nav className="md:hidden border-t border-white/20 px-4 py-2 flex flex-col gap-1" aria-label="Mobile navigation">
          {navLinks.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                clsx(
                  "px-3 py-2 rounded text-sm font-medium transition-colors",
                  isActive
                    ? "bg-white/20 text-white"
                    : "text-white/80 hover:bg-white/10 hover:text-white"
                )
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  );
}
