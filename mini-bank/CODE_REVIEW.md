# Code review mini-banku — PoC z pułapkami (na potrzeby M4)

Data: 2026-06-04. Zakres: `mini-bank/backend` (drzewo startowe = stan, który dostaje
uczestnik). Cel: potwierdzić, że zaplanowane pułapki nadają się na warsztat (5 bugów + 5
featurów M4, dema 14–23), wskazać rozjazdy dokumentacji i ryzyka niezamierzone.

Werdykt: **PoC jest zdrowy jako poligon**. Pułapki są realne, samozawarte i wykrywalne
przez czerwony test. Główny problem to **rozjazd dokumentacji** (deklarowane „4 xfail" vs
realne 11) i kilka **niezamierzonych luk** do świadomej decyzji „pułapka czy łatka".

---

## 1. Stan faktyczny test-suite (zweryfikowany)

`cd mini-bank && PYTHONPATH=backend/src python3 -m pytest -q -rxX`:

```
123 passed, 11 xfailed, 1 xpassed, 2 warnings
```

11 aktywnych `xfail` (każdy = jedna zaplanowana pułapka), nie 4:

| Bug | Test (xfail) | Plik źródłowy |
|---|---|---|
| BUG-01 | `test_transfers.py::test_concurrent_transfers_race_overdraws_account` | `transfers/concurrent_transfer.py`, `services/transfer_service.py` |
| BUG-02 | `test_timezone.py::...just_after_midnight_at_positive_offset` | `timezone_check.py` |
| BUG-03 | `test_interest.py::test_treasury_balance_many_periods_within_tolerance` | `interest.py` |
| BUG-04 | `test_fraud_score.py::test_missing_merchant_country_is_scored` | `fraud_score.py` |
| BUG-05 (×2) | `test_audit_log_immutable.py::...update/...delete_is_blocked_BUG_05` | migracja audit_log (brak triggera) |
| BUG-06 | `test_access_grant_service.py::test_is_active_grant_expired_BUG_06` | `services/access_grant_service.py:76` |
| BUG-07 | `test_audit_service.py::...payload_including_pesel_plaintext_BUG_07` | `services/audit_service.py` |
| BUG-08 | `test_sca_service.py::test_verify_amount_mismatch_rejected_BUG_08` | `services/sca_service.py:53` |
| BUG-09 | `test_idempotency.py::...different_payload_returns_conflict_BUG_09` | `middleware/idempotency.py:24` |
| BUG-10 | `test_step_up.py::test_recent_login_no_step_up_denied_BUG_10` | `middleware/step_up.py` |

**1 XPASS (do naprawy przed warsztatem):** `test_concurrent_api.py::...overdraw_account`
(e2e wariant BUG-01) przeszedł, mimo że bug jest aktywny — wyścig jest **niedeterministyczny
na poziomie e2e** (`strict=False` maskuje to). Wariant jednostkowy (`test_transfers.py`)
reprodukuje niezawodnie dzięki wstrzykniętemu `time.sleep`. Rekomendacja: dla dema 15
(BUG-01) używać wariantu jednostkowego jako bramki; e2e zostawić jako ilustrację „czemu
wyścig bywa nieuchwytny", nie jako test akceptacyjny.

---

## 2. Pięć pułapek wybranych do M4 — ocena jakości

Wszystkie ★★★★+ na warsztat (realistyczne, samozawarte, ~15–30 min, czerwony test jako
bramka). Marker `# BUG-XX PLANTED` w źródle ułatwia trenerowi orientację (uczestnik go nie
potrzebuje — wchodzi przez test).

- **BUG-03 (demo 14, TDD).** `interest.py` — cast `float` per okres kumuluje błąd
  zaokrąglenia; oracle w `Decimal`. Idealne na red-green-refactor: zdejmij xfail → czerwony →
  fix (zostań w `Decimal`) → zielony. Pieniądz, więc trafia w „money-math" (linia Audit-Log
  w commicie). Wykrywalność wysoka, zakres jeden plik.
- **BUG-01 (demo 15, systematic debugging).** Check-then-act bez zamka; `time.sleep`
  poszerza okno. Klasyczny TOCTOU / double-spend. Świetne na pętlę repro→hipoteza→fix→regresja.
  Uwaga e2e-flaky z §1.
- **BUG-08 (demo 16, security-review).** `sca_service.verify()` przyjmuje
  `request_amount`/`request_dest_iban`, ale ich NIE porównuje z `linked_*` (linie 63–82
  z komentarzem). Łamie PSD2 dynamic-linking: kod OTP na 250 PLN autoryzuje przelew 5000 PLN.
  Mocny przykład „security review znajduje to, czego testy happy-path nie łapią".
- **BUG-09 (demo 17, mock-Jira).** `idempotency.cache_lookup` zwraca odpowiedź po samym
  kluczu, ignorując `request_hash` (linia 33–34). Łamie kontrakt Stripe (ten sam klucz + inny
  payload → 409). Dobre jako „ticket z Jiry → fix": treść błędu czytana z mocka, naprawa lokalna.
