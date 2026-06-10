import { api } from "./client";

export interface MeResponse {
  user_id: string;
  role: string;
  full_name: string;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<MeResponse>("/auth/login", { email, password }).then((r) => r.data),
  logout: () => api.post("/auth/logout").then((r) => r.data),
  me: () => api.get<MeResponse>("/auth/me").then((r) => r.data),
};

export interface ActiveAgentAccess {
  id: string;
  ticket_id: string;
  expires_at: string;
  agent_user_id: string;
}

export const customerSelfApi = {
  activeAgentAccess: () =>
    api.get<ActiveAgentAccess[]>("/auth/active-agent-access").then((r) => r.data),
};

export const stepUpApi = {
  stepUp: (code: string) => api.post("/auth/step-up", { code }).then((r) => r.data),
};
