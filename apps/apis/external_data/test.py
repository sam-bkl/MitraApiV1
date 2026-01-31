import cx_Oracle
GSM = "9422601722"
CIRCLE = 1
REQ_TYPE = "NORMAL"

pools = {}

def get_pool(zone: str):
    if zone not in pools:
        if zone == "SZ":
            pools[zone] = cx_Oracle.SessionPool(
                user="ONBOARDKL",
                password="Onboard_KL2025",
                dsn="10.19.238.38/SIMSOFT",
                min=2, max=10, increment=1, threaded=True
            )
        elif zone == "WZ":
            pools[zone] = cx_Oracle.SessionPool(
                user="ONBOARDKL",
                password="Onboard_KL2025",
                dsn="10.102.187.103/SSDB11",
                min=2, max=10, increment=1, threaded=True
            )
        elif zone == "EZ":
            pools[zone] = cx_Oracle.SessionPool(
                user="ONBOARDKL",
                password="Onboard_KL2025",
                dsn="10.189.1.3/sseast",
                min=2, max=10, increment=1, threaded=True
            )
        elif zone == "NZ":
            pools[zone] = cx_Oracle.SessionPool(
                user="ONBOARDKL",
                password="Onboard_KL2025",
                dsn="10.190.8.95/SIMIMS",
                min=2, max=10, increment=1, threaded=True
            )

    return pools[zone]


def get_zone_from_circle(circle_code: int) -> str:
    mapping = {
        77: "EZ", 51: "SZ", 71: "EZ", 73: "EZ", 78: "EZ",
        40: "SZ", 3: "WZ", 2: "NZ", 10: "WZ", 61: "NZ",
        55: "NZ", 65: "NZ", 76: "EZ", 53: "SZ", 50: "SZ",
        4: "WZ", 1: "WZ", 74: "EZ", 75: "EZ", 72: "EZ",
        56: "NZ", 59: "NZ", 79: "EZ", 54: "SZ", 41: "SZ",
        60: "NZ", 62: "NZ", 64: "NZ", 70: "EZ"
    }
    return mapping.get(circle_code)

def main():
    zone = get_zone_from_circle(CIRCLE)
    if not zone:
        print("❌ Invalid circle")
        return

    pool = get_pool(zone)
    conn = pool.acquire()
    print("----------------------------------------------------------------------------------")
    try:
        cursor = conn.cursor()
        out_cursor = cursor.var(cx_Oracle.CURSOR)

        print("Calling procedure...")
        cursor.callproc(
            "simmgmt.post_to_pre_check_sm",
            [GSM, 2, REQ_TYPE, out_cursor]
        )

        result_cursor = out_cursor.getvalue()

        print("\nColumns:")
        columns = [col[0] for col in result_cursor.description]
        for c in columns:
            print(" -", c)

        rows = result_cursor.fetchall()

        print("\nRows:")
        for row in rows:
            print(row)

        # Optional: pretty print as dict
        print("\nAs dict:")
        for row in rows:
            print(dict(zip(columns, row)))

        result_cursor.close()
        cursor.close()

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print("❌ Oracle error:", error.message)

    finally:
        pool.release(conn)

# ==============================
if __name__ == "__main__":
    main()
