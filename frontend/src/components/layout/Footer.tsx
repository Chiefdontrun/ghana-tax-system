import { Link } from "react-router-dom";

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="bg-white border-t border-cu-border" role="contentinfo">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-cu-muted">
        <p>
          &copy; {year} Ghana District Assembly – Revenue Unit. All rights reserved.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
          <Link
            to="/help"
            className="hover:text-cu-red transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cu-red rounded"
          >
            Help &amp; FAQ
          </Link>
          <span aria-hidden>·</span>
          {/* Subtle staff entry point — text-only, low visual weight */}
          <Link
            to="/admin/login"
            className="text-cu-muted/70 hover:text-cu-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cu-red rounded"
          >
            Admin Login
          </Link>
          <span aria-hidden className="hidden sm:inline">·</span>
          <span className="hidden sm:inline">Powered by the Digital Revenue Platform</span>
        </div>
      </div>
    </footer>
  );
}
