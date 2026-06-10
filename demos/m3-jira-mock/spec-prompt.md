# Prompt startowy do Claude Code (Demo 5, Etap 1 — bootstrap z OpenAPI)

Wklej w świeżym katalogu `demo-jira/` po uruchomieniu `claude`.

---

Mam OpenAPI nieswojego API ticketowego (JiraMock mBank) pod adresem:
`https://mbank-jiramock-szkolenie.azurewebsites.net/openapi/v1.json`

Autoryzacja: nagłówek `X-API-Key: $JIRAMOCK_API_KEY` (klucz `jmk_...` jest w zmiennej
środowiskowej `JIRAMOCK_API_KEY`). Jeśli sieci/klucza brak — użyj lokalnego pliku
`fallback/issues-sample.json` jako przykładowej odpowiedzi `GET /issues`.

Zbuduj **wyłącznie do odczytu** minimalnego klienta CLI w Pythonie (tylko biblioteka
standardowa, `urllib`), który:
- czyta klucz z `JIRAMOCK_API_KEY`,
- pobiera listę ticketów `GET /api/v1/issues?limit=5` oraz, dla pierwszego z nich,
  szczegóły `GET /api/v1/issues/{id}`,
- pobiera słowniki `GET /api/v1/statuses`, `/priorities`, `/types`,
- wypisuje surowe payloady (pretty-print JSON).

Zasady bezpieczeństwa demo:
- **żadnych** metod zapisujących (POST/PATCH/DELETE) — to ma być read-only,
- nie wpisuj klucza do kodu ani do gita; tylko ze zmiennej środowiskowej,
- jeśli odpowiedź `GET` nie ma udokumentowanego schematu w specu, najpierw spróbuj
  pojedynczego wywołania i wypisz, co realnie wraca (spec opisuje tylko request bodies).

Najpierw krótki plan (jakie pliki, jakie wywołania), potem implementacja.
