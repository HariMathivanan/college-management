import os
import pymysql
import pymysql.cursors
import razorpay
from decimal import Decimal, ROUND_HALF_UP

# ─── Razorpay Configuration ───────────────────────────────────────────────────

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')


def get_razorpay_client():
    """Get Razorpay client instance"""
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise RuntimeError('Razorpay credentials not configured in environment variables')
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def get_allocation_splits(purpose):
    """Get donation allocation splits based on purpose"""
    purpose = (purpose or '').strip()
    if purpose == 'Scholarship Fund':
        return [
            ('Scholarships', Decimal('0.60')),
            ('Student Support', Decimal('0.25')),
            ('Operations', Decimal('0.15'))
        ]
    if purpose == 'Infrastructure Development':
        return [
            ('Infrastructure', Decimal('0.60')),
            ('Operations', Decimal('0.20')),
            ('Student Support', Decimal('0.20'))
        ]
    if purpose == 'Student Support':
        return [
            ('Student Support', Decimal('0.65')),
            ('Scholarships', Decimal('0.20')),
            ('Operations', Decimal('0.15'))
        ]
    if purpose == 'Research Initiative':
        return [
            ('Research', Decimal('0.50')),
            ('Infrastructure', Decimal('0.25')),
            ('Operations', Decimal('0.25'))
        ]
    if purpose == 'Sports & Culture':
        return [
            ('Events', Decimal('0.50')),
            ('Community Outreach', Decimal('0.30')),
            ('Student Support', Decimal('0.20'))
        ]
    # Default split for General Fund
    return [
        ('Scholarships', Decimal('0.35')),
        ('Infrastructure', Decimal('0.25')),
        ('Student Support', Decimal('0.20')),
        ('Operations', Decimal('0.20'))
    ]


def auto_allocate_donation(cur, donation_id, amount, purpose):
    """Auto-allocate donation to different categories based on purpose"""
    amount = Decimal(str(amount or '0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if amount <= 0:
        return
    
    splits = get_allocation_splits(purpose)
    remainder = amount
    
    for index, (category, ratio) in enumerate(splits):
        if index == len(splits) - 1:
            allocation = remainder
        else:
            allocation = (amount * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            remainder -= allocation
        
        if allocation > 0:
            cur.execute(
                "INSERT INTO donation_spending (donation_id, amount, category, description) VALUES (%s, %s, %s, %s)",
                (donation_id, str(allocation), category, f"Auto allocation to {category}")
            )


def ensure_staff_schema():
    """Ensure staff table and user role enum are set up correctly"""
    from config import db
    with db() as (conn, cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL,
                department VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cur.execute("ALTER TABLE users MODIFY role ENUM('admin','alumni','student','staff') NOT NULL DEFAULT 'alumni'")


def ensure_donation_schema():
    """Ensure donation_spending table exists"""
    from config import db
    with db() as (conn, cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS donation_spending (
                id INT AUTO_INCREMENT PRIMARY KEY,
                donation_id INT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                category VARCHAR(100) DEFAULT 'General',
                description TEXT NOT NULL,
                spent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE
            )
        """)
        try:
            cur.execute("ALTER TABLE donation_spending ADD COLUMN category VARCHAR(100) DEFAULT 'General'")
        except Exception:
            pass

# ─── Database Configuration ───────────────────────────────────────────────────

DB_CONFIG = {
    'host':        os.getenv('DB_HOST', 'localhost'),
    'port':        int(os.getenv('DB_PORT', '3306')),
    'user':        os.getenv('DB_USER', 'root'),
    'password':    os.getenv('DB_PASSWORD', ''),
    'db':          os.getenv('DB_NAME', 'alumni_db'),
    'charset':     'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

# ─── Connection Helper ────────────────────────────────────────────────────────

def get_connection():
    """
    Returns a new PyMySQL connection using DB_CONFIG.
    Usage:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT ...")
                result = cur.fetchall()
            conn.commit()
        finally:
            conn.close()
    """
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.err.OperationalError as exc:
        raise RuntimeError(
            "Unable to connect to the MySQL database. Make sure MySQL is running and credentials match."
            f" Original error: {exc}"
        ) from exc


# ─── Context-manager helper (optional convenience) ────────────────────────────

class db:
    """
    Convenience context manager — auto-closes connection.
    Usage:
        with db() as (conn, cur):
            cur.execute("SELECT ...")
            rows = cur.fetchall()
        # conn.commit() is called automatically on exit (no exception)
    """
    def __enter__(self):
        self.conn = get_connection()
        self.cur  = self.conn.cursor()
        return self.conn, self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        self.cur.close()
        self.conn.close()
        return False   # re-raise any exception


# ─── Initialize Database Schema ────────────────────────────────────────────────

ensure_staff_schema()
ensure_donation_schema()
