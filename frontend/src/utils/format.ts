export function formatMoney(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(num)) return "-";
  return num.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export function formatDate(value: string | null): string {
  if (!value) return "-";
  return value;
}

export function formatDateTime(value: string | null): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

export function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function currentYearMonth(): { year: number; month: number } {
  const now = new Date();
  return { year: now.getFullYear(), month: now.getMonth() + 1 };
}
