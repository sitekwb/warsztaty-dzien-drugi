import { api } from "./client";

export interface AccessGrant {
  id: string;
  agent_user_id: string;
  customer_user_id: string;
  ticket_id: string;
  reason: string;
  granted_at: string;
  expires_at: string;
  revoked_at: string | null;
}

export interface CreateGrantPayload {
  customer_id: string;
  ticket_id: string;
  reason: string;
  ttl_minutes: number;
}

export const accessGrantsApi = {
  create: (payload: CreateGrantPayload) =>
    api.post<AccessGrant>("/agent/access-grants", payload).then((r) => r.data),
  listActive: () =>
    api.get<AccessGrant[]>("/agent/access-grants/active").then((r) => r.data),
  revoke: (grantId: string) =>
    api.delete(`/agent/access-grants/${grantId}`).then((r) => r.data),
};
