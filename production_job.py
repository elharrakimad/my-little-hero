"""One disposable generation process. The durable parent owns the queue/journal."""
import logging
import sys


def main(order_ref):
    from order_production import get_supabase_client, normalize_order, generate_order
    from order_actions import ProductionStopped
    rows = (get_supabase_client().table('orders').select('*')
            .eq('order_ref', order_ref).eq('status', 'GENERATING').execute()).data
    if len(rows or []) != 1:
        raise RuntimeError('La commande ne peut plus être produite.')
    try:
        generate_order(normalize_order(rows[0]))
    except ProductionStopped:
        return 2
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    sys.exit(main(sys.argv[1]))
