import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Box, Card, CardContent, Typography, Button, Alert, CircularProgress,
  Chip, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { AppHeader } from "../components/AppHeader";
import { accountsApi, Account, TransactionRow } from "../api/accounts";
import { summaryApi, AccountSummary } from "../api/summary";
import { labelFor, colorFor } from "../utils/category";
import { extractErrorDetail } from "../utils/errors";

function formatMoney(amount: string | number, currency: string): string {
  const n = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("pl-PL", { style: "currency", currency }).format(n);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pl-PL");
}

export default function AccountDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [account, setAccount] = useState<Account | null>(null);
  const [transactions, setTransactions] = useState<TransactionRow[] | null>(null);
  const [summary, setSummary] = useState<AccountSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      accountsApi.getOne(id),
      accountsApi.listTransactions(id),
      summaryApi.getMonth(id),
    ])
      .then(([acc, txs, sum]) => {
        setAccount(acc);
        setTransactions(txs);
        setSummary(sum);
      })
      .catch((e: unknown) => {
        setError(extractErrorDetail(e, "Nie udało się załadować szczegółów konta."));
      });
  }, [id]);

  if (error) {
    return (
      <Box>
        <AppHeader />
        <Box p={3} maxWidth={900} mx="auto">
          <Alert severity="error">{error}</Alert>
          <Button sx={{ mt: 2 }} onClick={() => navigate("/dashboard")}>
            Powrót do dashboardu
          </Button>
        </Box>
      </Box>
    );
  }
  if (!account || !transactions || !summary) {
    return (
      <Box>
        <AppHeader />
        <Box p={3} display="flex" justifyContent="center"><CircularProgress /></Box>
      </Box>
    );
  }

  const donutData = summary.by_category.map((row) => ({
    name: labelFor(row.category),
    value: parseFloat(row.total),
    color: colorFor(row.category),
  }));

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={1100} mx="auto">
        <Button onClick={() => navigate("/dashboard")} sx={{ mb: 2 }}>← Powrót</Button>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="overline" color="text.secondary">
              {account.currency} · {account.status === "open" ? "aktywne" : "zamknięte"}
            </Typography>
            <Typography variant="h4" fontWeight={700} sx={{ mt: 1 }}>
              {formatMoney(account.balance, account.currency)}
            </Typography>
            <Typography variant="body2" fontFamily="monospace" color="text.secondary">
              {account.holder_iban}
            </Typography>
          </CardContent>
        </Card>

        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card sx={{ borderLeft: "4px solid #43a047" }}>
              <CardContent>
                <Typography variant="overline" color="text.secondary">Wpływy MTD</Typography>
                <Typography variant="h5" fontWeight={700} color="success.main">
                  {formatMoney(summary.inflow, account.currency)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card sx={{ borderLeft: "4px solid #e53935" }}>
              <CardContent>
                <Typography variant="overline" color="text.secondary">Wydatki MTD</Typography>
                <Typography variant="h5" fontWeight={700} color="error.main">
                  {formatMoney(summary.outflow, account.currency)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card sx={{ borderLeft: "4px solid #1e88e5" }}>
              <CardContent>
                <Typography variant="overline" color="text.secondary">Saldo MTD</Typography>
                <Typography variant="h5" fontWeight={700}>
                  {formatMoney(summary.mtd_balance, account.currency)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {donutData.length > 0 && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Wydatki per kategoria — {summary.month}
              </Typography>
              <Box sx={{ width: "100%", height: 320 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={donutData} dataKey="value" nameKey="name"
                         cx="50%" cy="50%" innerRadius={70} outerRadius={110}>
                      {donutData.map((entry, idx) => (
                        <Cell key={idx} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: number) => formatMoney(v, account.currency)} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Historia transakcji</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Data</TableCell>
                    <TableCell>Tytuł</TableCell>
                    <TableCell>Kategoria</TableCell>
                    <TableCell align="right">Kwota</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactions.map((tx) => {
                    const incoming = tx.dest_account_id === id;
                    return (
                      <TableRow key={tx.id}>
                        <TableCell>{formatDate(tx.created_at)}</TableCell>
                        <TableCell>{tx.title ?? "—"}</TableCell>
                        <TableCell>
                          <Chip
                            label={labelFor(tx.category)}
                            size="small"
                            sx={{
                              bgcolor: colorFor(tx.category),
                              color: "#fff",
                              fontWeight: 600,
                            }}
                          />
                        </TableCell>
                        <TableCell align="right" sx={{
                          color: incoming ? "success.main" : "error.main",
                          fontWeight: 600,
                        }}>
                          {incoming ? "+" : "−"}{formatMoney(tx.amount, tx.currency)}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">{tx.status}</Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {transactions.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography variant="body2" color="text.secondary">
                          Brak transakcji do wyświetlenia.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
