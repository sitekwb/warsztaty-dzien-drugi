import { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
} from "@mui/material";
import { AppHeader } from "../components/AppHeader";
import { GrantCountdown } from "../components/GrantCountdown";
import { accessGrantsApi, AccessGrant } from "../api/accessGrants";

export default function MyGrantsPage() {
  const [grants, setGrants] = useState<AccessGrant[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    accessGrantsApi.listActive().then(setGrants).catch(() => setError("Nie udało się załadować."));
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleRevoke(id: string) {
    await accessGrantsApi.revoke(id);
    refresh();
  }

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={900} mx="auto">
        <Typography variant="h5" fontWeight={700} mb={3}>
          Moje aktywne dostępy
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        {!grants && !error && <CircularProgress />}
        {grants && grants.length === 0 && (
          <Alert severity="info">Brak aktywnych grantów.</Alert>
        )}
        {grants && grants.map((g) => (
          <Card key={g.id} sx={{ mb: 2 }}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
                <Typography variant="subtitle1" fontWeight={700}>
                  Zgłoszenie: {g.ticket_id}
                </Typography>
                <GrantCountdown expiresAt={g.expires_at} />
                <Box flexGrow={1} />
                <Button color="error" onClick={() => handleRevoke(g.id)}>
                  Cofnij dostęp
                </Button>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Klient ID: {g.customer_user_id} · od {new Date(g.granted_at).toLocaleString("pl-PL")}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Powód: {g.reason}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
}
