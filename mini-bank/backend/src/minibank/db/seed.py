"""Deterministic demo seed: 40 customers (32 PL + 8 UA), 3 employees, ~70 accounts, ~800 transactions.

Run with: PYTHONPATH=src python3 -m minibank.db.seed
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from faker import Faker
from sqlalchemy.orm import Session

from minibank.db.models import (
    Account,
    Currency,
    Role,
    Transaction,
    TransactionStatus,
    User,
    AltIdType,
)
from minibank.db.seed_helpers import generate_iban_pl_mbank, generate_pesel
from minibank.db.session import SessionLocal, engine
from minibank.db.base import Base
from minibank.services.auth_service import hash_password
from minibank.services.category_service import categorize


SEED = 42
UKR_SURNAMES = [
    "Szewczenko", "Bojko", "Kowalenko", "Melnyk", "Bondar",
    "Tkaczenko", "Kowalczuk", "Pawluk", "Iwanenko", "Sydorenko",
]
UKR_GIVEN_NAMES = ["Olena", "Mykola", "Iryna", "Andrij", "Natalia", "Petro", "Oksana", "Vasyl"]

EMPLOYEES = [
    ("agent.helpdesk@minibank.pl", "Magdalena Pacholczyk", Role.AGENT),
    ("agent.branch@minibank.pl", "Piotr Wiśniewski", Role.AGENT),
    ("agent.supervisor@minibank.pl", "Katarzyna Lewandowska", Role.SUPERVISOR),
]

TRANSACTION_CATEGORIES = [
    # (weight, title_choices, amount_range_pln)
    (15, ["Wynagrodzenie 04/2026", "Pensja 05/2026", "Wynagrodzenie - umowa o pracę"], (4500, 18000)),
    (5, ["Składka ZUS 05/2026", "PIT-37 dopłata", "Składka zdrowotna ZUS"], (380, 2200)),
    (10, ["Czynsz 05/2026", "Opłata wspólnota", "Czynsz ul. Marszałkowska 05/2026"], (1800, 4200)),
    (12, ["Rachunek za prąd PGE", "Internet UPC 05/2026", "Gaz PGNiG", "Tauron prąd"], (80, 650)),
    (5, ["Świadczenie 800+ 05/2026", "Świadczenie rodzinne"], (800, 1600)),
    (25, ["Za pizzę", "Zwrot za bilety", "Zrzutka na prezent", "Za obiad", "Zwrot pożyczki"], (20, 800)),
    (15, ["Allegro #12345", "Zamówienie Lidl", "Biedronka zakupy", "Empik książki"], (30, 600)),
    (13, ["Zwrot pożyczki", "Naprawa auta Bosch Service", "Rachunek za telefon Orange"], (50, 1500)),
]


def _pick_category(rng: random.Random) -> tuple[str, tuple[int, int]]:
    total = sum(w for w, _, _ in TRANSACTION_CATEGORIES)
    pick = rng.uniform(0, total)
    cum = 0.0
    for w, titles, amt_range in TRANSACTION_CATEGORIES:
        cum += w
        if pick <= cum:
            return rng.choice(titles), amt_range
    return TRANSACTION_CATEGORIES[-1][1][0], TRANSACTION_CATEGORIES[-1][2]


def _random_birth(rng: random.Random) -> date:
    today = date(2026, 5, 26)
    age = rng.randint(18, 75)
    days_offset = rng.randint(0, 364)
    return date(today.year - age, 1, 1) + timedelta(days=days_offset)


def seed(db: Session) -> dict:
    """Wipe existing v1 tables, repopulate with deterministic demo data.

    Returns counts dict for verification.
    """
    db.query(Transaction).delete()
    db.query(Account).delete()
    db.query(User).delete()
    db.commit()

    fake_pl = Faker("pl_PL")
    Faker.seed(SEED)
    rng = random.Random(SEED)

    counts = {"users": 0, "accounts": 0, "transactions": 0}

    # ---- employees -----------------------------------------------------------
    employees = []
    for email, full_name, role in EMPLOYEES:
        u = User(
            email=email,
            password_hash=hash_password("Agent1234!"),
            role=role,
            full_name=full_name,
            pesel=generate_pesel(_random_birth(rng), rng.choice(["M", "F"])),
            citizenship="PL",
            phone=fake_pl.phone_number()[:15],
        )
        db.add(u)
        employees.append(u)
        counts["users"] += 1

    # ---- customers (32 PL + 8 UA) -------------------------------------------
    customers: list[User] = []
    for i in range(32):
        gender = rng.choice(["M", "F"])
        first = fake_pl.first_name_male() if gender == "M" else fake_pl.first_name_female()
        last = fake_pl.last_name_male() if gender == "M" else fake_pl.last_name_female()
        u = User(
            email=f"customer{i+1}@minibank.pl",
            password_hash=hash_password("Demo1234!"),
            role=Role.CUSTOMER,
            full_name=f"{first} {last}",
            pesel=generate_pesel(_random_birth(rng), gender),
            citizenship="PL",
            phone=f"+48 {rng.randint(500, 799)} {rng.randint(100, 999)} {rng.randint(100, 999)}",
        )
        db.add(u)
        customers.append(u)
        counts["users"] += 1

    for i in range(8):
        gender = rng.choice(["M", "F"])
        first = rng.choice(UKR_GIVEN_NAMES)
        last = rng.choice(UKR_SURNAMES)
        # 5 of 8 UA citizens have UKR-status PESEL (post-2022 special status), 3 don't.
        has_pesel = i < 5
        u = User(
            email=f"ukr{i+1}@minibank.pl",
            password_hash=hash_password("Demo1234!"),
            role=Role.CUSTOMER,
            full_name=f"{first} {last}",
            pesel=generate_pesel(_random_birth(rng), gender) if has_pesel else None,
            alt_id_type=None if has_pesel else AltIdType.RESIDENCE_CARD,
            alt_id_value=None if has_pesel else f"KK{rng.randint(100000, 999999)}",
            citizenship="UA",
            phone=f"+380 {rng.randint(50, 99)} {rng.randint(100, 999)} {rng.randint(1000, 9999)}",
        )
        db.add(u)
        customers.append(u)
        counts["users"] += 1

    db.flush()  # need ids for accounts

    # ---- accounts ------------------------------------------------------------
    accounts: list[Account] = []
    iban_idx = 0
    for c in customers:
        # everyone has a current PLN account
        a = Account(
            owner_user_id=c.id,
            holder_iban=generate_iban_pl_mbank(iban_idx),
            balance=Decimal(str(round(rng.lognormvariate(8.5, 1.2), 2))).quantize(Decimal("0.01")),
            currency=Currency.PLN,
            status="open",
            overdraft_limit=Decimal("500.00") if rng.random() < 0.3 else Decimal("0.00"),
            opened_on=date(2024, 1, 1) + timedelta(days=rng.randint(0, 600)),
        )
        accounts.append(a)
        db.add(a)
        iban_idx += 1
        # ~30% also have savings PLN
        if rng.random() < 0.30:
            a = Account(
                owner_user_id=c.id,
                holder_iban=generate_iban_pl_mbank(iban_idx),
                balance=Decimal(str(round(rng.lognormvariate(9.5, 1.0), 2))).quantize(Decimal("0.01")),
                currency=Currency.PLN,
                opened_on=date(2024, 1, 1) + timedelta(days=rng.randint(0, 600)),
            )
            accounts.append(a)
            db.add(a)
            iban_idx += 1
        # ~15% have a foreign-currency account
        if rng.random() < 0.15:
            a = Account(
                owner_user_id=c.id,
                holder_iban=generate_iban_pl_mbank(iban_idx),
                balance=Decimal(str(round(rng.lognormvariate(7.5, 1.0), 2))).quantize(Decimal("0.01")),
                currency=rng.choice([Currency.EUR, Currency.USD]),
                opened_on=date(2024, 1, 1) + timedelta(days=rng.randint(0, 600)),
            )
            accounts.append(a)
            db.add(a)
            iban_idx += 1

    counts["accounts"] = len(accounts)
    db.flush()

    # ---- transactions --------------------------------------------------------
    today = datetime(2026, 5, 26, tzinfo=timezone.utc)
    start = today - timedelta(days=182)  # ~6 months

    for _ in range(800):
        src = rng.choice(accounts)
        if src.currency != Currency.PLN:
            continue  # keep things simple in v1
        title, (lo, hi) = _pick_category(rng)
        amount = Decimal(str(rng.randint(lo * 100, hi * 100) / 100)).quantize(Decimal("0.01"))
        # 60% are P2P internal (find another customer's PLN account)
        dest = None
        dest_iban = None
        if rng.random() < 0.6:
            candidates = [a for a in accounts if a.id != src.id and a.currency == Currency.PLN]
            dest = rng.choice(candidates) if candidates else None
            if dest:
                dest_iban = dest.holder_iban
        if dest_iban is None:
            # external IBAN
            dest_iban = generate_iban_pl_mbank(900000 + rng.randint(0, 9999))
        ts = start + (today - start) * rng.random()
        trx = Transaction(
            source_account_id=src.id,
            dest_account_id=dest.id if dest else None,
            dest_iban=dest_iban,
            amount=amount,
            currency=Currency.PLN,
            title=title,
            status=TransactionStatus.COMPLETED.value,
            initiated_by_user_id=src.owner_user_id,
            created_at=ts,
            completed_at=ts,
            recipient_name=fake_pl.name(),
            category=categorize(title),
        )
        db.add(trx)
        counts["transactions"] += 1

    db.commit()
    return counts


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        counts = seed(db)
    print(f"Seeded: {counts}")


if __name__ == "__main__":
    main()
