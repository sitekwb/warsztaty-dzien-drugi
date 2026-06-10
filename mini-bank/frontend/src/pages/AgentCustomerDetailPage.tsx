import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
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
import { OpenAccessModal } from "../components/OpenAccessModal";
import { agentApi, CustomerMasked } from "../api/agent";

export default function AgentCustomerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState<CustomerMasked | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    if (!id) return;
    agentApi.getCustomer(id).then(setCustomer).catch(() => setError("Nie znaleziono klienta."));
  }, [id]);

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={700} mx="auto">
        <Button onClick={() => navigate("/agent")}>← Powrót do listy</Button>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {!customer && !error && <CircularProgress sx={{ mt: 3 }} />}
        {customer && id && (
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h5" fontWeight={700} gutterBottom>
                {customer.full_name}
              </Typography>
              <Typography variant="body1" sx={{ mb: 1 }}>
                Email: {customer.email}
              </Typography>
              <Typography variant="body1" sx={{ mb: 1 }}>
                PESEL: {customer.pesel_masked ?? "brak (cudzoziemiec)"}
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                Obywatelstwo: {customer.citizenship}
              </Typography>
              <Box display="flex" gap={2} mt={2}>
                <Button variant="contained" onClick={() => setModalOpen(true)}>
                  Otwórz dostęp do konta
                </Button>
                <Button variant="outlined" onClick={() => navigate("/agent/grants")}>
                  Moje aktywne dostępy
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}
        {id && (
          <OpenAccessModal
            open={modalOpen}
            customerId={id}
            onClose={() => setModalOpen(false)}
            onCreated={(grant) => navigate(`/agent/customers/${id}/accounts?grant=${grant.id}`)}
          />
        )}
      </Box>
    </Box>
  );
}
