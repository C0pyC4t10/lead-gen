"""MongoDB Atlas storage layer for the lead-gen server.

Replaces SQLite (auth.db) and CSV-based lead storage.
Reads connection from MONGODB_URI env var.

Code style: sync (server.py is sync — pymongo, not motor).
"""
import os
import time
import threading
import datetime
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure, ConfigurationError

try:
    import certifi
    _TLS_CA = certifi.where()
except Exception:
    _TLS_CA = None

MONGO_URI = os.environ.get('MONGODB_URI', '').strip()
DB_NAME = os.environ.get('MONGODB_DB', 'scraven')

_client = None
_db = None
_lock = threading.Lock()
_mongo_ready = False  # Set True ONLY after a successful connect (and indexes)


def _connect_with_retry(max_attempts=3, base_delay=1.0):
    """Connect to MongoDB with exponential backoff.

    Tighter budget than before: max ~7s total. We only block the
    init thread on this — request threads short-circuit via
    _mongo_ready and fall back to SQLite until this returns.
    """
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            kwargs = dict(
                serverSelectionTimeoutMS=6000,
                connectTimeoutMS=6000,
                socketTimeoutMS=15000,
                retryWrites=False,
                appname='scraven-render',
                tls=True,
                tlsAllowInvalidCertificates=False,
            )
            if _TLS_CA:
                kwargs['tlsCAFile'] = _TLS_CA
            _client = MongoClient(MONGO_URI, **kwargs)
            _client.admin.command('ping')
            print(f"[mongo] connected on attempt {attempt}", flush=True)
            return _client
        except (ServerSelectionTimeoutError, ConnectionFailure, ConfigurationError, Exception) as e:
            last_err = e
            err_short = str(e).split(',')[0][:140]
            print(f"[mongo] attempt {attempt}/{max_attempts} failed: {err_short}", flush=True)
            try:
                if _client:
                    _client.close()
            except Exception:
                pass
            _client = None
            if attempt < max_attempts:
                time.sleep(base_delay * (2 ** (attempt - 1)))  # 1s, 2s, 4s
    print(f"[mongo] giving up after {max_attempts} attempts; last error: {str(last_err).split(chr(10))[0][:200]}", flush=True)
    return None


def get_db():
    """Return the cached pymongo database handle, or None if not yet connected.

    NOTE: This NEVER triggers a connect. Connection is owned by the
    background init thread in server.py. Request threads must call
    is_ready() first; if False, they should use the SQLite fallback.
    """
    global _db
    if not MONGO_URI or not _mongo_ready:
        return None
    return _db


def is_ready():
    """True only after a successful connect + index creation."""
    return _mongo_ready


def wait_ready(max_ms=2500, step_ms=100):
    """Briefly block waiting for the background init to complete.
    Returns True if ready within the budget, False otherwise. Use this
    in request threads instead of falling back to SQLite on cold start.
    """
    if _mongo_ready:
        return True
    import time as _t
    waited = 0
    while waited < max_ms:
        _t.sleep(step_ms / 1000.0)
        waited += step_ms
        if _mongo_ready:
            return True
    return False


def init_and_get_db():
    """Connect synchronously, mark ready, return db. Called ONCE by the
    background init thread in server.py."""
    global _client, _db, _mongo_ready
    if not MONGO_URI:
        return None
    with _lock:
        if _mongo_ready:
            return _db
        client = _connect_with_retry()
        if client is None:
            _mongo_ready = False
            return None
        _client = client
        _db = _client[DB_NAME]
        _ensure_indexes(_db)
        _mongo_ready = True
        return _db

