import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { AppHeader } from "../components/AppHeader";
import { accountsApi, Account } from "../api/accounts";
import { customerSelfApi, ActiveAgentAccess } from "../api/auth";
import { formatMoney } from "../utils/currency";

export default function DashboardPage() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [agentAccess, setAgentAccess] = useState<ActiveAgentAccess[]>([]);

  useEffect(() => {
    accountsApi
      .listMine()
      .then(setAccounts)
      .catch(() => setError("Nie udało się załadować kont."));
  }, []);

  useEffect(() => {
    customerSelfApi
      .activeAgentAccess()
      .then(setAgentAccess)
      .catch(() => setAgentAccess([]));
  }, []);

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={1100} mx="auto">
        {agentAccess.length > 0 && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            Pracownik banku ma dostęp do Twojego konta do {new Date(agentAccess[0].expires_at).toLocaleTimeString("pl-PL")} (zgłoszenie {agentAccess[0].ticket_id}).
          </Alert>
        )}
        <Box mb={2}>
          <Button variant="text" onClick={() => navigate("/consents")}>
            Oczekujące zgody
          </Button>
        </Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" fontWeight={700}>Twoje konta</Typography>
          <Button variant="contained" onClick={() => navigate("/transfer")}>
            Nowy przelew
          </Button>
        </Box>
        {error && <Alert severity="error">{error}</Alert>}
        {!accounts && !error && <CircularProgress />}
        {accounts && (
          <Grid container spacing={2}>
            {accounts.map((a) => (
              <Grid size={{ xs: 12, md: 6 }} key={a.id}>
                <Card
                  onClick={() => navigate(`/accounts/${a.id}`)}
                  sx={{ cursor: "pointer", transition: "box-shadow 120ms", "&:hover": { boxShadow: 6 } }}
                >
                  <CardContent>
                    <Typography variant="overline" color="text.secondary">
                      {a.currency} · {a.status === "open" ? "aktywne" : "zamknięte"}
                    </Typography>
                    <Typography variant="h4" fontWeight={700} sx={{ mt: 1, mb: 1 }}>
                      {formatMoney(a.balance, a.currency)}
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace" color="text.secondary">
                      {a.holder_iban}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Box>
  );
}
