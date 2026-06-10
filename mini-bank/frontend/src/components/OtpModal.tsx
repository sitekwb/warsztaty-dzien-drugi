import { useEffect, useState } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, Alert, Box, Typography,
} from "@mui/material";
import { scaApi } from "../api/sca";
import { notificationsApi } from "../api/notifications";
import { extractErrorDetail } from "../utils/errors";

interface Props {
  open: boolean;
  challengeId: string;
  amount: string;
  currency: string;
  destIban: string;
  recipientName: string;
  onSuccess: (transactionId: string, status: string) => void;
  onCancel: () => void;
}

export function OtpModal({ open, challengeId, amount, currency, destIban, recipientName, onSuccess, onCancel }: Props) {
  const [code, setCode] = useState("");
  const [hint, setHint] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    notificationsApi.listMine().then((rows) => {
      const newest = rows[0];
      if (newest) setHint(newest.body);
    });
  }, [open]);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      const r = await scaApi.verify(challengeId, code);
      onSuccess(r.transaction_id, r.status);
    } catch (e: unknown) {
      setError(extractErrorDetail(e, "Niepoprawny kod."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} maxWidth="sm" fullWidth>
      <DialogTitle>Autoryzacja przelewu (SCA)</DialogTitle>
      <DialogContent>
        <Box display="flex" flexDirection="column" gap={2} mt={1}>
          <Typography>
            Wpisz 6-cyfrowy kod, który otrzymałeś na powiadomienie.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Przelew <strong>{amount} {currency}</strong> na rzecz{" "}
            <strong>{recipientName}</strong>, IBAN <strong>{destIban}</strong>
          </Typography>
          {hint && (
            <Alert severity="info">
              Mock SMS: {hint}
            </Alert>
          )}
          <TextField
            label="Kod"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            slotProps={{ htmlInput: { maxLength: 6, inputMode: "numeric", pattern: "[0-9]{6}" } }}
            fullWidth
            autoFocus
          />
          {error && <Alert severity="error">{error}</Alert>}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={submitting}>Anuluj</Button>
        <Button variant="contained" onClick={handleSubmit}
                disabled={submitting || code.length !== 6}>
          {submitting ? "Weryfikuję..." : "Zatwierdź"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
