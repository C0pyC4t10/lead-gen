import os, sqlite3, csv
from datetime import datetime

LEADS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leads.db')
_LEADS_READY = False  # Lazy schema init flag for cold-start SQLite fallback

LEADS_COLUMNS = [
    'date', 'platform', 'business_name', 'page_url', 'category', 'followers',
    'email', 'phone', 'website', 'has_website', 'address', 'last_post_date',
    'qualification_score', 'status', 'notes', 'follow_up_date', 'open_state', 'hours_text',
    'deleted_at', 'saved_by_user_id', 'saved_by_user_name',
]

def get_conn():
    global _LEADS_READY
    conn = sqlite3.connect(LEADS_DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    if not _LEADS_READY:
        # Mark ready BEFORE calling init_db() to prevent recursion
        # (init_db also calls get_conn).
        _LEADS_READY = True
        try:
            init_db()
        except Exception:
            pass
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        platform TEXT DEFAULT '',
        business_name TEXT DEFAULT '',
        page_url TEXT DEFAULT '',
        category TEXT DEFAULT '',
        followers TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        website TEXT DEFAULT '',
        has_website TEXT DEFAULT '',
        address TEXT DEFAULT '',
        last_post_date TEXT DEFAULT '',
        qualification_score TEXT DEFAULT '',
        status TEXT DEFAULT 'new',
        notes TEXT DEFAULT '',
        follow_up_date TEXT DEFAULT '',
        open_state TEXT DEFAULT '',
        hours_text TEXT DEFAULT '',
        deleted_at TEXT DEFAULT '',
        saved_by_user_id TEXT DEFAULT '',
        saved_by_user_name TEXT DEFAULT '',
        user_id INTEGER DEFAULT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS qualified_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        date TEXT NOT NULL,
        platform TEXT DEFAULT '',
        business_name TEXT DEFAULT '',
        page_url TEXT DEFAULT '',
        category TEXT DEFAULT '',
        followers TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        website TEXT DEFAULT '',
        has_website TEXT DEFAULT '',
        address TEXT DEFAULT '',
        last_post_date TEXT DEFAULT '',
        qualification_score TEXT DEFAULT '',
        status TEXT DEFAULT 'qualified',
        notes TEXT DEFAULT '',
        follow_up_date TEXT DEFAULT '',
        open_state TEXT DEFAULT '',
        hours_text TEXT DEFAULT '',
        deleted_at TEXT DEFAULT '',
        saved_by_user_id TEXT DEFAULT '',
        saved_by_user_name TEXT DEFAULT '',
        qualified_at TEXT DEFAULT '',
        qualified_by TEXT DEFAULT '',
        user_id INTEGER DEFAULT NULL
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_leads_page_url ON leads(page_url)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_leads_user_id ON leads(user_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_qualified_leads_lead_id ON qualified_leads(lead_id)')
    conn.commit()

    _migrate_csv()
    conn.close()

def _migrate_csv():
    csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'collected_leads')
    csv_path = os.path.join(csv_dir, 'leads.csv')
    if not os.path.exists(csv_path):
        return
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM leads')
    if c.fetchone()[0] > 0:
        conn.close()
        return
    for fname in ['leads.csv']:
        path = os.path.join(csv_dir, fname)
        if not os.path.exists(path):
            continue
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cols = {k: (row.get(k) or '') for k in LEADS_COLUMNS}
                cols['user_id'] = None
                c.execute('''INSERT INTO leads (date, platform, business_name, page_url, category,
                    followers, email, phone, website, has_website, address, last_post_date,
                    qualification_score, status, notes, follow_up_date, open_state, hours_text,
                    deleted_at, saved_by_user_id, saved_by_user_name, user_id)
                    VALUES (:date, :platform, :business_name, :page_url, :category,
                    :followers, :email, :phone, :website, :has_website, :address, :last_post_date,
                    :qualification_score, :status, :notes, :follow_up_date, :open_state, :hours_text,
                    :deleted_at, :saved_by_user_id, :saved_by_user_name, :user_id)''', cols)
        conn.commit()
    print(f"[leads_db] Migrated CSV data to SQLite", flush=True)
    conn.close()

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)