def _ensure_indexes(db):
    """Create indexes used by the lead-gen queries."""
    try:
        db.users.create_index([('email', ASCENDING)], unique=True)
        db.sessions.create_index([('token', ASCENDING)], unique=True)
        db.sessions.create_index([('user_id', ASCENDING)])
        db.sessions.create_index([('created_at', ASCENDING)], expireAfterSeconds=60 * 60 * 24 * 30)
        db.leads.create_index([('page_url', ASCENDING), ('saved_by_user_id', ASCENDING)])
        db.leads.create_index([('saved_by_user_id', ASCENDING), ('deleted_at', ASCENDING)])
        db.leads.create_index([('status', ASCENDING)])
        db.leads.create_index([('date', DESCENDING)])
        db.qualified_leads.create_index([('page_url', ASCENDING), ('qualified_at', ASCENDING)], unique=True)
        db.qualified_leads.create_index([('qualified_at', DESCENDING)])
        db.daily_qualified.create_index([('date', DESCENDING)])
        db.daily_qualified.create_index([('page_url', ASCENDING), ('date', ASCENDING)], unique=True)
        # Outreach tracking: one collection per outreach log entry
        db.outreach_logs.create_index([('page_url', ASCENDING), ('created_at', DESCENDING)])
        db.outreach_logs.create_index([('logged_by_user_id', ASCENDING), ('created_at', DESCENDING)])
        db.outreach_logs.create_index([('qualified_lead_id', ASCENDING)])
        # Standard-quality remarks: free-form notes about a qualified lead
        db.qualified_remarks.create_index([('page_url', ASCENDING), ('created_at', DESCENDING)])
        db.qualified_remarks.create_index([('qualified_lead_id', ASCENDING)])
        db.qualified_remarks.create_index([('author_user_id', ASCENDING), ('created_at', DESCENDING)])
        db.fcommerce_leads.create_index([('page_url', ASCENDING)], unique=True)
        db.linkedin_leads.create_index([('url', ASCENDING)])
        db.maps_leads.create_index([('page_url', ASCENDING)])
    except Exception as e:
        print(f"[mongo] index creation warning: {e}", flush=True)

# ── Helpers ──────────────────────────────────────────────────────────
def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def to_object_id(value):
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

