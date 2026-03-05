import clsx from "clsx";

export type BadgeVariant =
  | "active"
  | "inactive"
  | "pending"
  | "web"
  | "ussd"
  | "sys_admin"
  | "tax_admin"
  | "default";

export interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  active:    "bg-green-100 text-green-800 border border-green-200",
  inactive:  "bg-gray-100 text-gray-600 border border-gray-200",
  pending:   "bg-yellow-100 text-yellow-800 border border-yellow-200",
  web:       "bg-blue-100 text-blue-800 border border-blue-200",
  ussd:      "bg-purple-100 text-purple-800 border border-purple-200",
  sys_admin: "bg-cu-red/10 text-cu-red border border-cu-red/20",
  tax_admin: "bg-orange-100 text-orange-800 border border-orange-200",
  default:   "bg-gray-100 text-gray-600 border border-gray-200",
};

export default function Badge({ variant = "default", children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap",
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