def add_lead(data, user_id=None):
    conn = get_conn()
    c = conn.cursor()
    page_url = data.get('page_url', '').strip()
    if page_url:
        c.execute('SELECT id FROM leads WHERE page_url = ? AND deleted_at = ?', (page_url, ''))
        if c.fetchone():
            conn.close()
            return False, 'duplicate'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cols = {k: str(data.get(k, '')) for k in LEADS_COLUMNS}
    cols['date'] = now
    cols['deleted_at'] = ''
    cols['user_id'] = user_id
    if not cols.get('platform'):
        cols['platform'] = 'facebook'
    if not cols.get('status'):
        cols['status'] = 'new'
    c.execute('''INSERT INTO leads (date, platform, business_name, page_url, category,
        followers, email, phone, website, has_website, address, last_post_date,
        qualification_score, status, notes, follow_up_date, open_state, hours_text,
        deleted_at, saved_by_user_id, saved_by_user_name, user_id)
        VALUES (:date, :platform, :business_name, :page_url, :category,
        :followers, :email, :phone, :website, :has_website, :address, :last_post_date,
        :qualification_score, :status, :notes, :follow_up_date, :open_state, :hours_text,
        :deleted_at, :saved_by_user_id, :saved_by_user_name, :user_id)''', cols)
    conn.commit()
    conn.close()
    return True, 'Lead saved'

def get_lead_by_url(page_url, include_trashed=False):
    conn = get_conn()
    c = conn.cursor()
    if include_trashed:
        c.execute('SELECT * FROM leads WHERE page_url = ?', (page_url,))
    else:
        c.execute('SELECT * FROM leads WHERE page_url = ? AND deleted_at = ?', (page_url, ''))
    row = c.fetchone()
    conn.close()
    return row_to_dict(row)

def get_leads(filter_status=None, include_trashed=False, user_id=None, include_all_users=False):
    conn = get_conn()
    c = conn.cursor()
    where = []
    params = []
    if not include_trashed:
        where.append('deleted_at = ?')
        params.append('')
    if filter_status:
        if isinstance(filter_status, list):
            placeholders = ','.join('?' for _ in filter_status)
            where.append(f'status IN ({placeholders})')
            params.extend(filter_status)
        else:
            where.append('status = ?')
            params.append(filter_status)
    if user_id and not include_all_users:
        where.append('(user_id = ? OR user_id IS NULL)')
        params.append(user_id)
    sql = 'SELECT * FROM leads'
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY id DESC'
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def trash_lead(page_url, user_id=None):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('UPDATE leads SET deleted_at = ? WHERE page_url = ? AND deleted_at = ?', (now, page_url, ''))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def restore_lead(page_url, user_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE leads SET deleted_at = ? WHERE page_url = ? AND deleted_at != ?', ('', page_url, ''))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def delete_lead_permanently(page_url, user_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM leads WHERE page_url = ?', (page_url,))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def update_lead_status(page_url, new_status, follow_up_date=None, user_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE leads SET status = ?, follow_up_date = ? WHERE page_url = ? AND deleted_at = ?',
              (new_status, follow_up_date or '', page_url, ''))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def qualify_lead(page_url, user_id=None, user_name=''):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM leads WHERE page_url = ? AND deleted_at = ?', (page_url, ''))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    lead = dict(row)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lead['status'] = 'qualified'
    lead['qualified_at'] = now
    lead['qualified_by'] = user_name or ''
    lead['lead_id'] = lead['id']
    c.execute('''INSERT INTO qualified_leads (lead_id, date, platform, business_name, page_url,
        category, followers, email, phone, website, has_website, address, last_post_date,
        qualification_score, status, notes, follow_up_date, open_state, hours_text,
        deleted_at, saved_by_user_id, saved_by_user_name, qualified_at, qualified_by, user_id)
        VALUES (:lead_id, :date, :platform, :business_name, :page_url,
        :category, :followers, :email, :phone, :website, :has_website, :address, :last_post_date,
        :qualification_score, :status, :notes, :follow_up_date, :open_state, :hours_text,
        :deleted_at, :saved_by_user_id, :saved_by_user_name, :qualified_at, :qualified_by, :user_id)''', lead)
    c.execute('UPDATE leads SET status = ? WHERE id = ?', ('qualified', lead['id']))
    conn.commit()
    conn.close()
    return True

