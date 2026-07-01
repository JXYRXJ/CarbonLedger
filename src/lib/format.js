export const fmtNumber = (n, opts) =>
  n == null || Number.isNaN(Number(n)) ? "—" : new Intl.NumberFormat("en-US", opts).format(Number(n));

export const fmtCurrency = (n, currency = "USD") =>
  n == null ? "—" : new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 2 }).format(Number(n));

export const fmtDate = (d) => {
  if (!d) return "—";
  const date = new Date(d);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
};

export const fmtDateTime = (d) => {
  if (!d) return "—";
  const date = new Date(d);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-US", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
};

export const truncate = (s, n = 12) => {
  if (!s) return "—";
  return s.length <= n * 2 ? s : `${s.slice(0, n)}…${s.slice(-6)}`;
};