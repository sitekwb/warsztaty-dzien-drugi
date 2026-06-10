import { useEffect, useState } from "react";
import { Box, Typography, Card, CardContent, Button, Alert, CircularProgress } from "@mui/material";
import { AppHeader } from "../components/AppHeader";
import { consentsApi, PendingConsent } from "../api/consents";

export default function ConsentsPage() {
  const [list, setList] = useState<PendingConsent[] | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  function refresh() {
    consentsApi.pending().then(setList);
  }
  useEffect(() => { refresh(); }, []);

  async function decide(id: string, approve: boolean) {
    if (approve) await consentsApi.approve(id);
    else await consentsApi.reject(id);
    setMsg(approve ? "Zgoda zaakceptowana." : "Zgoda odrzucona.");
    refresh();
  }

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={700} mx="auto">
        <Typography variant="h5" fontWeight={700} mb={3}>Oczekujące zgody</Typography>
        {msg && <Alert severity="info" sx={{ mb: 2 }}>{msg}</Alert>}
        {!list && <CircularProgress />}
        {list && list.length === 0 && <Alert severity="info">Brak oczekujących próśb o zgodę.</Alert>}
        {list && list.map((c) => (
          <Card key={c.id} sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700}>Zakres: {c.scope}</Typography>
              <Typography variant="body2">Agent ID: {c.agent_user_id}</Typography>
              <Typography variant="body2" color="text.secondary">
                Wygasa: {new Date(c.expires_at).toLocaleString("pl-PL")}
              </Typography>
              <Box display="flex" gap={2} mt={2}>
                <Button variant="contained" color="success"
                        onClick={() => decide(c.id, true)}>Zaakceptuj</Button>
                <Button variant="outlined" color="error"
                        onClick={() => decide(c.id, false)}>Odrzuć</Button>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
}
