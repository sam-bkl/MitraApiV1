from django.db import connections


def fetch_sim_swap_status(mobile_numbers):
    """
    Fetch SIM swap status via Postgres FDW using Django connection

    Returns:
        {
            "8078902546": "upgradationcomplete",
            "9492331736": "pending",
            ...
        }
    """
    if not mobile_numbers:
        return {}

    placeholders = ",".join(["%s"] * len(mobile_numbers))

    query = f"""
        SELECT gsmnumber, ACTIVATION_STATUS
        FROM oracle_caf_admin.sim_swap_data
        WHERE gsmnumber IN ({placeholders})
    """

    with connections["read"].cursor() as cursor:
        cursor.execute(query, mobile_numbers)
        rows = cursor.fetchall()

    status_map = {}

    for gsm, activation_status in rows:
        if activation_status == "SC":
            status_map[str(gsm)] = "upgradation complete"
        else:
            status_map[str(gsm)] = "pending"

    return status_map