def get_qualified_leads():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM qualified_leads ORDER BY id DESC')
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_funnel_stats(user_id=None, is_admin=False):
    conn = get_conn()
    c = conn.cursor()
    stats = {}
    for status in ['new', 'contacted', 'qualified', 'meeting', 'proposal', 'won', 'lost']:
        if user_id and not is_admin:
            c.execute('SELECT COUNT(*) FROM leads WHERE status = ? AND deleted_at = ? AND (user_id = ? OR user_id IS NULL)',
                      (status, '', user_id))
        else:
            c.execute('SELECT COUNT(*) FROM leads WHERE status = ? AND deleted_at = ?', (status, ''))
        stats[status] = c.fetchone()[0]
    conn.close()
    return stats

def get_total_leads_count(user_id=None, is_admin=False):
    conn = get_conn()
    c = conn.cursor()
    if user_id and not is_admin:
        c.execute('SELECT COUNT(*) FROM leads WHERE deleted_at = ? AND (user_id = ? OR user_id IS NULL)', ('', user_id))
    else:
        c.execute('SELECT COUNT(*) FROM leads WHERE deleted_at = ?', ('',))
    count = c.fetchone()[0]
    conn.close()
    return count

def update_telegram_config(user_id, bot_token, chat_id=None):
    try:
        from auth_db import _use_mongo
        if _use_mongo():
            import mongo_db
            update = {'telegram_bot_token': bot_token}
            update['telegram_chat_id'] = chat_id if chat_id else None
            return bool(mongo_db.update_user(user_id, update))
        import auth_db
        conn = auth_db._sqlite_conn()
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            c = conn.cursor()
            try:
                c.execute('ALTER TABLE users ADD COLUMN telegram_bot_token TEXT DEFAULT NULL')
            except sqlite3.OperationalError:
                pass
            try:
                c.execute('ALTER TABLE users ADD COLUMN telegram_chat_id TEXT DEFAULT NULL')
            except sqlite3.OperationalError:
                pass
            if chat_id:
                c.execute('UPDATE users SET telegram_bot_token = ?, telegram_chat_id = ? WHERE id = ?', (bot_token, chat_id, user_id))
            else:
                c.execute('UPDATE users SET telegram_bot_token = ?, telegram_chat_id = NULL WHERE id = ?', (bot_token, user_id))
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False
    conn.close()

def get_telegram_config(user_id):
    """Read per-user Telegram config (bot_token, chat_id).

    On Mongo: stored in users.telegram_bot_token / telegram_chat_id.
    On SQLite: stored in auth.db users table.
    Uses auth_db._sqlite_conn() to trigger the lazy schema init — this
    prevents the "no such table: users" error on Render cold start when
    a lead-save hits this path before init_auth_db() has run.
    """
    try:
        from auth_db import _use_mongo
        if _use_mongo():
            import mongo_db
            u = mongo_db.get_user_by_id(user_id) or {}
            return {
                'bot_token': u.get('telegram_bot_token') or None,
                'chat_id':   u.get('telegram_chat_id')   or None,
            }
        import auth_db
        conn = auth_db._sqlite_conn()
        try:
            c = conn.cursor()
            try:
                c.execute('ALTER TABLE users ADD COLUMN telegram_bot_token TEXT DEFAULT NULL')
            except sqlite3.OperationalError:
                pass
            try:
                c.execute('ALTER TABLE users ADD COLUMN telegram_chat_id TEXT DEFAULT NULL')
            except sqlite3.OperationalError:
                pass
            c.execute('SELECT telegram_bot_token, telegram_chat_id FROM users WHERE id = ?', (user_id,))
            row = c.fetchone()
            if row:
                return {'bot_token': row['telegram_bot_token'], 'chat_id': row['telegram_chat_id']}
            return {'bot_token': None, 'chat_id': None}
        finally:
            conn.close()
    except Exception:
        return {'bot_token': None, 'chat_id': None}
