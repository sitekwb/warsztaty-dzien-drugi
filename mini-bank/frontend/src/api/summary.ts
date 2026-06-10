import { api } from "./client";

export interface CategoryTotal {
  category: string;
  total: string;
}

export interface AccountSummary {
  month: string;
  inflow: string;
  outflow: string;
  mtd_balance: string;
  by_category: CategoryTotal[];
}

export const summaryApi = {
  getMonth: (accountId: string, month?: string) =>
    api
      .get<AccountSummary>(`/accounts/${accountId}/summary`, {
        params: month ? { month } : {},
      })
      .then((r) => r.data),
};
