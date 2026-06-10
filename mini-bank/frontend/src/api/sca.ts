import { api } from "./client";

export const scaApi = {
  verify: (challengeId: string, code: string) =>
    api.post<{ transaction_id: string; status: string }>(
      `/sca/challenges/${challengeId}/verify`, { code }
    ).then((r) => r.data),
};
