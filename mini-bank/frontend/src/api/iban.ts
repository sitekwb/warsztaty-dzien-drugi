import { api } from "./client";

export interface IbanValidation {
  iban: string;
  valid: boolean;
  bank_name?: string;
  bic?: string;
  source: "local" | "external" | "cache";
}

export const ibanApi = {
  validate: (iban: string) =>
    api.get<IbanValidation>("/iban/validate", { params: { iban } }).then((r) => r.data),
};
