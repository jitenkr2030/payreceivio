"""
Reconciliation services - import, matching engine, approval.

The matching engine uses a multi-pass approach:
1. Exact UTR match (100% confidence)
2. Exact reference match + amount (95%)
3. Amount + customer name in description (75%)
4. Amount-only match (50%)
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List

from django.db import transaction
from django.utils import timezone

from .models import BankAccount, BankStatement, BankTransaction, ReconciliationMatch


def import_bank_statement_csv(organization, bank_account, csv_rows, statement_date=None, user=None) -> BankStatement:
    """Import a CSV bank statement. csv_rows is list of dict rows."""
    statement_date = statement_date or date.today()
    statement = BankStatement.objects.create(
        organization=organization,
        company=bank_account.company,
        branch=bank_account.branch,
        bank_account=bank_account,
        statement_date=statement_date,
        source="csv",
        imported_by=user,
        created_by=user,
        updated_by=user,
    )
    credits = Decimal("0")
    debits = Decimal("0")
    txn_count = 0
    for row in csv_rows:
        txn_date = _parse_date(row.get("date") or row.get("transaction_date") or row.get("Date"))
        if not txn_date:
            continue
        amount_str = (row.get("amount") or row.get("Amount") or "0").replace(",", "")
        try:
            amount = Decimal(str(amount_str))
        except Exception:
            continue
        txn_type = row.get("type") or row.get("Type") or ("credit" if amount > 0 else "debit")
        if amount < 0:
            amount = abs(amount)
        txn = BankTransaction.objects.create(
            organization=organization,
            company=bank_account.company,
            branch=bank_account.branch,
            bank_account=bank_account,
            statement=statement,
            transaction_date=txn_date,
            value_date=_parse_date(row.get("value_date")) if row.get("value_date") else None,
            txn_type=txn_type.lower(),
            amount=amount,
            description=row.get("description") or row.get("narration") or row.get("Description") or "",
            reference_number=row.get("reference") or row.get("ref") or row.get("Reference") or "",
            utr_number=row.get("utr") or row.get("UTR") or _extract_utr(row.get("description", "")),
            counterparty=row.get("counterparty") or row.get("name") or "",
            balance_after=_parse_decimal(row.get("balance")),
            created_by=user,
            updated_by=user,
        )
        if txn.txn_type == "credit":
            credits += amount
        else:
            debits += amount
        txn_count += 1

    statement.total_credits = credits
    statement.total_debits = debits
    statement.transaction_count = txn_count
    statement.unmatched_count = txn_count
    statement.save()

    # Run auto-matching
    auto_match_transactions(organization)
    return statement


def _parse_date(s):
    if not s:
        return None
    if isinstance(s, (date, datetime)):
        return s if isinstance(s, date) else s.date()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(s):
    if not s:
        return None
    try:
        return Decimal(str(s).replace(",", ""))
    except Exception:
        return None


def _extract_utr(description: str) -> str:
    """Try to extract a UTR from a bank narrative (common Indian patterns)."""
    import re
    if not description:
        return ""
    # Common UTR formats: N03425XXXXXX, UTR/N03425XXXXXX, 12-digit alphanumeric
    patterns = [
        r"\bN\d{10,12}\b",
        r"\bUTR[/:\s]*([A-Z0-9]{12,22})\b",
        r"\b([A-Z0-9]{12,22})\b",
    ]
    for p in patterns:
        m = re.search(p, description, re.IGNORECASE)
        if m:
            return m.group(1) if m.lastindex else m.group(0)
    return ""


@transaction.atomic
def auto_match_transactions(organization):
    """
    Run the matching engine on all unmatched credit transactions.
    For each, suggest a payment match.
    """
    from apps.payments.models import Payment

    unmatched_txns = BankTransaction.objects.filter(
        organization=organization,
        status="unmatched",
        txn_type="credit",
    )

    for txn in unmatched_txns:
        # Pass 1: exact UTR match
        if txn.utr_number:
            payment = Payment.objects.filter(
                organization=organization,
                reference=txn.utr_number,
                status="confirmed",
            ).first()
            if payment:
                _create_match(txn, payment, "auto", Decimal("100"),
                              {"criterion": "utr_exact"})
                continue

        # Pass 2: exact reference match
        if txn.reference_number:
            payment = Payment.objects.filter(
                organization=organization,
                reference=txn.reference_number,
                status="confirmed",
            ).first()
            if payment:
                _create_match(txn, payment, "auto", Decimal("95"),
                              {"criterion": "reference_exact"})
                continue

        # Pass 3: amount + customer name in description
        # Try to find a payment with matching amount and customer name in description
        candidate_payments = Payment.objects.filter(
            organization=organization,
            amount=txn.amount,
            status="confirmed",
            is_reconciled=False,
        )
        best_match = None
        best_score = Decimal("0")
        for p in candidate_payments:
            score = _score_match(txn, p)
            if score > best_score:
                best_score = score
                best_match = p

        if best_match and best_score >= Decimal("50"):
            _create_match(txn, best_match, "suggested", best_score,
                          {"criterion": "amount_and_description"})

    # Update statement counts
    for stmt in BankStatement.objects.filter(organization=organization, is_fully_processed=False):
        matched = stmt.transactions.filter(status="matched").count()
        suggested = stmt.transactions.filter(status="suggested").count()
        unmatched = stmt.transactions.filter(status="unmatched").count()
        stmt.matched_count = matched
        stmt.unmatched_count = unmatched
        if unmatched == 0 and stmt.transaction_count > 0:
            stmt.is_fully_processed = True
        stmt.save()


def _score_match(txn, payment) -> Decimal:
    """Compute a 0-100 match score between a bank txn and a payment."""
    score = Decimal("0")
    if txn.amount == payment.amount:
        score += Decimal("50")
    elif abs(txn.amount - payment.amount) <= Decimal("1"):
        score += Decimal("40")
    # Customer name in description
    if payment.customer and payment.customer.name and payment.customer.name.lower() in (txn.description or "").lower():
        score += Decimal("25")
    # Date proximity
    if txn.transaction_date and payment.payment_date:
        diff = abs((txn.transaction_date - payment.payment_date).days)
        if diff == 0:
            score += Decimal("25")
        elif diff <= 3:
            score += Decimal("15")
        elif diff <= 7:
            score += Decimal("5")
    return min(score, Decimal("100"))


def _create_match(txn, payment, match_type, confidence, criteria):
    """Create a reconciliation match and update statuses."""
    ReconciliationMatch.objects.get_or_create(
        bank_transaction=txn, payment=payment,
        defaults={
            "match_type": match_type,
            "confidence": confidence,
            "match_criteria": criteria,
        }
    )
    if match_type == "auto" and confidence >= Decimal("95"):
        # Auto-approve high-confidence matches
        approve_match(txn, payment)
    else:
        txn.status = "suggested"
        txn.matched_payment = payment
        txn.match_confidence = confidence
        txn.save()


@transaction.atomic
def approve_match(txn: BankTransaction, payment, user=None):
    """Approve a suggested match."""
    txn.status = "matched"
    txn.matched_payment = payment
    txn.matched_at = timezone.now()
    txn.matched_by = user
    txn.save()
    payment.is_reconciled = True
    payment.reconciled_with = txn
    payment.save()
    # Update match record
    match = ReconciliationMatch.objects.filter(bank_transaction=txn, payment=payment).first()
    if match:
        match.match_type = "approved"
        match.approved_by = user
        match.approved_at = timezone.now()
        match.save()


@transaction.atomic
def ignore_transaction(txn: BankTransaction, user=None):
    """Mark a bank transaction as ignored (e.g. bank charges)."""
    txn.status = "ignored"
    txn.save()
