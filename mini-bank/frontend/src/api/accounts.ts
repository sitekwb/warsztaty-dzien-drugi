import { api } from "./client";

export interface Account {
  id: string;
  holder_iban: string;
  balance: string;
  currency: string;
  status: string;
  overdraft_limit: string;
  opened_on: string;
  closed_on: string | null;
}

export interface TransactionRow {
  id: string;
  source_account_id: string;
  dest_account_id: string | null;
  dest_iban: string | null;
  amount: string;
  currency: string;
  title: string | null;
  status: string;
  created_at: string;
  category: string;
}

export const accountsApi = {
  listMine: () => api.get<Account[]>("/accounts").then((r) => r.data),
  getOne: (accountId: string) =>
    api.get<Account[]>("/accounts").then((r) => {
      const acc = r.data.find((a) => a.id === accountId);
      if (!acc) throw new Error("account not found");
      return acc;
    }),
  listTransactions: (accountId: string) =>
    api
      .get<TransactionRow[]>(`/accounts/${accountId}/transactions`)
      .then((r) => r.data),
};
