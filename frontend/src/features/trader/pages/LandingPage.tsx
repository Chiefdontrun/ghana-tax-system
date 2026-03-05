import { Link } from "react-router-dom";

// ── Hero coat-of-arms SVG placeholder ────────────────────────────────────────
function CoatOfArms({ size = 80 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 80 80"
      aria-label="Ghana coat of arms"
      className="drop-shadow-md"
    >
      <circle cx="40" cy="40" r="38" fill="#8A1020" stroke="white" strokeWidth="2" />
      <circle cx="40" cy="40" r="30" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="1" />
      <polygon
        points="40,14 44.7,27.6 59,27.6 47.6,35.8 52.4,49.4 40,41.2 27.6,49.4 32.4,35.8 21,27.6 35.3,27.6"
        fill="white"
        opacity="0.95"
      />
      <text x="40" y="64" textAnchor="middle" fill="rgba(255,255,255,0.85)" fontSize="7" fontWeight="bold" letterSpacing="1">
        GHANA
      </text>
    </svg>
  );
}

// ── How-it-works step card ────────────────────────────────────────────────────
function HowItWorksStep({
  number,
  title,
  description,
  icon,
}: {
  number: number;
  title: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center text-center gap-3 p-6 bg-white rounded-xl border border-cu-border shadow-card">
      <div className="h-12 w-12 rounded-full bg-cu-red/10 flex items-center justify-center text-cu-red">
        {icon}
      </div>
      <div className="h-6 w-6 rounded-full bg-cu-red flex items-center justify-center text-white text-xs font-bold">
        {number}
      </div>
      <h3 className="font-semibold text-cu-text">{title}</h3>
      <p className="text-sm text-cu-muted leading-relaxed">{description}</p>
    </div>
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <p className="text-3xl font-bold text-cu-red">{value}</p>
      <p className="text-sm text-cu-muted mt-1">{label}</p>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div className="flex flex-col">
      {/* ── Hero ── */}
      <section className="bg-gradient-to-b from-cu-red to-cu-red-dark text-white">
        <div className="max-w-4xl mx-auto px-6 py-16 sm:py-24 flex flex-col items-center text-center gap-6">
          <CoatOfArms size={88} />
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight leading-tight">
              Digital Taxation &amp; Revenue System
            </h1>
            <p className="mt-2 text-white/80 text-lg font-medium">
              District Assembly — Revenue Unit
            </p>
          </div>
          <p className="text-white/70 max-w-xl text-base leading-relaxed">
            Register your business, obtain your Tax Identification Number (TIN), and stay
            compliant with the District Assembly Revenue Unit — online or via USSD.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 mt-2">
            <Link
              to="/register"
              className="inline-flex items-center justify-center gap-2 rounded-md bg-white text-cu-red font-semibold px-7 py-3 text-base hover:bg-gray-100 transition-colors shadow-md"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Register Your Business
            </Link>
            <Link
              to="/check-tin"
              className="inline-flex items-center justify-center gap-2 rounded-md border-2 border-white/60 text-white font-semibold px-7 py-3 text-base hover:bg-white/10 transition-colors"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
              </svg>
              Check My TIN
            </Link>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="bg-white border-b border-cu-border">
        <div className="max-w-4xl mx-auto px-6 py-8 grid grid-cols-3 gap-6 divide-x divide-cu-border">
          <StatCard value="1,200+" label="Registered Traders" />
          <StatCard value="10" label="Districts Covered" />
          <StatCard value="2" label="Registration Channels" />
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="max-w-4xl mx-auto px-6 py-14 w-full">
        <h2 className="text-2xl font-bold text-cu-text text-center mb-2">How It Works</h2>
        <p className="text-cu-muted text-center mb-10 text-sm">
          Register your business and receive your TIN in three simple steps
        </p>
        <div className="grid sm:grid-cols-3 gap-6">
          <HowItWorksStep
            number={1}
            title="Fill the Form"
            description="Provide your name, phone number, business type, and location online or via USSD."
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          />
          <HowItWorksStep
            number={2}
            title="Receive Your TIN"
            description="A unique Tax Identification Number (GH-TIN-XXXXXX) is issued instantly and sent via SMS."
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
              </svg>
            }
          />
          <HowItWorksStep
            number={3}
            title="Stay Compliant"
            description="Keep your TIN safe and use it for all transactions with the District Assembly Revenue Unit."
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            }
          />
        </div>
      </section>

      {/* ── USSD banner ── */}
      <section className="bg-cu-red text-white">
        <div className="max-w-4xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center gap-6 text-center sm:text-left">
          <div className="h-14 w-14 rounded-full bg-white/20 flex items-center justify-center shrink-0">
            <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold">No Internet? No Problem.</h3>
            <p className="text-white/80 mt-1 text-sm leading-relaxed">
              Dial <span className="font-bold bg-white/20 px-2 py-0.5 rounded font-mono">*XXX#</span> on
              any mobile phone to register your business via USSD — no smartphone or internet required.
            </p>
          </div>
          <Link
            to="/help"
            className="shrink-0 inline-flex items-center gap-2 rounded-md border-2 border-white/60 text-white font-semibold px-5 py-2.5 text-sm hover:bg-white/10 transition-colors"
          >
            Learn More
          </Link>
        </div>
      </section>
    </div>
  );
}
