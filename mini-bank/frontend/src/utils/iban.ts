/** Strip spaces, uppercase. */
export function normalizeIban(input: string): string {
  return input.replace(/\s+/g, "").toUpperCase();
}

/** Display IBAN in 4-char groups: PL21114020040000... → "PL21 1140 2004 0000 ..." */
export function formatIban(input: string): string {
  const s = normalizeIban(input);
  return s.replace(/(.{4})/g, "$1 ").trim();
}