- **BUG-06 (demo 18, plan mode).** `access_grant_service.is_active_grant` nie sprawdza
  `now < expires_at` (linia 89 komentarz). Wygasły JIT-grant zostaje aktywny → authz. Dobre na
  „najpierw plan mode (read-only śledztwo), potem exec", bo trzeba prześledzić ścieżkę grantu.

Rezerwa (gdyby trzeba podmienić): **BUG-02** (double tz), **BUG-04** (None-guard, łatwy),
**BUG-10** (step-up sprawdza `last_login` zamiast `last_step_up`), **BUG-05** (brak triggera
niemutowalności audytu), **REF-01** (refactor god-function `fraud_score`).

---

## 3. Rozjazdy dokumentacji (DO NAPRAWY — patrz §6 planu M4)

1. **CLAUDE.md (repo główne), bramka weryfikacji:** „`pytest mini-bank/` on `main` shows
   exactly 4 expected `xfail` (planted BUG-01..04)". **Nieaktualne** — realnie 11 xfail
   (BUG-01..10). Trzeba zmienić liczbę na 11 (lub na „wszystkie testy `@pytest.mark.planted`
   jako xfail") oraz dopisać 1 znany XPASS (e2e BUG-01) albo go usztywnić.
2. **`mini-bank/README.md:41`:** „Expected on `main` branch: 4 xfail (BUG-01..04)". To samo —
   zaktualizować do 11.
3. **`mini-bank/README.md:54`:** „More bugs (BUG-05..10) come in v2 and v3." — w drzewie są
   **już teraz** (aktywne xfail). Przeformułować na „BUG-05..10 obecne; v2/v3 odnosi się do
   migracji/feature'ów, nie do obecności bugów".
4. **Tabela README:48** wskazuje BUG-01 w `services/transfer_service.py`, a realnie wyścig
   siedzi w `transfers/concurrent_transfer.py` (transfer_service deleguje). Doprecyzować.

---

## 4. Ryzyka niezamierzone (decyzja: pułapka dydaktyczna vs łatka)

- **`approve_transfer` bez audytu** — `api/transfers.py:79`. `initiate_transfer` ma
  `@audited(action="transfer_initiated")` (linia 26), ale **ścieżka zatwierdzenia
  dual-control nie ma `@audited`**. Zatwierdzenie przelewu ponad próg AML to akcja
  konsekwentna — brak śladu audytowego jest realną luką ładu. Rekomendacja: **załatać**
  (dodać `@audited(action="transfer_approved")`) albo świadomie zostawić jako materiał do
  dema 23 (audit-export pokaże „czego w logu brakuje").
- **Wyścig w `approve_transfer`** — `api/transfers.py:93-96`. Read-modify-write na
  `src.balance` bez zamka/`SELECT FOR UPDATE`; dwóch supervisorów zatwierdzających dwa różne
  przelewy z tego samego źródła może zejść pod limit. To **ten sam wzorzec co BUG-01**, ale w
  ścieżce dual-control i bez własnego testu. Decyzja: oznaczyć jako rozszerzenie BUG-01 albo
  dopisać xfail. (Nie wybrane do M4 — notatka na przyszłość.)
- **Brak autoryzacji per-transakcja w `approve_transfer`** — `api/transfers.py:86`. Dowolny
  supervisor zatwierdzi dowolną transakcję (brak pojęcia „oddział/grupa approvera"). Najpewniej
  **zamierzone** (supervisor = zaufana rola), ale przy przejęciu konta supervisora = eskalacja.
  Zostawić jako temat do debriefu (najmniejszy przywilej).

Wniosek: poza powyższymi nie znaleziono przypadkowych defektów łamiących happy-path —
123 testy zielone, ścieżki authz (owner-check `accounts.py`, grant-check, role-gating)
spójne.

---

## 5. Struktura testów (zdrowie)

- ~40 plików: `tests/` (root, pułapki + charakteryzacja), `tests/unit`, `tests/integration`,
  `tests/e2e`. Pułapki oznaczone `@pytest.mark.planted` (11 wystąpień) — można je izolować:
  `pytest -m planted`.
- Uruchomienie hermetyczne (zgodnie z CLAUDE.md): `PYTHONPATH=backend/src python3 -m pytest`
  z katalogu `mini-bank/`. Czas ~26 s.
- Charakteryzacja REF-01 (`test_fraud_score.py`) pełni rolę siatki bezpieczeństwa przy
  refaktorze — zostaje zielona przed i po.

---

## 6. Rekomendacje (priorytet malejąco)

1. Uzgodnić CLAUDE.md + README z realnymi 11 xfail (§3) — inaczej `make verify` da fałszywy
   alarm.
2. Usztywnić lub przekwalifikować e2e BUG-01 (XPASS, §1) — dla dema 15 bramką jest wariant
   jednostkowy.
3. Zdecydować o `approve_transfer` (audyt + wyścig, §4) — minimalnie dodać `@audited`.
4. Dema 14–23 mogą ruszać na tym drzewie bez zmian w kodzie aplikacji (pułapki aktywne).
