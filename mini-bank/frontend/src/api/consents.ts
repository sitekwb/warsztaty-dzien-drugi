import { api } from "./client";

export interface PendingConsent {
  id: string;
  agent_user_id: string;
  scope: string;
  expires_at: string;
}

export const consentsApi = {
  pending: () => api.get<PendingConsent[]>("/consents/pending").then((r) => r.data),
  approve: (id: string) => api.post(`/consents/${id}/approve`).then((r) => r.data),
  reject: (id: string) => api.post(`/consents/${id}/reject`).then((r) => r.data),
};
