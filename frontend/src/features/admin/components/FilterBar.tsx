import { useRef } from "react";
import type { TraderFilters } from "../hooks/useTraders";

const BUSINESS_TYPES = [
  "hawker", "food_vendor", "clothing", "electronics", "services",
  "agriculture", "wholesale", "retail", "artisan", "other",
];

const REGIONS = [
  "Greater Accra", "Ashanti", "Western", "Northern", "Eastern", "Volta", "Other",
];

function labelFor(val: string) {
  return val.split("_").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
}

interface FilterBarProps {
  filters: TraderFilters;
  onChange: (f: Partial<TraderFilters>) => void;
  onReset: () => void;
}

export default function FilterBar({ filters, onChange, onReset }: FilterBarProps) {
  const searchRef = useRef<HTMLInputElement>(null);

  return (
    <div className="bg-white border border-cu-border rounded-lg p-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Search */}
        <div className="lg:col-span-2">
          <label className="block text-xs font-semibold text-cu-muted mb-1">Search</label>
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cu-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
            </svg>
            <input
              ref={searchRef}
              type="search"
              placeholder="Name, phone, or TIN…"
              defaultValue={filters.search ?? ""}
              onChange={(e) => onChange({ search: e.target.value })}
              className="w-full pl-9 pr-3 py-2 rounded-md border border-cu-border text-sm text-cu-text placeholder:text-cu-muted focus:outline-none focus:ring-2 focus:ring-cu-red focus:border-cu-red"
            />
          </div>
        </div>

        {/* Channel */}
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">Channel</label>
          <select
            value={filters.channel ?? ""}
            onChange={(e) => onChange({ channel: e.target.value || undefined })}
            className="w-full px-3 py-2 rounded-md border border-cu-border text-sm text-cu-text focus:outline-none focus:ring-2 focus:ring-cu-red focus:border-cu-red"
          >
            <option value="">All Channels</option>
            <option value="web">Web</option>
            <option value="ussd">USSD</option>
          </select>
        </div>

        {/* Business type */}
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">Business Type</label>
          <select
            value={filters.business_type ?? ""}
            onChange={(e) => onChange({ business_type: e.target.value || undefined })}
            className="w-full px-3 py-2 rounded-md border border-cu-border text-sm text-cu-text focus:outline-none focus:ring-2 focus:ring-cu-red focus:border-cu-red"
          >
            <option value="">All Types</option>
            {BUSINESS_TYPES.map((t) => (
              <option key={t} value={t}>{labelFor(t)}</option>
            ))}
          </select>
        </div>

        {/* Region */}
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">Region</label>
          <select
            value={filters.region ?? ""}
            onChange={(e) => onChange({ region: e.target.value || undefined })}
            className="w-full px-3 py-2 rounded-md border border-cu-border text-sm text-cu-text focus:outline-none focus:ring-2 focus:ring-cu-red focus:border-cu-red"
          >
            <option value="">All Regions</option>
            {REGIONS.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>

        {/* Date from */}
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">From Date</label>
          <input
            type="date"
            value={filters.date_from ?? ""}
            onChange={(e) => onChange({ date_from: e.target.value || undefined })}
            className="w-full px-3 py-2 rounded-md border border-cu-border text-sm text-cu-text focus:outline-none focus:ring-2 focus:ring-cu-red focus:border-cu-red"
          />
        </div>

        {/* Date to */}
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">To Date</label>
          <input
            type="date"
            value={filters.date_to ?? ""}
            onChange={(e) => onChange({ date_to: e.target.value || undefined })}
            className="w-full px-3 py-2 rounded-md border border-cu-border text-sm text-cu-text focus:outline-none focus:ring-2 focus:ring-cu-red focus:border-cu-red"
          />
        </div>

        {/* Reset */}
        <div className="flex items-end">
          <button
            onClick={() => {
              if (searchRef.current) searchRef.current.value = "";
              onReset();
            }}
            className="w-full px-4 py-2 rounded-md border border-cu-border text-sm font-medium text-cu-muted bg-white hover:bg-gray-50 transition-colors"
          >
            Reset Filters
          </button>
        </div>
      </div>
    </div>
  );
}
