"""Cloudinary file storage for avatars, generated demos, and any uploads.

Replaces local file writes (avatars/, /tmp/demo_*).
Reads credentials from CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET.
"""
import os
import io
import time
import cloudinary
import cloudinary.uploader
import cloudinary.api

CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

_configured = False
def _ensure_config():
    global _configured
    if _configured:
        return True
    if not (CLOUD_NAME and API_KEY and API_SECRET):
        return False
    try:
        cloudinary.config(
            cloud_name=CLOUD_NAME,
            api_key=API_KEY,
            api_secret=API_SECRET,
            secure=True,
        )
        _configured = True
        return True
    except Exception as e:
        print(f"[cloudinary] config error: {e}", flush=True)
        return False

def is_configured():
    return bool(CLOUD_NAME and API_KEY and API_SECRET)

def upload_bytes(data, folder, public_id, resource_type='image', overwrite=True):
    """Upload raw bytes to Cloudinary. Returns dict with 'url' and 'public_id' on success, or None on failure."""
    if not _ensure_config():
        return None
    try:
        result = cloudinary.uploader.upload(
            data,
            folder=folder,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=overwrite,
            invalidate=True,
        )
        return {
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'bytes': result.get('bytes'),
        }
    except Exception as e:
        print(f"[cloudinary] upload error: {e}", flush=True)
        return None

def upload_file(file_path, folder, public_id, resource_type='image', overwrite=True):
    """Upload a file from disk. Returns dict on success or None on failure."""
    if not _ensure_config():
        return None
    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=overwrite,
            invalidate=True,
        )
        return {
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'bytes': result.get('bytes'),
        }
    except Exception as e:
        print(f"[cloudinary] upload error: {e}", flush=True)
        return None

def delete_file(public_id, resource_type='image'):
    """Delete a file from Cloudinary by public_id."""
    if not _ensure_config():
        return False
    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type, invalidate=True)
        return True
    except Exception as e:
        print(f"[cloudinary] delete error: {e}", flush=True)
        return False

# ── Avatar helpers ───────────────────────────────────────────────────
def upload_avatar(user_id, image_bytes):
    """Upload a user's avatar. Returns the Cloudinary URL or None."""
    folder = f"scraven/avatars"
    public_id = f"user_{user_id}"
    result = upload_bytes(image_bytes, folder=folder, public_id=public_id, resource_type='image', overwrite=True)
    if result:
        return result['url']
    return None

def get_avatar_url(user_id, stored_url=None):
    """Return the URL to display for a user. Prefers stored Cloudinary URL; falls back to constructed public URL."""
    if stored_url:
        return stored_url
    if not (CLOUD_NAME):
        return None
    return f"https://res.cloudinary.com/{CLOUD_NAME}/image/upload/scraven/avatars/user_{user_id}.jpg"
