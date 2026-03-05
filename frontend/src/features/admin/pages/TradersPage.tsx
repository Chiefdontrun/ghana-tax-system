import FilterBar from "../components/FilterBar";
import TraderTable from "../components/TraderTable";
import { useTraders } from "../hooks/useTraders";
import { Alert } from "@/components/ui";

export default function TradersPage() {
  const { traders, total, page, totalPages, isLoading, error, filters, setFilters, resetFilters } =
    useTraders();

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-cu-text">Traders</h1>
        <p className="text-sm text-cu-muted mt-0.5">
          {isLoading ? "Loading…" : `${total.toLocaleString()} registered trader${total !== 1 ? "s" : ""}`}
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Filters */}
      <FilterBar filters={filters} onChange={setFilters} onReset={resetFilters} />

      {/* Table */}
      <TraderTable
        traders={traders}
        total={total}
        page={page}
        totalPages={totalPages}
        pageSize={filters.page_size ?? 20}
        isLoading={isLoading}
        onPageChange={(p) => setFilters({ page: p })}
      />
    </div>
  );
}
