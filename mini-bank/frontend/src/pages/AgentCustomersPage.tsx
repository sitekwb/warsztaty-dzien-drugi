import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  TextField,
  Card,
  List,
  ListItemButton,
  ListItemText,
  CircularProgress,
} from "@mui/material";
import { AppHeader } from "../components/AppHeader";
import { agentApi, CustomerMasked } from "../api/agent";

export default function AgentCustomersPage() {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState<CustomerMasked[] | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const handle = setTimeout(() => {
      setCustomers(null);
      agentApi.listCustomers(search || undefined).then(setCustomers);
    }, 250);
    return () => clearTimeout(handle);
  }, [search]);

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={900} mx="auto">
        <Typography variant="h5" fontWeight={700} mb={3}>Klienci</Typography>
        <TextField
          fullWidth
          label="Szukaj po nazwisku lub emailu"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ mb: 3 }}
        />
        <Card>
          {!customers && <Box p={3}><CircularProgress /></Box>}
          {customers && (
            <List>
              {customers.map((c) => (
                <ListItemButton key={c.id} onClick={() => navigate(`/agent/customers/${c.id}`)}>
                  <ListItemText
                    primary={c.full_name}
                    secondary={`${c.email} · ${c.pesel_masked ?? "brak PESEL"} · ${c.citizenship}`}
                  />
                </ListItemButton>
              ))}
            </List>
          )}
        </Card>
      </Box>
    </Box>
  );
}
