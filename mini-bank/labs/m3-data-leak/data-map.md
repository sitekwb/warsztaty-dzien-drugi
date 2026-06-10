# Data Map — mini-bank (M3-Lab, 10 min w parach)

Wypełnij **kolumny 2–4** dla każdego pola. Cel: ustalić, które dane mogą w ogóle wyjść z `users`/`accounts`/`transactions` przez prompt do LLM, a które nie, i którym landing zone'em pójdą.

Kategorie klasyfikacji (kolumna 2): `PUBL` = publiczne, `WEWN` = wewnętrzne, `PII` = dane osobowe (RODO art. 4), `SC9` = szczególne kategorie (RODO art. 9), `TAJ.BANK` = tajemnica bankowa (Prawo bankowe art. 104).

Landing zone (kolumna 3): `Bedrock-VPC` = AWS Bedrock w VPC z PrivateLink, `Vertex-VPCSC` = GCP Vertex w VPC Service Controls, `AOAI-VNet` = Azure OpenAI z Private Endpoint, `Lokalnie` = model lokalny / on-prem, `Brak` = nie wolno trafić do LLM w żadnej formie.

Kto widzi (kolumna 4): `klient`, `agent`, `auditor`, `nikt-tylko-hash`, `nikt`.

## Tabela do wypełnienia

| Pole z bazy mini-banku                | Klasyfikacja | Landing zone (z dozwolonych) | Kto widzi |
|---------------------------------------|--------------|------------------------------|-----------|
| `users.email`                         |              |                              |           |
| `users.full_name`                     |              |                              |           |
| `users.pesel`                         |              |                              |           |
| `users.alt_id_value` (paszport / karta pobytu) |     |                              |           |
| `users.phone`                         |              |                              |           |
| `accounts.holder_iban`                |              |                              |           |
| `accounts.balance`                    |              |                              |           |
| `transactions.title`                  |              |                              |           |
| `transactions.category` (np. `RESTAURACJE`, `RACHUNKI`) |  |                       |           |
| `audit_log.event` (kto, kiedy, co)    |              |                              |           |

## Pytania kontrolne (5 min na koniec)

1. **Które pole jest „najbardziej toksyczne" w prompcie do LLM?** Dlaczego? (Podpowiedź: jedno pole = pełna identyfikacja + ścieżka życia finansowego.)
2. **Czy `transactions.title` można puścić do Bedrock-VPC?** Co, jeśli tytuł brzmi „Alimenty od Jan Kowalski"?
3. **`accounts.balance` — `PII`, `WEWN`, czy `TAJ.BANK`?** Uzasadnij wybór.
4. **Co dokładnie powinno się znaleźć w `audit_log.event` po użyciu LLM w mini-banku?** Trzy elementy minimum.
5. **Gdzie zero-trust się załamuje, jeśli wybierzesz `Lokalnie` dla `users.pesel`?** (Podpowiedź: kto patrzy na disk w stagingu?)

## Po wypełnieniu

Twoja tabela + odpowiedzi przejdzie do **M4-Lab1 „Karta migracji"** jako pole 3 (`Data`) z 6 wymiarów m4-s03. Nie wyrzucaj.
