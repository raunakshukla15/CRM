"""Authentication: register, login, logout, profile, password reset, delete account."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_client_ip, get_current_session, get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.ratelimit import is_rate_limited
from app.models.user import PasswordReset, Session as SessionRow, User
from app.schemas.auth import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.activity import log_activity
from app.services.auth import (
    cookie_kwargs,
    create_session,
    hash_password,
    revoke_all_user_sessions,
    revoke_session,
    validate_password_strength,
    verify_password,
)
from app.services.email_sender import send_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _rate_limit_or_429(request: Request, scope: str) -> None:
    settings = get_settings()
    key = f"auth:{get_client_ip(request)}:{scope}"
    if is_rate_limited(key, settings.RATE_LIMIT_AUTH_ATTEMPTS, settings.RATE_LIMIT_AUTH_WINDOW_S):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
        )


def _set_session_cookie(response: Response, raw_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=settings.SESSION_EXPIRE_DAYS * 86400,
        path="/",
        **cookie_kwargs(),
    )


def _clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest, request: Request, response: Response, db: DBSession = Depends(get_db)):
    _rate_limit_or_429(request, "register")
    if body.password != body.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match.")
    weak = validate_password_strength(body.password)
    if weak:
        raise HTTPException(status_code=422, detail=weak)

    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(full_name=body.full_name.strip(), email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    log_activity(db, "account.registered", f"Account created for {email}.",
                 user_id=user.id, entity_type="user", entity_id=user.id, ip=get_client_ip(request))
    raw = create_session(db, user, ip=get_client_ip(request),
                         user_agent=request.headers.get("user-agent"))
    db.commit()
    _set_session_cookie(response, raw)
    return user


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, request: Request, response: Response, db: DBSession = Depends(get_db)):
    _rate_limit_or_429(request, "login")
    email = body.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        # Generic message — do not reveal whether the email exists.
        log_activity(db, "auth.login_failed", "Failed sign-in attempt.",
                     user_id=user.id if user else None, ip=get_client_ip(request))
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    log_activity(db, "auth.login", f"{email} signed in.", user_id=user.id, ip=get_client_ip(request))
    raw = create_session(db, user, ip=get_client_ip(request),
                         user_agent=request.headers.get("user-agent"))
    db.commit()
    _set_session_cookie(response, raw)
    return user


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current: tuple[User, SessionRow] = Depends(get_current_session),
    db: DBSession = Depends(get_db),
):
    user, session = current
    # Record before invalidating.
    log_activity(db, "auth.logout", f"{user.email} signed out.", user_id=user.id,
                 ip=get_client_ip(request))
    revoke_session(db, session)
    db.commit()
    _clear_session_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    user.full_name = body.full_name.strip()
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current: tuple[User, SessionRow] = Depends(get_current_session),
    db: DBSession = Depends(get_db),
):
    user, session = current
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=422, detail="New passwords do not match.")
    weak = validate_password_strength(body.new_password)
    if weak:
        raise HTTPException(status_code=422, detail=weak)
    user.password_hash = hash_password(body.new_password)
    revoked = revoke_all_user_sessions(db, user.id, except_id=session.id)
    log_activity(db, "auth.password_changed",
                 f"Password changed; {revoked} other session(s) revoked.",
                 user_id=user.id, ip=get_client_ip(request))
    db.commit()
    return {"ok": True, "sessions_revoked": revoked}


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, request: Request, db: DBSession = Depends(get_db)):
    _rate_limit_or_429(request, "forgot")
    settings = get_settings()
    # Always respond the same way — do not reveal whether the email exists.
    email = body.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is not None and user.is_active:
        # Invalidate older unused tokens for this user.
        olds = db.scalars(
            select(PasswordReset).where(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None))
        ).all()
        for old in olds:
            old.used_at = datetime.utcnow()
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        db.add(PasswordReset(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        ))
        log_activity(db, "auth.reset_requested", "Password reset requested.",
                     user_id=user.id, ip=get_client_ip(request))
        db.commit()
        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={raw}"
        if settings.SMTP_HOST:
            send_email(
                user.email,
                "Reset your KilloKart password",
                f"Hi {user.full_name},\n\nReset your password here (valid 1 hour):\n{reset_link}\n\n"
                "If you did not request this, ignore this email.",
            )
        else:
            logger.warning("SMTP not configured — password reset link for %s was NOT emailed.", email)
    return {"ok": True, "message": "If an account exists for this email, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, request: Request, db: DBSession = Depends(get_db)):
    _rate_limit_or_429(request, "reset")
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=422, detail="New passwords do not match.")
    weak = validate_password_strength(body.new_password)
    if weak:
        raise HTTPException(status_code=422, detail=weak)
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    row = db.scalar(select(PasswordReset).where(PasswordReset.token_hash == token_hash))
    if row is None or row.used_at is not None or row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    user.password_hash = hash_password(body.new_password)
    row.used_at = datetime.utcnow()
    revoke_all_user_sessions(db, user.id)
    log_activity(db, "auth.password_reset", "Password was reset via email link.",
                 user_id=user.id, ip=get_client_ip(request))
    db.commit()
    return {"ok": True}


@router.delete("/account")
def delete_account(
    body: DeleteAccountRequest,
    request: Request,
    response: Response,
    current: tuple[User, SessionRow] = Depends(get_current_session),
    db: DBSession = Depends(get_db),
):
    """Permanent deletion with re-authentication.

    Retention policy: the user row, all sessions/reset tokens, and ALL owned CRM
    records (customers incl. their orders/notes/interactions/followups/logs) plus
    the user's activity history are deleted in ONE transaction. Afterwards a
    single anonymized audit row (user_id NULL, email domain only) is kept.
    """
    user, _ = current
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Password is incorrect.")

    email = user.email
    domain = email.split("@")[-1] if "@" in email else "unknown"
    user_id = user.id

    from app.models.customer import Customer

    customer_count = (
        db.query(Customer).filter(Customer.owner_id == user_id).count()
    )
    db.delete(user)  # cascades: sessions, resets, owned CRM rows, activity logs
    db.flush()
    # Anonymized tombstone — no email, no name, no tokens.
    log_activity(
        db, "account.deleted",
        f"Account deleted. Removed {customer_count} owned customer(s) and all related records.",
        user_id=None, entity_type="user", entity_id=None,
        meta={"email_domain": domain}, ip=get_client_ip(request),
    )
    db.commit()
    _clear_session_cookie(response)
    return {"ok": True}
