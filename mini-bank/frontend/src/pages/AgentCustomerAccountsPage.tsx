import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Button,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { AppHeader } from "../components/AppHeader";
import { agentCustomerApi } from "../api/agent";
import { Account } from "../api/accounts";
import { formatMoney } from "../utils/currency";

export default function AgentCustomerAccountsPage() {
  const { id } = useParams<{ id: string }>();
  const [params] = useSearchParams();
  const grantId = params.get("grant");
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || !grantId) {
      setError("Brak wymaganego grantu.");
      return;
    }
    agentCustomerApi
      .listAccounts(id, grantId)
      .then(setAccounts)
      .catch(() => setError("Brak dostępu (grant nieaktywny lub wygasł)."));
  }, [id, grantId]);

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={1100} mx="auto">
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" fontWeight={700}>Konta klienta</Typography>
          {grantId && (
            <Button
              variant="outlined"
              onClick={() => navigate(`/agent/customers/${id}/transactions?grant=${grantId}`)}
            >
              Historia transakcji
            </Button>
          )}
        </Box>
        {error && <Alert severity="error">{error}</Alert>}
        {!accounts && !error && <CircularProgress />}
        {accounts && (
          <Grid container spacing={2}>
            {accounts.map((a) => (
              <Grid size={{ xs: 12, md: 6 }} key={a.id}>
                <Card>
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
