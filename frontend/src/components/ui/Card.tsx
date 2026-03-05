import clsx from "clsx";

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  /** Optional header strip — renders a cu-red top band with white text */
  headerTitle?: string;
  headerRight?: React.ReactNode;
  /** If true, removes padding from body */
  noPadding?: boolean;
}

export default function Card({
  children,
  className,
  headerTitle,
  headerRight,
  noPadding = false,
}: CardProps) {
  return (
    <div
      className={clsx(
        "bg-white border border-cu-border rounded-lg shadow-card overflow-hidden",
        className
      )}
    >
      {headerTitle && (
        <div className="flex items-center justify-between px-5 py-3 border-b border-cu-border bg-gray-50">
          <h3 className="text-sm font-semibold text-cu-text">{headerTitle}</h3>
          {headerRight && <div className="ml-4">{headerRight}</div>}
        </div>
      )}
      <div className={clsx(!noPadding && "p-5")}>{children}</div>
    </div>
  );
}
