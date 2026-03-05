import clsx from "clsx";
import Spinner from "./Spinner";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
  headerClassName?: string;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField: keyof T;
  isLoading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  className?: string;
}

export default function Table<T extends Record<string, unknown>>({
  columns,
  data,
  keyField,
  isLoading = false,
  emptyMessage = "No records found.",
  onRowClick,
  className,
}: TableProps<T>) {
  return (
    <div className={clsx("w-full overflow-x-auto", className)}>
      <table className="min-w-full text-sm text-left">
        <thead>
          <tr className="border-b border-cu-border bg-gray-50">
            {columns.map((col) => (
              <th
                key={col.key}
                className={clsx(
                  "px-4 py-3 text-xs font-semibold text-cu-muted uppercase tracking-wider whitespace-nowrap",
                  col.headerClassName
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-cu-border">
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="py-12 text-center">
                <div className="flex flex-col items-center gap-2 text-cu-muted">
                  <Spinner size="lg" />
                  <span className="text-sm">Loading…</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="py-12 text-center text-cu-muted text-sm"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={String(row[keyField])}
                onClick={() => onRowClick?.(row)}
                className={clsx(
                  "bg-white hover:bg-gray-50 transition-colors",
                  onRowClick && "cursor-pointer"
                )}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={clsx("px-4 py-3 text-cu-text", col.className)}
                  >
                    {col.render
                      ? col.render(row)
                      : String(row[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
