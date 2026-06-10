# fallback Demo 5 — JiraMock

`issues-sample.json` to **reprezentatywny** zrzut odpowiedzi `GET /api/v1/issues`
(kształt obiektu nieudokumentowany w specu — w OpenAPI są tylko request bodies),
żeby demo zadziałało **bez sieci i bez klucza** (Claude czyta ten plik jak odpowiedź API).

Treść jest celowo „bankowa": PII w polach free-text (`description`, `comments[].body`) —
nazwiska, PESEL, IBAN, numer karty, e-mail, telefon — plus puste pole (`merchant country`),
co napędza pointę o jakości i anonimizacji.

**Przed slotem (zalecane):** odśwież realnym kluczem, żeby kształt zgadzał się z bieżącym API:
```bash
curl -s -H "X-API-Key: $JIRAMOCK_API_KEY" \
  'https://mbank-jiramock-szkolenie.azurewebsites.net/api/v1/issues?limit=5' \
  > demos/m3-jira-mock/fallback/issues-sample.json
```
Klucz `jmk_...` generujesz po zalogowaniu w UI (`/Account/Profile`, hasło demo `demo`).
