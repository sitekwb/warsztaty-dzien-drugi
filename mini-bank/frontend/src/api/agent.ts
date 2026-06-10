import { api } from "./client";
import { Account, TransactionRow } from "./accounts";

export interface CustomerMasked {
  id: string;
  email: string;
  role: string;
  full_name: string;
  pesel_masked: string | null;
  citizenship: string;
}

export const agentApi = {
  listCustomers: (search?: string) =>
    api
      .get<CustomerMasked[]>("/agent/customers", { params: { search } })
      .then((r) => r.data),
  getCustomer: (id: string) =>
    api.get<CustomerMasked>(`/agent/customers/${id}`).then((r) => r.data),
};

export const agentCustomerApi = {
  listAccounts: (customerId: string, grantId: string) =>
    api
      .get<Account[]>(`/agent/customers/${customerId}/accounts`, {
        headers: { "X-Access-Grant-Id": grantId },
      })
      .then((r) => r.data),
  listTransactions: (customerId: string, grantId: string) =>
    api
      .get<TransactionRow[]>(`/agent/customers/${customerId}/transactions`, {
        headers: { "X-Access-Grant-Id": grantId },
      })
      .then((r) => r.data),
};
