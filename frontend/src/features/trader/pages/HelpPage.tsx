import { useState } from "react";

// ── FAQ Accordion ─────────────────────────────────────────────────────────────
const FAQS = [
  {
    q: "What is a TIN?",
    a: "A Tax Identification Number (TIN) is a unique identifier (format: GH-TIN-XXXXXX) issued by the District Assembly Revenue Unit to every registered business or trader. It is required for official transactions, permits, and compliance with local revenue regulations.",
  },
  {
    q: "How do I register online?",
    a: "Visit the Register page on this website, fill in your name, phone number, business type, and location details in two quick steps, then submit. Your TIN is generated instantly and an SMS confirmation is sent to your phone.",
  },
  {
    q: "How do I register via USSD?",
    a: "Dial *XXX# on any mobile phone — no internet or smartphone required. Follow the on-screen menu: select '1. Register Business', then enter your name, business type, region, and market name across 5 simple steps. Your TIN is read back to you and sent via SMS.",
  },
  {
    q: "What if I lose my TIN?",
    a: "Visit the 'Check My TIN' page on this website and enter the phone number you used during registration. Your TIN will be displayed immediately. Alternatively, dial *XXX# and select '2. Check My TIN'.",
  },
  {
    q: "Who do I contact for help?",
    a: "Visit your nearest District Assembly Revenue Unit office during working hours (Monday – Friday, 8:00 AM – 5:00 PM). You can also call the helpline at +233 XX XXX XXXX or email revenue@districtassembly.gov.gh.",
  },
];

function AccordionItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-cu-border rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-5 py-4 text-left text-sm font-semibold text-cu-text bg-white hover:bg-gray-50 transition-colors"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span>{q}</span>
        <svg
          className={`h-5 w-5 text-cu-muted shrink-0 ml-3 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="px-5 pb-5 pt-1 text-sm text-cu-muted leading-relaxed bg-white border-t border-cu-border">
          {a}
        </div>
      )}
    </div>
  );
}

// ── USSD step guide ───────────────────────────────────────────────────────────
const USSD_STEPS = [
  { step: 1, label: "Dial *XXX#", detail: "Open your phone dialler and dial the USSD code." },
  { step: 2, label: "Select option 1 — Register Business", detail: "Press 1 and send to begin registration." },
  { step: 3, label: "Enter your full name", detail: "Type your name and press send." },
  { step: 4, label: "Select your business type", detail: "Choose from the numbered list (1=Hawker first) and press send." },
  { step: 5, label: "Select monthly income bracket", detail: "Choose 1–4 for your typical monthly income range." },
  { step: 6, label: "Select your region", detail: "Choose from the numbered list (1–7) and press send." },
  { step: 7, label: "Enter market or community name", detail: "Type your market name and press send." },
  { step: 8, label: "Confirm and register", detail: "Review your details, press 1 to confirm. Your TIN is displayed and sent via SMS." },
];

// ── Main page ─────────────────────────────────────────────────────────────────
export default function HelpPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      {/* Page header */}
      <div className="mb-10 text-center">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-cu-red/10 mb-3">
          <svg className="h-6 w-6 text-cu-red" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-cu-text">Help &amp; FAQ</h1>
        <p className="text-cu-muted text-sm mt-1">
          Frequently asked questions and registration guides
        </p>
      </div>

      {/* FAQ section */}
      <section className="mb-12">
        <h2 className="text-lg font-semibold text-cu-text mb-4">Frequently Asked Questions</h2>
        <div className="space-y-3">
          {FAQS.map((faq) => (
            <AccordionItem key={faq.q} q={faq.q} a={faq.a} />
          ))}
        </div>
      </section>

      {/* USSD guide */}
      <section className="mb-12">
        <h2 className="text-lg font-semibold text-cu-text mb-1">USSD Registration Guide</h2>
        <p className="text-sm text-cu-muted mb-6">
          Follow these steps to register via any mobile phone — no internet required.
        </p>
        <div className="bg-gray-900 rounded-xl p-6 text-green-400 font-mono text-sm space-y-3 overflow-x-auto">
          <p className="text-gray-500 text-xs mb-2"># USSD session simulation</p>
          <p><span className="text-yellow-400">DIAL:</span> *XXX#</p>
          <p><span className="text-blue-400">MENU:</span> Welcome to DA Revenue</p>
          <p className="pl-4 text-gray-400">1. Register Business</p>
          <p className="pl-4 text-gray-400">2. Check My TIN</p>
          <p className="pl-4 text-gray-400">3. Help</p>
          <p><span className="text-yellow-400">INPUT:</span> 1</p>
          <p><span className="text-blue-400">PROMPT:</span> Step 1/5 — Enter your full name:</p>
          <p><span className="text-yellow-400">INPUT:</span> Kofi Mensah</p>
          <p><span className="text-blue-400">PROMPT:</span> Step 2/5 — Select business type...</p>
          <p className="text-gray-500">... (continue through all 5 steps)</p>
          <p><span className="text-green-300">RESULT:</span> Registration complete!</p>
          <p className="pl-4 text-green-300">Your TIN: GH-TIN-3A7F2C</p>
        </div>
        <ol className="mt-6 space-y-3">
          {USSD_STEPS.map(({ step, label, detail }) => (
            <li key={step} className="flex gap-4">
              <div className="h-7 w-7 rounded-full bg-cu-red flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5">
                {step}
              </div>
              <div>
                <p className="text-sm font-semibold text-cu-text">{label}</p>
                <p className="text-xs text-cu-muted mt-0.5">{detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* Contact info */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-cu-text mb-4">Contact the Revenue Unit</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {[
            {
              icon: (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              ),
              label: "Office Address",
              value: "District Assembly Compound, Revenue Unit\nP.O. Box 001, Ghana",
            },
            {
              icon: (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              ),
              label: "Helpline",
              value: "+233 XX XXX XXXX\nMon – Fri, 8:00 AM – 5:00 PM",
            },
          ].map(({ icon, label, value }) => (
            <div key={label} className="flex gap-3 p-4 rounded-lg border border-cu-border bg-white">
              <div className="h-9 w-9 rounded-full bg-cu-red/10 text-cu-red flex items-center justify-center shrink-0">
                {icon}
              </div>
              <div>
                <p className="text-xs font-semibold text-cu-muted uppercase tracking-wide">{label}</p>
                <p className="text-sm text-cu-text mt-0.5 whitespace-pre-line">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Download guide placeholder */}
      <div className="rounded-lg border border-dashed border-cu-border p-6 text-center">
        <svg className="h-8 w-8 text-cu-muted mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-sm font-medium text-cu-text">Registration Guide (PDF)</p>
        <p className="text-xs text-cu-muted mt-1 mb-3">Printable step-by-step registration instructions</p>
        <button
          disabled
          className="inline-flex items-center gap-2 rounded-md border border-cu-border px-4 py-2 text-sm font-medium text-cu-muted cursor-not-allowed opacity-60"
        >
          Download Guide
        </button>
        <p className="text-xs text-cu-muted mt-2">Coming soon</p>
      </div>
    </div>
  );
}
