import { useEffect, useState } from "react";
import {
  Box, Typography, Card, CardContent, Button, Alert, CircularProgress,
  Table, TableHead, TableBody, TableRow, TableCell,
} from "@mui/material";
import { AppHeader } from "../components/AppHeader";
import { supervisorApi, QueueRow } from "../api/supervisor";
import { transfersApi } from "../api/transfers";
import { formatMoney } from "../utils/currency";

export default function SupervisorQueuePage() {
  const [rows, setRows] = useState<QueueRow[] | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  function refresh() {
    supervisorApi.queue().then(setRows);
  }
  useEffect(() => { refresh(); }, []);

  async function approve(id: string) {
    try {
      await transfersApi.approve(id);
      setMsg(`Zatwierdzono transakcję ${id.slice(0, 8)}.`);
      refresh();
    } catch {
      setMsg("Błąd zatwierdzenia.");
    }
  }

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={1100} mx="auto">
        <Typography variant="h5" fontWeight={700} mb={3}>Kolejka supervisora</Typography>
        {msg && <Alert severity="info" sx={{ mb: 2 }}>{msg}</Alert>}
        {!rows && <CircularProgress />}
        {rows && rows.length === 0 && <Alert severity="info">Kolejka pusta.</Alert>}
        {rows && rows.length > 0 && (
          <Card>
            <CardContent>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Data</TableCell>
                    <TableCell>IBAN</TableCell>
                    <TableCell align="right">Kwota</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell>{new Date(t.created_at).toLocaleString("pl-PL")}</TableCell>
                      <TableCell sx={{ fontFamily: "monospace", fontSize: 12 }}>
                        {t.dest_iban ?? "—"}
                      </TableCell>
                      <TableCell align="right">{formatMoney(t.amount, t.currency)}</TableCell>
                      <TableCell>{t.status}</TableCell>
                      <TableCell>
                        {t.status === "requires_dual_approval" && (
                          <Button size="small" variant="contained"
                                  onClick={() => approve(t.id)}>Zatwierdź</Button>
                        )}
                      </TableCell>
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
