# Intencja do `/opsx:propose` (wkleić w Claude Code, Etap 1)

Zbuduj interaktywny kalkulator rat kredytu jako narzędzie CLI w Pythonie.

Wymagania:
- Wejście (interaktywne, prompty w terminalu): kwota kredytu, nominalne oprocentowanie
  roczne (%), liczba rat miesięcznych, typ rat (równe / malejące).
- Obliczenia:
  - raty równe (annuitet) oraz raty malejące,
  - dla każdej raty: kapitał, odsetki, saldo po racie,
  - suma odsetek za cały okres,
  - RRSO (rzeczywista roczna stopa oprocentowania) — bez opłat dodatkowych w v1.
- Wyjście: czytelny harmonogram w formie tabeli + podsumowanie (suma odsetek, RRSO).
- Walidacja wejścia: liczby dodatnie, oprocentowanie >= 0, liczba rat >= 1.

Jakość:
- testy pytest dla obu typów rat na znanych przypadkach (porównanie z ręcznie policzonymi
  wartościami), testy walidacji błędnego wejścia,
- czysty podział: logika obliczeń oddzielona od warstwy CLI (żeby logika była testowalna
  bez wejścia interaktywnego).

Najpierw spec i plan zadań, potem implementacja pod testy.
