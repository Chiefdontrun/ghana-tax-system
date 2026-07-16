import { useState } from "react";
import { Navigate } from "react-router-dom";
import { Alert, Button, Card } from "@/components/ui";
import { useAuthStore } from "@/store/authStore";
import api from "@/lib/api";
import { useRateSchedules, type RateSchedule } from "../hooks/useTax";

const BUSINESS_TYPES = [
  "food_vendor",
  "clothing",
  "electronics",
  "services",
  "agriculture",
  "other",
];

const emptyForm = {
  tax_category: "BOP",
  business_type: "food_vendor",
  region: "",
  district: "",
  rate_type: "FIXED" as "FIXED" | "PERCENTAGE_TURNOVER",
  fixed_amount: 10000,
  percentage_rate: null as number | null,
  min_amount: null as number | null,
  max_amount: null as number | null,
  period: "ANNUAL",
  effective_year: new Date().getFullYear(),
  is_active: true,
};

export default function TaxRateSchedulesPage() {
  const role = useAuthStore((s) => s.role);
  if (role !== "SYS_ADMIN") {
    return <Navigate to="/admin/dashboard" replace />;
  }

  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [category, setCategory] = useState("");
  const { items, isLoading, error, reload } = useRateSchedules({
    effective_year: year || undefined,
    tax_category: category || undefined,
  });
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const onRateTypeChange = (rate_type: "FIXED" | "PERCENTAGE_TURNOVER") => {
    if (rate_type === "FIXED") {
      setForm((f) => ({
        ...f,
        rate_type,
        fixed_amount: f.fixed_amount ?? 10000,
        percentage_rate: null,
        min_amount: null,
        max_amount: null,
      }));
    } else {
      setForm((f) => ({
        ...f,
        rate_type,
        fixed_amount: null as unknown as number,
        percentage_rate: 2.5,
        min_amount: 0,
        max_amount: null,
      }));
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload: Record<string, unknown> = {
        tax_category: form.tax_category,
        business_type: form.business_type,
        region: form.region || null,
        district: form.district || null,
        rate_type: form.rate_type,
        period: form.period,
        effective_year: Number(form.effective_year),
        is_active: form.is_active,
      };
      if (form.rate_type === "FIXED") {
        payload.fixed_amount = Number(form.fixed_amount);
      } else {
        payload.percentage_rate = Number(form.percentage_rate);
        if (form.min_amount != null) payload.min_amount = Number(form.min_amount);
        if (form.max_amount != null) payload.max_amount = Number(form.max_amount);
      }
      await api.post("/api/tax/rate-schedules/", payload);
      setShowForm(false);
      setForm(emptyForm);
      reload();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (s: RateSchedule) => {
    try {
      await api.patch(`/api/tax/rate-schedules/${s.schedule_id}/`, {
        is_active: !s.is_active,
      });
      reload();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Update failed");
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-cu-text">Tax Rate Schedules</h1>
          <p className="text-sm text-cu-muted mt-0.5">SYS_ADMIN only — BOP fee schedules</p>
        </div>
        <Button onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "New schedule"}
        </Button>
      </div>

      {(error || formError) && <Alert variant="error">{error || formError}</Alert>}

      <div className="bg-white border border-cu-border rounded-lg p-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">Year</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="w-full px-3 py-2 rounded-md border border-cu-border text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">Category</label>
          <input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="BOP"
            className="w-full px-3 py-2 rounded-md border border-cu-border text-sm"
          />
        </div>
      </div>

      {showForm && (
        <Card>
          <form onSubmit={submit} className="p-4 space-y-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-cu-muted">Tax category</label>
              <input
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={form.tax_category}
                onChange={(e) => setForm({ ...form, tax_category: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-cu-muted">Business type</label>
              <select
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={form.business_type}
                onChange={(e) => setForm({ ...form, business_type: e.target.value })}
              >
                {BUSINESS_TYPES.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-cu-muted">Region (optional)</label>
              <input
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={form.region}
                onChange={(e) => setForm({ ...form, region: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-cu-muted">District (optional)</label>
              <input
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={form.district}
                onChange={(e) => setForm({ ...form, district: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-cu-muted">Rate type</label>
              <select
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={form.rate_type}
                onChange={(e) => onRateTypeChange(e.target.value as "FIXED" | "PERCENTAGE_TURNOVER")}
              >
                <option value="FIXED">FIXED (flat pesewas)</option>
                <option value="PERCENTAGE_TURNOVER">PERCENTAGE_TURNOVER</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-cu-muted">Effective year</label>
              <input
                type="number"
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={form.effective_year}
                onChange={(e) => setForm({ ...form, effective_year: Number(e.target.value) })}
              />
            </div>
            {form.rate_type === "FIXED" ? (
              <div>
                <label className="text-xs font-semibold text-cu-muted">Fixed amount (pesewas)</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border rounded-md text-sm"
                  value={form.fixed_amount ?? ""}
                  onChange={(e) => setForm({ ...form, fixed_amount: Number(e.target.value) })}
                  required
                />
              </div>
            ) : (
              <>
                <div>
                  <label className="text-xs font-semibold text-cu-muted">Percentage rate</label>
                  <input
                    type="number"
                    step="0.01"
                    className="w-full px-3 py-2 border rounded-md text-sm"
                    value={form.percentage_rate ?? ""}
                    onChange={(e) => setForm({ ...form, percentage_rate: Number(e.target.value) })}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-cu-muted">Min amount (pesewas)</label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border rounded-md text-sm"
                    value={form.min_amount ?? ""}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        min_amount: e.target.value === "" ? null : Number(e.target.value),
                      })
                    }
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-cu-muted">Max amount (pesewas)</label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border rounded-md text-sm"
                    value={form.max_amount ?? ""}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        max_amount: e.target.value === "" ? null : Number(e.target.value),
                      })
                    }
                  />
                </div>
              </>
            )}
            <div className="sm:col-span-2">
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Create schedule"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <div className="bg-white border border-cu-border rounded-lg overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-cu-muted">
            <tr>
              <th className="px-3 py-2">Category</th>
              <th className="px-3 py-2">Business</th>
              <th className="px-3 py-2">Scope</th>
              <th className="px-3 py-2">Rate</th>
              <th className="px-3 py-2">Year</th>
              <th className="px-3 py-2">Active</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-cu-muted">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-cu-muted">
                  No schedules
                </td>
              </tr>
            )}
            {items.map((s) => (
              <tr key={s.schedule_id} className="border-t border-cu-border">
                <td className="px-3 py-2">{s.tax_category}</td>
                <td className="px-3 py-2">{s.business_type}</td>
                <td className="px-3 py-2">
                  {[s.region, s.district].filter(Boolean).join(" / ") || "Assembly-wide"}
                </td>
                <td className="px-3 py-2">
                  {s.rate_type === "FIXED"
                    ? `FIXED GHS ${((s.fixed_amount ?? 0) / 100).toFixed(2)}`
                    : `${s.percentage_rate}% of turnover`}
                </td>
                <td className="px-3 py-2">{s.effective_year}</td>
                <td className="px-3 py-2">
                  <button
                    type="button"
                    onClick={() => toggleActive(s)}
                    className={`text-xs font-semibold px-2 py-1 rounded ${
                      s.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {s.is_active ? "Active" : "Inactive"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
