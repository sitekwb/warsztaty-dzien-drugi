import { api } from "./client";

export interface TransferPayload {
  source_account_id: string;
  dest_iban: string;
  amount: string;
  currency: string;
  title?: string;
  recipient_name: string;
}

export interface TransferInitiateResult {
  sca_challenge_id: string;
  expires_at: string;
}

export interface TransferResult {
  transaction_id: string;
  status: string;
}

export const transfersApi = {
  initiate: (payload: TransferPayload, idempotencyKey?: string) =>
    api.post<TransferInitiateResult>("/transfers", payload, {
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
    }).then((r) => r.data),
  approve: (transactionId: string) =>
    api.post(`/transfers/${transactionId}/approve`).then((r) => r.data),
};
