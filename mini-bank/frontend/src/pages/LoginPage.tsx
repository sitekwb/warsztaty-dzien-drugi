import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
} from "@mui/material";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const loc = useLocation();
  const [email, setEmail] = useState("customer1@minibank.pl");
  const [password, setPassword] = useState("Demo1234!");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    const to = user.role === "customer" ? "/dashboard" : "/agent";
    navigate(to, { replace: true });
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const u = await login(email, password);
      const dest = (loc.state as { from?: { pathname: string } })?.from?.pathname;
      navigate(dest ?? (u.role === "customer" ? "/dashboard" : "/agent"), { replace: true });
    } catch {
      setError("Nieprawidłowy email lub hasło.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="background.default">
      <Card sx={{ minWidth: 360, maxWidth: 420, p: 2 }}>
        <CardContent>
          <Typography variant="h5" align="center" sx={{ fontWeight: 700, mb: 3 }}>
            Logowanie · mini-bank
          </Typography>
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Hasło"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              margin="normal"
              required
            />
            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="large"
              sx={{ mt: 3 }}
              disabled={submitting}
            >
              {submitting ? "Logowanie..." : "Zaloguj się"}
            </Button>
          </form>
          <Typography variant="caption" display="block" sx={{ mt: 3, color: "text.secondary" }}>
            Konta demo: customer1@minibank.pl / Demo1234! · agent.helpdesk@minibank.pl / Agent1234!
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
