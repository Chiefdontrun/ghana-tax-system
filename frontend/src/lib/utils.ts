/**
 * General utility helpers.
 */

import { clsx, type ClassValue } from "clsx";

/** Merge Tailwind class names safely. */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

/** Format a date string to readable form. */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-GH", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Format a date string with time. */
export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-GH", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Mask a phone number: +233****4567 */
export function maskPhone(phone: string): string {
  if (phone.length < 6) return phone;
  return phone.slice(0, 4) + "****" + phone.slice(-4);
}

/** Convert business_type snake_case to Title Case label. */
export function formatBusinessType(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** Capitalise the first letter of a string. */
export function capitalize(str: string): string {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/** Format pesewas into GHS. */
export function formatMoney(pesewas: number): string {
  if (!pesewas || isNaN(pesewas)) return "0.00";
  return (pesewas / 100).toFixed(2);
}
