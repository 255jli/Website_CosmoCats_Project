from __future__ import annotations
from typing import Optional
from io import BytesIO

from PIL import Image
from werkzeug.security import check_password_hash, generate_password_hash

import db_manager


AVATAR_SIZE = 1024


def update_name(user_id: int, new_name: str) -> bool:
    if new_name is None:
        return False
    new_name = new_name.strip()
    for session in db_manager.get_session():
        user = session.get(db_manager.User, user_id)
        if user is None:
            return False
        user.name = new_name
        return True
    return False


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    if not old_password or not new_password:
        return False
    for session in db_manager.get_session():
        user = session.get(db_manager.User, user_id)
        if user is None:
            return False
        if not check_password_hash(user.password_hash, old_password):
            return False
        user.password_hash = generate_password_hash(new_password)
        return True
    return False


def _prepare_avatar_1024(image_bytes: bytes) -> Optional[bytes]:
    try:
        with Image.open(BytesIO(image_bytes)) as im:
            # Force convert to RGB (drop alpha)
            im = im.convert("RGB")
            # Center-crop to square
            w, h = im.size
            if w != h:
                side = min(w, h)
                left = (w - side) // 2
                top = (h - side) // 2
                im = im.crop((left, top, left + side, top + side))
            im = im.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
            out = BytesIO()
            # Save as PNG to ensure compatibility and fixed size
            im.save(out, format="PNG")
            return out.getvalue()
    except Exception:
        return None


def upload_avatar(user_id: int, image_bytes: bytes) -> bool:
    prepared = _prepare_avatar_1024(image_bytes)
    if not prepared:
        return False
    for session in db_manager.get_session():
        user = session.get(db_manager.User, user_id)
        if user is None:
            return False
        user.avatar_blob = prepared
        return True
    return False

