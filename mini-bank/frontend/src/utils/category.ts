export const CATEGORY_LABEL: Record<string, string> = {
  SPOZYWCZE: "Spożywcze",
  RESTAURACJE: "Restauracje",
  TRANSPORT: "Transport",
  TELEKOM: "Telekom",
  RACHUNKI: "Rachunki",
  ROZRYWKA: "Rozrywka",
  PRZELEW_WLASNY: "Przelew własny",
  WPLYWY: "Wpływy",
  INNE: "Inne",
};

export const CATEGORY_COLOR: Record<string, string> = {
  SPOZYWCZE: "#43a047",
  RESTAURACJE: "#fb8c00",
  TRANSPORT: "#1e88e5",
  TELEKOM: "#8e24aa",
  RACHUNKI: "#e53935",
  ROZRYWKA: "#fdd835",
  PRZELEW_WLASNY: "#6d4c41",
  WPLYWY: "#00897b",
  INNE: "#757575",
};

export function labelFor(category: string): string {
  return CATEGORY_LABEL[category] ?? category;
}

export function colorFor(category: string): string {
  return CATEGORY_COLOR[category] ?? "#9e9e9e";
}
