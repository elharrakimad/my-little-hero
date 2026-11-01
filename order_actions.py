"""Owner actions and cooperative production cancellation."""

CANCELLABLE_STATUSES = frozenset({"WAITING_FOR_PAYMENT", "PAID", "GENERATING",
    "GENERATION_INTERRUPTED", "BOOKS_READY", "SHIPPED", "DELIVERED"})


class ProductionStopped(RuntimeError):
    """The order is no longer owned by the running production job."""


def cancel_order(db, order_ref, expected_status):
    if expected_status not in CANCELLABLE_STATUSES:
        return False
    result = (db.table("orders").update({"status": "CANCELLED"})
        .eq("order_ref", order_ref).eq("status", expected_status).execute())
    return bool(result.data)


def save_production_fields(db, order_ref, fields):
    # Compare-and-set prevents a late AI result or PDF from reviving cancellation.
    expected = "BOOKS_READY" if (fields.get("generation_progress") or {}).get("stage") == "complete" else "GENERATING"
    result = (db.table("orders").update(fields)
        .eq("order_ref", order_ref).eq("status", expected).execute())
    if not result.data:
        raise ProductionStopped("Commande annulée ou production arrêtée ; fichiers existants conservés.")
    return result
