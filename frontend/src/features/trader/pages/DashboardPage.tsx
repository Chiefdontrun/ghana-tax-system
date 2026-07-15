import { useTraderAuthStore } from "@/store/traderAuthStore";

export default function DashboardPage() {
  const { name, phoneNumber } = useTraderAuthStore();

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-cu-text mb-4">Trader Dashboard</h1>
      <div className="bg-white rounded-xl border border-cu-border shadow-card-sm p-6">
        <p className="text-cu-text">
          Logged in as <strong>{name || phoneNumber}</strong>
        </p>
        <p className="text-cu-muted mt-2">
          (Dashboard placeholder. Full dashboard implementation in Phase D).
        </p>
      </div>
    </div>
  );
}
