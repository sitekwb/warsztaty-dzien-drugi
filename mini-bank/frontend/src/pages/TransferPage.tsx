import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box, Card, CardContent, Typography, TextField, Button, MenuItem, Alert,
} from "@mui/material";
import { AppHeader } from "../components/AppHeader";
import { OtpModal } from "../components/OtpModal";
import { accountsApi, Account } from "../api/accounts";
import { transfersApi } from "../api/transfers";
import { ibanApi } from "../api/iban";
import { formatIban, normalizeIban } from "../utils/iban";
import { extractErrorDetail } from "../utils/errors";

type IbanState =
  | { kind: "idle" }
  | { kind: "validating" }
  | { kind: "valid"; bankName?: string }
  | { kind: "invalid"; message: string };

export default function TransferPage() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [src, setSrc] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [iban, setIban] = useState("");
  const [ibanState, setIbanState] = useState<IbanState>({ kind: "idle" });
  const [amount, setAmount] = useState("");
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [challenge, setChallenge] = useState<
    { id: string; amount: string; currency: string; destIban: string; recipientName: string } | null
  >(null);

  useEffect(() => {
    accountsApi.listMine().then((data) => {
      setAccounts(data);
      if (data.length > 0) setSrc(data[0].id);
    });
  }, []);

  async function handleIbanBlur() {
    const normalized = normalizeIban(iban);
    if (!normalized) {
      setIbanState({ kind: "idle" });
      return;
    }
    setIbanState({ kind: "validating" });
    try {
      const r = await ibanApi.validate(normalized);
      if (r.valid) {
        setIbanState({ kind: "valid", bankName: r.bank_name });
      } else {
        setIbanState({ kind: "invalid", message: "Niepoprawny numer IBAN" });
      }
    } catch {
      setIbanState({ kind: "invalid", message: "Nie udało się sprawdzić IBAN" });
    }
  }

  function ibanHelperText(): string {
    switch (ibanState.kind) {
      case "validating": return "Sprawdzam IBAN...";
      case "valid": return ibanState.bankName ? `✓ ${ibanState.bankName}` : "✓ IBAN poprawny";
      case "invalid": return ibanState.message;
      default: return "";
    }
  }

  const submitDisabled =
    submitting ||
    ibanState.kind === "validating" ||
    ibanState.kind === "invalid";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      const account = accounts.find((a) => a.id === src);
      if (!account) throw new Error("brak konta");
      const normalized = normalizeIban(iban);
      const result = await transfersApi.initiate({
        source_account_id: src,
        dest_iban: normalized,
        amount,
        currency: account.currency,
        title: title || undefined,
        recipient_name: recipientName,
      });
      setChallenge({
        id: result.sca_challenge_id,
        amount,
        currency: account.currency,
        destIban: formatIban(normalized),
        recipientName,
      });
    } catch (e: unknown) {
      setError(extractErrorDetail(e, "Nie udało się zainicjować przelewu."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Box>
      <AppHeader />
      <Box p={3} maxWidth={600} mx="auto">
        <Typography variant="h5" fontWeight={700} mb={3}>Nowy przelew</Typography>
        <Card>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <TextField
                select fullWidth label="Z konta" value={src}
                onChange={(e) => setSrc(e.target.value)} margin="normal" required
              >
                {accounts.map((a) => (
                  <MenuItem key={a.id} value={a.id}>
                    {a.holder_iban} — {a.balance} {a.currency}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                fullWidth label="Nazwa odbiorcy" value={recipientName}
                onChange={(e) => setRecipientName(e.target.value)}
                margin="normal" required
                slotProps={{ htmlInput: { minLength: 3, maxLength: 140 } }}
              />
              <TextField
                fullWidth label="IBAN odbiorcy" value={iban}
                onChange={(e) => setIban(e.target.value)}
                onBlur={handleIbanBlur}
                margin="normal" required
                helperText={ibanHelperText()}
                error={ibanState.kind === "invalid"}
                slotProps={{
                  formHelperText: ibanState.kind === "valid"
                    ? { sx: { color: "success.main" } }
                    : undefined,
                }}
              />
              <TextField
                fullWidth label="Kwota" type="number" value={amount}
                onChange={(e) => setAmount(e.target.value)} margin="normal"
                slotProps={{ htmlInput: { step: "0.01", min: "0.01" } }} required
              />
              <TextField
                fullWidth label="Tytuł przelewu" value={title}
                onChange={(e) => setTitle(e.target.value)} margin="normal"
              />
              {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
              {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
              <Box display="flex" gap={2} mt={3}>
                <Button variant="outlined" onClick={() => navigate("/dashboard")} disabled={submitting}>
                  Anuluj
                </Button>
                <Button type="submit" variant="contained" disabled={submitDisabled}>
                  {submitting ? "Wysyłanie..." : "Zatwierdź przelew"}
                </Button>
              </Box>
            </form>
          </CardContent>
        </Card>
        {challenge && (
          <OtpModal
            open={true}
            challengeId={challenge.id}
            amount={challenge.amount}
            currency={challenge.currency}
            destIban={challenge.destIban}
            recipientName={challenge.recipientName}
            onCancel={() => setChallenge(null)}
            onSuccess={(_tx, status) => {
              setChallenge(null);
              setSuccess(status === "completed"
                ? "Przelew zrealizowany."
                : status === "requires_dual_approval"
                ? "Przelew czeka na akceptację supervisora."
                : status === "requires_review"
                ? "Przelew skierowany do przeglądu (AML)."
                : `Status: ${status}`);
              setTimeout(() => navigate("/dashboard"), 2500);
            }}
          />
        )}
      </Box>
    </Box>
  );
}