def serialize(doc):
    """Convert ObjectId to string and datetime to ISO for JSON response."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize(d) for d in doc]
    if isinstance(doc, dict):
        out = {}
        for k, v in doc.items():
            if k == '_id':
                out['id'] = str(v)
            elif isinstance(v, ObjectId):
                out[k] = str(v)
            elif isinstance(v, datetime.datetime):
                out[k] = v.isoformat() if v.tzinfo else v.isoformat() + 'Z'
            elif isinstance(v, dict):
                out[k] = serialize(v)
            elif isinstance(v, list):
                out[k] = [serialize(x) if isinstance(x, (dict, list)) else x for x in v]
            else:
                out[k] = v
        return out
    return doc

def get_user_by_email(email):
    db = get_db()
    if db is None:
        return None
    return db.users.find_one({'email': email.lower().strip()})

def get_user_by_id(uid):
    db = get_db()
    if db is None:
        return None
    return db.users.find_one({'_id': to_object_id(uid)})

def create_user(name, email, password_hash, password_salt, role='user', subscription_tier='free'):
    db = get_db()
    if db is None:
        return None
    now = now_iso()
    doc = {
        'name': name,
        'email': email.lower().strip(),
        'password_hash': password_hash,
        'password_salt': password_salt,
        'role': role,
        'email_verified': 1,
        'verification_code': None,
        'verification_expires': None,
        'leads_used': 0,
        'subscription_tier': subscription_tier,
        'telegram_notifications': 1,
        'password_reset_token': None,
        'password_reset_expires': None,
        'avatar_url': None,
        'created_at': now,
        'updated_at': now,
    }
    result = db.users.insert_one(doc)
    doc['_id'] = result.inserted_id
    return doc

def create_session(user_id, token, ttl_days=30):
    db = get_db()
    if db is None:
        return None
    db.sessions.insert_one({
        'user_id': to_object_id(user_id),
        'token': token,
        'created_at': now_iso(),
    })

def get_user_from_token(token):
    db = get_db()
    if db is None:
        return None
    sess = db.sessions.find_one({'token': token})
    if not sess:
        return None
    user = db.users.find_one({'_id': sess['user_id']})
    return user

def delete_session(token):
    db = get_db()
    if db is None:
        return
    db.sessions.delete_one({'token': token})

def delete_sessions_for_user(user_id):
    db = get_db()
    if db is None:
        return
    db.sessions.delete_many({'user_id': to_object_id(user_id)})

def update_user(user_id, update):
    db = get_db()
    if db is None:
        return
    update['updated_at'] = now_iso()
    db.users.update_one({'_id': to_object_id(user_id)}, {'$set': update})

def soft_delete_user(user_id):
    db = get_db()
    if db is None:
        return False
    try:
        oid = to_object_id(user_id)
        user = db.users.find_one({'_id': oid})
        if user:
            new_email = (user.get('email', '') or '') + '--deleted--' + str(user_id)
            db.users.update_one({'_id': oid}, {'$set': {'deleted_at': now_iso(), 'email': new_email}})
        db.sessions.delete_many({'user_id': str(user_id)})
        return True
    except Exception:
        return False

def restore_user(user_id):
    db = get_db()
    if db is None:
        return False
    try:
        oid = to_object_id(user_id)
        user = db.users.find_one({'_id': oid})
        if not user:
            return False
        # Strip the '--deleted--<uid>' suffix from the email added by soft_delete_user
        original_email = (user.get('email', '') or '')
        suffix = '--deleted--' + str(user_id)
        if original_email.endswith(suffix):
            original_email = original_email[:-len(suffix)]
        db.users.update_one(
            {'_id': oid},
            {'$set': {'deleted_at': None, 'email': original_email}}
        )
        return True
    except Exception:
        return False

def list_trashed_users():
    db = get_db()
    if db is None:
        return []
    return list(db.users.find({'deleted_at': {'$ne': None}}, {'password_hash': 0, 'password_salt': 0}).sort('deleted_at', DESCENDING))

def delete_user(user_id):
    db = get_db()
    if db is None:
        return False
    from bson import ObjectId
    try:
        oid = to_object_id(user_id)
        db.users.delete_one({'_id': oid})
        db.sessions.delete_many({'user_id': str(user_id)})
        return True
    except Exception:
        return False

def list_users(exclude_trashed=False):
    db = get_db()
    if db is None:
        return []
    q = {}
    if exclude_trashed:
        q['deleted_at'] = None
    cursor = db.users.find(q, {'password_hash': 0, 'password_salt': 0}).sort('created_at', DESCENDING)
    return list(cursor)

def count_users_grouped_by_role():
    db = get_db()
    if db is None:
        return {}
    pipeline = [{'$group': {'_id': '$role', 'count': {'$sum': 1}}}]
    return {r['_id']: r['count'] for r in db.users.aggregate(pipeline)}

# ── Leads ────────────────────────────────────────────────────────────
def save_lead(data, user_id):
    db = get_db()
    if db is None:
        return None
    now = now_iso()
    doc = {
        'date': data.get('date', now[:10]),
        'platform': data.get('platform', ''),
        'business_name': data.get('business_name', ''),
        'page_url': data.get('page_url', ''),
        'category': data.get('category', ''),
        'followers': str(data.get('followers', '')),
        'email': data.get('email', ''),
        'phone': data.get('phone', ''),
        'website': data.get('website', ''),
        'has_website': data.get('has_website', ''),
        'address': data.get('address', ''),
        'last_post_date': data.get('last_post_date', ''),
        'qualification_score': str(data.get('qualification_score', '')),
        'status': data.get('status', 'new'),
        'notes': data.get('notes', ''),
        'follow_up_date': data.get('follow_up_date', ''),
        'open_state': data.get('open_state', ''),
        'hours_text': data.get('hours_text', ''),
        'deleted_at': None,
        'saved_by_user_id': to_object_id(user_id),
        'saved_by_user_name': data.get('saved_by_user_name', ''),
        'created_at': now,
    }
    existing = db.leads.find_one({
        'page_url': doc['page_url'],
        'saved_by_user_id': doc['saved_by_user_id'],
        'deleted_at': None,
    })
    if existing:
        return {'duplicate': True, 'id': str(existing['_id'])}
    result = db.leads.insert_one(doc)
    doc['_id'] = result.inserted_id
    return doc

def find_lead_by_url(page_url, user_id=None, is_admin=False, include_trashed=False):
    db = get_db()
    if db is None:
        return None
    q = {'page_url': page_url}
    if not is_admin and user_id is not None:
        q['saved_by_user_id'] = to_object_id(user_id)
    if not include_trashed:
        q['deleted_at'] = None
    return db.leads.find_one(q)

def list_leads(user_id=None, is_admin=False, status=None, include_trashed=False, limit=None):
    db = get_db()
    if db is None:
        return []
    q = {}
    if not is_admin and user_id is not None:
        q['saved_by_user_id'] = to_object_id(user_id)
    if not include_trashed:
        q['deleted_at'] = None
    if status:
        q['status'] = status
    cursor = db.leads.find(q).sort('created_at', DESCENDING)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)

def list_trashed_leads(user_id=None, is_admin=False):
    db = get_db()
    if db is None:
        return []
    q = {'deleted_at': {'$ne': None}}
    if not is_admin and user_id is not None:
        q['saved_by_user_id'] = to_object_id(user_id)
    return list(db.leads.find(q).sort('deleted_at', DESCENDING))

def update_lead_status(page_url, user_id, status, follow_up_date=None):
    db = get_db()
    if db is None:
        return False
    update = {'status': status}
    if follow_up_date:
        update['follow_up_date'] = follow_up_date
    result = db.leads.update_one(
        {'page_url': page_url, 'saved_by_user_id': to_object_id(user_id)},
        {'$set': update},
    )
    return result.modified_count > 0

def trash_lead(page_url, user_id):
    db = get_db()
    if db is None:
        return False
    result = db.leads.update_one(
        {'page_url': page_url, 'saved_by_user_id': to_object_id(user_id), 'deleted_at': None},
        {'$set': {'deleted_at': now_iso(), 'status': 'trashed'}},
    )
    return result.modified_count > 0

def restore_lead(page_url, user_id):
    db = get_db()
    if db is None:
        return False
    result = db.leads.update_one(
        {'page_url': page_url, 'saved_by_user_id': to_object_id(user_id)},
        {'$set': {'deleted_at': None, 'status': 'new'}},
    )
    return result.modified_count > 0

def purge_lead(page_url, user_id):
    db = get_db()
    if db is None:
        return False
    result = db.leads.delete_one({
        'page_url': page_url,
        'saved_by_user_id': to_object_id(user_id),
        'deleted_at': {'$ne': None},
    })
    return result.deleted_count > 0

def bulk_trash(page_urls, user_id):
    db = get_db()
    if db is None:
        return 0
    now = now_iso()
    ids = [to_object_id(user_id)]
    count = 0
    for url in page_urls:
        r = db.leads.update_one(
            {'page_url': url, 'saved_by_user_id': ids[0], 'deleted_at': None},
            {'$set': {'deleted_at': now, 'status': 'trashed'}},
        )
        if r.modified_count:
            count += 1
    return count

def bulk_restore(page_urls, user_id):
    db = get_db()
    if db is None:
        return 0
    count = 0
    for url in page_urls:
        r = db.leads.update_one(
            {'page_url': url, 'saved_by_user_id': to_object_id(user_id)},
            {'$set': {'deleted_at': None, 'status': 'new'}},
        )
        if r.modified_count:
            count += 1
    return count

def bulk_purge(page_urls, user_id):
    db = get_db()
    if db is None:
        return 0
    count = 0
    for url in page_urls:
        r = db.leads.delete_one({
            'page_url': url,
            'saved_by_user_id': to_object_id(user_id),
            'deleted_at': {'$ne': None},
        })
        if r.deleted_count:
            count += 1
    return count

def lead_action(page_url, user_id, action):
    db = get_db()
    if db is None:
        return False
    if action == 'qualified':
        update = {'status': 'qualified', 'qualification_score': '90'}
    elif action == 'contacted':
        update = {'status': 'contacted'}
    elif action == 'reset':
        update = {'status': 'new', 'qualification_score': ''}
    elif action == 'disqualify':
        db.leads.delete_one({'page_url': page_url, 'saved_by_user_id': to_object_id(user_id)})
        return True
    else:
        return False
    r = db.leads.update_one(
        {'page_url': page_url, 'saved_by_user_id': to_object_id(user_id)},
        {'$set': update},
    )
    return r.modified_count > 0

def count_trashed(user_id=None, is_admin=False):
    db = get_db()
    if db is None:
        return 0
    q = {'deleted_at': {'$ne': None}}
    if not is_admin and user_id is not None:
        q['saved_by_user_id'] = to_object_id(user_id)
    return db.leads.count_documents(q)

def funnel_stats(user_id=None, is_admin=False):
    db = get_db()
    if db is None:
        return {'total': 0, 'breakdown': {}}
    q = {'deleted_at': None}
    if not is_admin and user_id is not None:
        q['saved_by_user_id'] = to_object_id(user_id)
    total = db.leads.count_documents(q)
    pipeline = [
        {'$match': q},
        {'$group': {'_id': '$status', 'count': {'$sum': 1}}},
    ]
    breakdown = {r['_id']: r['count'] for r in db.leads.aggregate(pipeline)}
    return {'total': total, 'breakdown': breakdown}

def get_last_lead(user_id):
    db = get_db()
    if db is None:
        return None
    return db.leads.find_one(
        {'saved_by_user_id': to_object_id(user_id), 'deleted_at': None},
        sort=[('created_at', DESCENDING)],
    )

# ── Qualified leads ──────────────────────────────────────────────────
def save_qualified_lead(lead, qualified_by_user_id):
    db = get_db()
    if db is None:
        return False
    doc = {
        'lead_id': to_object_id(lead.get('id')) if lead.get('id') else None,
        'page_url': lead.get('page_url', ''),
        'business_name': lead.get('business_name', ''),
        'phone': lead.get('phone', ''),
        'email': lead.get('email', ''),
        'platform': lead.get('platform', ''),
        'category': lead.get('category', ''),
        'qualification_score': str(lead.get('qualification_score', '')),
        'qualified_at': lead.get('qualified_at') or now_iso(),
        'qualified_by': to_object_id(qualified_by_user_id),
        'qualified_by_name': lead.get('qualified_by_name', ''),
        'saved_by_user_id': to_object_id(lead.get('saved_by_user_id')) if lead.get('saved_by_user_id') else None,
        'notes': lead.get('notes', ''),
    }
    try:
        db.qualified_leads.insert_one(doc)
        return True
    except Exception:
        return False

def list_qualified_leads(limit=500):
    db = get_db()
    if db is None:
        return []
    return list(db.qualified_leads.find().sort('qualified_at', DESCENDING).limit(limit))

def list_daily_qualified(date_str):
    db = get_db()
    if db is None:
        return []
    return list(db.daily_qualified.find({'date': date_str}).sort('qualified_at', DESCENDING))

def save_daily_qualified(lead, qualified_by_user_id):
    db = get_db()
    if db is None:
        return False
    date_str = (lead.get('qualified_at') or now_iso())[:10]
    doc = {
        'date': date_str,
        'page_url': lead.get('page_url', ''),
        'business_name': lead.get('business_name', ''),
        'phone': lead.get('phone', ''),
        'email': lead.get('email', ''),
        'category': lead.get('category', ''),
        'qualification_score': str(lead.get('qualification_score', '')),
        'qualified_at': lead.get('qualified_at') or now_iso(),
        'qualified_by': to_object_id(qualified_by_user_id),
        'qualified_by_name': lead.get('qualified_by_name', ''),
    }
    try:
        db.daily_qualified.update_one(
            {'page_url': doc['page_url'], 'date': date_str},
            {'$set': doc},
            upsert=True,
        )
        return True
    except Exception:
        return False

def list_daily_files():
    db = get_db()
    if db is None:
        return []
    pipeline = [
        {'$group': {'_id': '$date', 'count': {'$sum': 1}}},
        {'$sort': {'_id': DESCENDING}},
    ]
    return [{'date': r['_id'], 'filename': f"{r['_id']}.csv", 'count': r['count']} for r in db.daily_qualified.aggregate(pipeline)]

def get_today_qualified():
    db = get_db()
    if db is None:
        return []
    today = datetime.date.today().isoformat()
    return list(db.daily_qualified.find({'date': today}).sort('qualified_at', DESCENDING))


# ── Outreach tracking ─────────────────────────────────────────────────
# Each outreach log is one attempt to reach a qualified lead via a channel
# (phone call, WhatsApp call/message, FB message, email) with an outcome
# (replied, no_reply, voicemail, busy) and free-form notes.
VALID_OUTREACH_TYPES = {'phone_call', 'whatsapp_call', 'whatsapp_message', 'facebook_message', 'email'}
VALID_OUTREACH_OUTCOMES = {'replied', 'no_reply', 'voicemail', 'busy'}

def save_outreach_log(page_url, outreach_type, outcome, notes, user_id, user_name, qualified_lead_id=None):
    """Save a new outreach log. Returns the inserted document (with _id) or None on failure."""
    db = get_db()
    if db is None:
        return None
    if outreach_type not in VALID_OUTREACH_TYPES:
        return None
    if outcome not in VALID_OUTREACH_OUTCOMES:
        return None
    if not page_url:
        return None
    try:
        doc = {
            'page_url': page_url,
            'type': outreach_type,
            'outcome': outcome,
            'notes': (notes or '').strip(),
            'logged_by_user_id': user_id,
            'logged_by_name': user_name or '',
            'qualified_lead_id': qualified_lead_id,
            'created_at': now_iso(),
        }
        result = db.outreach_logs.insert_one(doc)
        doc['_id'] = str(result.inserted_id)
        return doc
    except Exception:
        return None

def list_outreach_logs(page_url=None, user_id=None, limit=200):
    """List outreach logs. Filter by page_url (for a single lead) or user_id (for current user's logs)."""
    db = get_db()
    if db is None:
        return []
    query = {}
    if page_url:
        query['page_url'] = page_url
    if user_id:
        query['logged_by_user_id'] = user_id
    try:
        return list(db.outreach_logs.find(query).sort('created_at', DESCENDING).limit(limit))
    except Exception:
        return []

def delete_outreach_log(log_id, user_id=None, is_admin=False):
    """Delete an outreach log. If user_id is given, only the owner can delete
    (admins can delete anyone's)."""
    db = get_db()
    if db is None:
        return False
    try:
        oid = to_object_id(log_id)
        if not oid:
            return False
        query = {'_id': oid}
        if user_id and not is_admin:
            query['logged_by_user_id'] = user_id
        result = db.outreach_logs.delete_one(query)
        return result.deleted_count > 0
    except Exception:
        return False


# ── Standard-quality remarks ──────────────────────────────────────────
# Free-form notes about a qualified lead. Each remark is text authored
# by a user with timestamp. Used by the Qualified page for manual
# observations about lead quality (e.g. "Phone disconnected", "Owner is
# slow to respond", "Competitor already in market").
def save_qualified_remark(page_url, text, user_id, user_name, qualified_lead_id=None):
    """Save a new standard-quality remark. Returns the inserted doc or None."""
    db = get_db()
    if db is None:
        return None
    if not page_url or not (text or '').strip():
        return None
    try:
        doc = {
            'page_url': page_url,
            'text': (text or '').strip(),
            'author_user_id': user_id,
            'author_name': user_name or '',
            'qualified_lead_id': qualified_lead_id,
            'created_at': now_iso(),
        }
        result = db.qualified_remarks.insert_one(doc)
        doc['_id'] = str(result.inserted_id)
        return doc
    except Exception:
        return None

def list_qualified_remarks(page_url=None, user_id=None, limit=200):
    """List standard-quality remarks. Filter by page_url (single lead) or user_id."""
    db = get_db()
    if db is None:
        return []
    query = {}
    if page_url:
        query['page_url'] = page_url
    if user_id:
        query['author_user_id'] = user_id
    try:
        return list(db.qualified_remarks.find(query).sort('created_at', DESCENDING).limit(limit))
    except Exception:
        return []

def delete_qualified_remark(remark_id, user_id=None, is_admin=False):
    """Delete a remark. Owner-only unless admin."""
    db = get_db()
    if db is None:
        return False
    try:
        oid = to_object_id(remark_id)
        if not oid:
            return False
        query = {'_id': oid}
        if user_id and not is_admin:
            query['author_user_id'] = user_id
        result = db.qualified_remarks.delete_one(query)
        return result.deleted_count > 0
    except Exception:
        return False

# ── F-commerce leads ─────────────────────────────────────────────────
def save_fcommerce_lead(data):
    db = get_db()
    if db is None:
        return None
    now = now_iso()
    doc = {
        'date': data.get('date', now[:10]),
        'source': data.get('source', 'apify'),
        'business_name': data.get('business_name', ''),
        'page_url': data.get('page_url', ''),
        'followers_int': str(data.get('followers_int', '')),
        'has_website': data.get('has_website', ''),
        'order_method': data.get('order_method', ''),
        'last_post_date': data.get('last_post_date', ''),
        'product_categories': data.get('product_categories', ''),
        'discovery_source': data.get('discovery_source', ''),
        'qualification_score': str(data.get('qualification_score', '')),
        'priority': data.get('priority', 'LOW'),
        'opportunity_flags': data.get('opportunity_flags', ''),
        'email': data.get('email', ''),
        'phone': data.get('phone', ''),
        'address': data.get('address', ''),
        'status': data.get('status', 'new'),
        'notes': data.get('notes', ''),
        'created_at': now,
    }
    try:
        result = db.fcommerce_leads.insert_one(doc)
        doc['_id'] = result.inserted_id
        return doc
    except Exception:
        existing = db.fcommerce_leads.find_one({'page_url': doc['page_url']})
        return existing or doc

def list_fcommerce_leads(filters=None):
    db = get_db()
    if db is None:
        return []
    q = {}
    if filters:
        if filters.get('priority'):
            q['priority'] = filters['priority']
        if filters.get('source'):
            q['source'] = filters['source']
        if filters.get('category'):
            q['product_categories'] = {'$regex': filters['category'], '$options': 'i'}
    return list(db.fcommerce_leads.find(q).sort('created_at', DESCENDING))

def delete_fcommerce_lead(page_url):
    db = get_db()
    if db is None:
        return False
    result = db.fcommerce_leads.delete_one({'page_url': page_url})
    return result.deleted_count > 0

def fcommerce_stats():
    db = get_db()
    if db is None:
        return {'by_priority': {}, 'by_source': {}, 'by_status': {}, 'total': 0}
    rows = list(db.fcommerce_leads.find({}, {'priority': 1, 'source': 1, 'status': 1}))
    by_priority, by_source, by_status = {}, {}, {}
    for r in rows:
        p = r.get('priority', 'unknown')
        s = r.get('source', 'unknown')
        st = r.get('status', 'unknown')
        by_priority[p] = by_priority.get(p, 0) + 1
        by_source[s] = by_source.get(s, 0) + 1
        by_status[st] = by_status.get(st, 0) + 1
    return {'by_priority': by_priority, 'by_source': by_source, 'by_status': by_status, 'total': len(rows)}

# ── LinkedIn leads ───────────────────────────────────────────────────
def save_linkedin_lead(data):
    db = get_db()
    if db is None:
        return None
    now = now_iso()
    doc = {
        'date': now[:10],
        'name': data.get('name', ''),
        'headline': data.get('headline', ''),
        'company': data.get('company', ''),
        'location': data.get('location', ''),
        'url': data.get('url', ''),
        'kb_score': str(data.get('kb_score', 0)),
        'kb_category': data.get('kb_category', ''),
        'matched_products': data.get('matched_products', ''),
        'status': 'new',
        'source': data.get('source', 'linkedin'),
        'created_at': now,
    }
    try:
        result = db.linkedin_leads.insert_one(doc)
        doc['_id'] = result.inserted_id
        return doc
    except Exception as e:
        print(f"[mongo] linkedin insert error: {e}", flush=True)
        return None

# ── Maps leads (read-only legacy) ────────────────────────────────────
def find_lead_by_url_across_files(page_url, user_id, is_admin=False):
    """Original _find_lead_by_url checked maps_leads too. Mirror that here."""
    lead = find_lead_by_url(page_url, user_id, is_admin=is_admin)
    if lead:
        return lead
    db = get_db()
    if db is None:
        return None
    return db.maps_leads.find_one({'page_url': page_url})

# ── Admin stats ──────────────────────────────────────────────────────
def admin_stats():
    db = get_db()
    if db is None:
        return {'total_users': 0, 'total_leads': 0, 'role_counts': {}, 'statuses': {}, 'this_month': 0, 'month_label': ''}
    total_users = db.users.count_documents({})
    total_leads = db.leads.count_documents({'deleted_at': None})
    role_counts = {r['_id']: r['count'] for r in db.users.aggregate([{'$group': {'_id': '$role', 'count': {'$sum': 1}}}])}
    statuses = {r['_id']: r['count'] for r in db.leads.aggregate([
        {'$match': {'deleted_at': None}},
        {'$group': {'_id': '$status', 'count': {'$sum': 1}}},
    ])}
    now = datetime.datetime.now()
    month_prefix = f"{now.year}-{now.month:02d}"
    this_month = db.leads.count_documents({
        'deleted_at': None,
        'created_at': {'$regex': f'^{month_prefix}'},
    })
    return {
        'total_users': total_users,
        'total_leads': total_leads,
        'role_counts': role_counts,
        'statuses': statuses,
        'this_month': this_month,
        'month_label': now.strftime('%B %Y'),
    }

# ── Outreach history ────────────────────────────────────────────────
def save_outreach(user_id, business_name, page_url, netlify_url, build_time):
    db = get_db()
    if db is None:
        return
    db.outreach_history.insert_one({
        'user_id': to_object_id(user_id) if user_id else None,
        'business_name': business_name,
        'page_url': page_url,
        'netlify_url': netlify_url,
        'build_time': build_time,
        'created_at': now_iso(),
    })
