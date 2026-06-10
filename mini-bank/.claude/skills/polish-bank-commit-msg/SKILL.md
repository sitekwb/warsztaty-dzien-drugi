---
name: polish-bank-commit-msg
description: Use when committing changes in the mini-bank repo - enforces the Conventional-Commits-style commit format and adds a mandatory audit-log line whenever money-math files change
---

# Polish Bank Commit Message

## Overview

Every commit in this repository must be machine-parseable and audit-friendly.
Regulated banking code needs a commit trail that a reviewer (or an auditor)
can read months later without archaeology. This skill is the worked example
attendees author and adapt during Block 2: it shows that *you* package the
discipline, you do not wait for a vendor to ship it.

**Core principle:** A commit message is a contract with your future auditor.

## When to Use

Invoke before writing any commit in `mini-bank/`. If the staged changes touch
money-math files, the audit-log requirement below is mandatory, not optional.

## Format Rules

The subject line MUST match:

```
<type>(<scope>): <subject>
```

- **type** is one of: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`,
  `perf`, `audit`.
- **scope** is the affected module, lowercase, no spaces
  (e.g. `interest`, `fraud`, `transfers`, `accounts`).
- **subject** is written in **English**, imperative mood, no trailing period,
  and is at most 72 characters.

Examples:

```
fix(interest): stop float drift in compound accrual
refactor(fraud): split score() into lookup, scoring, logging seams
test(transfers): pin overdraft race characterisation
```

## Money-Math Audit Line (mandatory)

The "money-math files" are any path under:

- `src/minibank/interest.py`
- `src/minibank/fraud_score.py`
- `src/minibank/transfers/`
- `src/minibank/accounts.py`
- `src/minibank/audit.py`

If a commit changes any of these, the body MUST contain exactly one audit-log
line, on its own line, in this shape:

```
Audit: <what changed> | impact=<none|balance|score|routing> | reviewer=<name-or-TBD>
```

Example full commit:

```
fix(interest): stop float drift in compound accrual

Accrue entirely in Decimal instead of dropping into a float accumulator,
so long-horizon treasury balances no longer drift past tolerance.

Audit: compound() accrual switched Decimal->float->Decimal to pure Decimal | impact=balance | reviewer=TBD
```

## Rules Checklist (verify before committing)

1. Subject matches `<type>(<scope>): <subject>` and is English, imperative,
   no trailing period, <= 72 chars.
2. `type` is from the allowed set; `scope` is a lowercase module name.
3. If any money-math file is staged, exactly one `Audit:` line is present in
   the body with a valid `impact=` value.
4. The audit line names a reviewer or `TBD` (never left blank).
5. Do not bundle unrelated changes; one logical change per commit.

## Common Mistakes

- **Past tense subject** ("fixed the bug") -> use imperative ("fix ...").
- **Missing scope** ("fix: drift") -> name the module ("fix(interest): ...").
- **Money-math change without `Audit:` line** -> blocked; add it.
- **Non-English subject** -> the trail must be readable by every reviewer;
  keep code and commit subjects in English.
