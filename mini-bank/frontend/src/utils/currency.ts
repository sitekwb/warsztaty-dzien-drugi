export function formatMoney(amount: string, currency: string): string {
  const num = Number.parseFloat(amount);
  return new Intl.NumberFormat("pl-PL", {
    style: "currency",
    currency,
  }).format(num);
}

export function maskIban(iban: string): string {
  const stripped = iban.replace(/\s/g, "");
  if (stripped.length < 8) return iban;
  return `${stripped.slice(0, 4)} ... ${stripped.slice(-4)}`;
}
