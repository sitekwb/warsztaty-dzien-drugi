import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Button,
  Alert,
  Box,
} from "@mui/material";
import { accessGrantsApi, AccessGrant } from "../api/accessGrants";

interface Props {
  open: boolean;
  customerId: string;
  onClose: () => void;
  onCreated: (grant: AccessGrant) => void;
}

export function OpenAccessModal({ open, customerId, onClose, onCreated }: Props) {
  const [ticketId, setTicketId] = useState("");
  const [reason, setReason] = useState("");
  const [ttl, setTtl] = useState(30);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      const grant = await accessGrantsApi.create({
        customer_id: customerId,
        ticket_id: ticketId,
        reason,
        ttl_minutes: ttl,
      });
      onCreated(grant);
      onClose();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Nie udało się otworzyć dostępu.";
      setError(typeof msg === "string" ? msg : "Błąd walidacji formularza.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Otwórz dostęp do konta klienta</DialogTitle>
      <DialogContent>
        <Box display="flex" flexDirection="column" gap={2} mt={1}>
          <TextField
            label="Numer zgłoszenia"
            value={ticketId}
            onChange={(e) => setTicketId(e.target.value)}
            required
            fullWidth
          />
          <TextField
            label="Powód otwarcia dostępu"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            multiline
            minRows={3}
            required
            fullWidth
          />
          <TextField
            select
            label="Czas dostępu"
            value={ttl}
            onChange={(e) => setTtl(Number(e.target.value))}
          >
            <MenuItem value={15}>15 minut</MenuItem>
            <MenuItem value={30}>30 minut</MenuItem>
            <MenuItem value={60}>60 minut</MenuItem>
          </TextField>
          {error && <Alert severity="error">{error}</Alert>}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={submitting}>Anuluj</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={submitting || !ticketId || !reason}
        >
          {submitting ? "Otwieram..." : "Otwórz dostęp"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
