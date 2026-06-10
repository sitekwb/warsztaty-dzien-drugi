import { api } from "./client";

export interface QueueRow {
  id: string;
  amount: string;
  currency: string;
  status: string;
  dest_iban: string | null;
  created_at: string;
}

export const supervisorApi = {
  queue: () => api.get<QueueRow[]>("/agent/supervisor/review-queue").then((r) => r.data),
};
