import psycopg2
from psycopg2 import pool

def get_pg_conn():
    return psycopg2.connect(
        database="postgres",
        user="postgres",
        password="1tc3llKL",
        host="10.201.222.65",
        port=5432
    )


# Create pool once (at module load)
# pg_pool = pool.SimpleConnectionPool(
#     minconn=1,
#     maxconn=1,
#     user="postgres",
#     password="1tc3llKL",
#     host="10.201.222.65",
#     port=5432,
#     database="postgres"
# )

# def get_pg_conn():
#     """Get a pooled PostgreSQL connection."""
#     return pg_pool.getconn()

def put_pg_conn(conn):
    """Return the connection back to the pool."""
    pg_pool.putconn(conn)

def get_caf_id(prefix="E"):
    """
    usage :

        get_caf_id('E') 
        get_caf_id('D') 
    """
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT generate_caf_id(%s);", (prefix,))
            result = cur.fetchone()
            return result[0]
    finally:
        conn.close()

def get_sms_id():

    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT sms_seq_generator('default_seq')")
            result = cur.fetchone()
            conn.commit()
            return result[0]

    finally:
        conn.close()

def normalize_db_message(msg):
    # msg is string from postgres: "SUCCESS: something" or "ERROR: something"
    if msg.startswith("SUCCESS:"):
        return {
            "status": "success",
            "message": msg.replace("SUCCESS:", "").strip()
        }
    elif msg.startswith("ERROR:"):
        return {
            "status": "error",
            "message": msg.replace("ERROR:", "").strip()
        }
    else:
        return {
            "status": "error",
            "message": msg
        }

def update_postpaid_sim(simno, mobno,plan):
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT public.allot_sim_postpaid(%s, %s, %s)", (simno, mobno, plan))
            (msg,) = cur.fetchone()
            conn.commit()
            return normalize_db_message(msg)

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": "Internal Error: " + str(e)}

    finally:
        conn.close()

def update_prepaid_sim(simno, mobno,plan):
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT public.allot_sim_prepaid(%s, %s, %s)", (simno, mobno, plan))
            (msg,) = cur.fetchone()
            conn.commit()
            return normalize_db_message(msg)

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": "Internal Error: " + str(e)}

    finally:
        conn.close()


