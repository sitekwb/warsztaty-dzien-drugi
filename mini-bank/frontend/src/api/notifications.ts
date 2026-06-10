import { api } from "./client";

export interface NotificationRow {
  id: string;
  kind: string;
  body: string;
  created_at: string;
}

export const notificationsApi = {
  listMine: () => api.get<NotificationRow[]>("/notifications/me").then((r) => r.data),
};
