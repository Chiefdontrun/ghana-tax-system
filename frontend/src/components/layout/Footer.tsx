export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="bg-white border-t border-cu-border" role="contentinfo">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-cu-muted">
        <p>
          &copy; {year} Ghana District Assembly – Revenue Unit. All rights reserved.
        </p>
        <div className="flex items-center gap-4">
          <a href="/help" className="hover:text-cu-red transition-colors">
            Help &amp; FAQ
          </a>
          <span aria-hidden>·</span>
          <span>Powered by the Digital Revenue Platform</span>
        </div>
      </div>
    </footer>
  );
}
