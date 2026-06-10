import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import { AppHeader } from "../components/AppHeader";
import { agentCustomerApi } from "../api/agent";
import { TransactionRow } from "../api/accounts";
import { formatMoney } from "../utils/currency";

export default function AgentCustomerTransactionsPage() {
  const { id } = useParams<{ id: string }>();
  const [params] = useSearchParams();
  const grantId = params.get("grant");
  const [rows, setRows] = useState<TransactionRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || !grantId) {
      setError("Brak wymaganego grantu.");
      return;
    }
    agentCustomerApi
      .listTransactions(id, grantId)
      .then(setRows)
      .catch(() => setError("Brak dostępu (grant nieaktywny lub wygasł)."));
  }, [id, grantId]);

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={1100} mx="auto">
        <Typography variant="h5" fontWeight={700} mb={3}>Historia transakcji klienta</Typography>
        {error && <Alert severity="error">{error}</Alert>}
        {!rows && !error && <CircularProgress />}
        {rows && (
          <Card>
            <CardContent>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Data</TableCell>
                    <TableCell>Tytuł</TableCell>
                    <TableCell>Odbiorca (IBAN)</TableCell>
                    <TableCell align="right">Kwota</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell>{new Date(t.created_at).toLocaleDateString("pl-PL")}</TableCell>
                      <TableCell>{t.title ?? "—"}</TableCell>
                      <TableCell sx={{ fontFamily: "monospace", fontSize: 12 }}>
                        {t.dest_iban ?? "—"}
                      </TableCell>
                      <TableCell align="right">{formatMoney(t.amount, t.currency)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </Box>
    </Box>
  );
}
