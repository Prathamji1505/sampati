"""Local accounts and opaque, server-side cookie sessions.

The organisation is resolved from a verified session and current membership,
never from uploaded records, URL identifiers, or a browser-supplied tenant ID.
"""
from dataclasses import dataclass
from datetime import timedelta
import hashlib
import hmac
import secrets
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pwdlib import PasswordHash
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .database import get_session
from .models import LoginThrottle, Membership, User, UserSession, Workspace, WORKSPACE_ID, utcnow

COOKIE = 'sampati_session'
password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash(secrets.token_urlsafe(32))
router = APIRouter(prefix='/api/auth', tags=['Accounts'])
DB = Annotated[Session, Depends(get_session)]


def get_auth_session():
    # Auth reads use a separate session so the data transaction can begin cleanly.
    yield from get_session()


AuthDB = Annotated[Session, Depends(get_auth_session)]


@dataclass(frozen=True)
class AccessContext:
    workspace_id: str
    actor_id: str | None
    actor: str
    role: str
    session_hash: str | None = None


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def authenticate(request: Request, session: Session, check_csrf=True) -> tuple[AccessContext, UserSession, User, Workspace]:
    token = request.cookies.get(COOKIE, '')
    saved = session.get(UserSession, token_digest(token)) if token else None
    if saved is None or saved.expires_at <= utcnow():
        raise HTTPException(401, 'Your session has ended. Sign in to open your private workspace.')
    user = session.get(User, saved.user_id)
    workspace = session.get(Workspace, saved.workspace_id)
    membership = session.get(Membership, (saved.user_id, saved.workspace_id))
    if user is None or workspace is None or workspace.is_demo or membership is None:
        raise HTTPException(403, 'This account no longer has access to the organisation workspace.')
    if check_csrf and request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        if not hmac.compare_digest(request.headers.get('x-csrf-token', ''), saved.csrf_token):
            raise HTTPException(403, 'Your request could not be verified. Refresh the page and try again.')
    return AccessContext(workspace.id, user.id, f'{user.display_name} (@{user.username})', membership.role, saved.token_hash), saved, user, workspace


def get_data_context(request: Request, session: AuthDB) -> AccessContext:
    if request.url.path.startswith('/api/demo/'):
        return AccessContext(WORKSPACE_ID, None, 'Demo visitor', 'demo')
    context, _, _, _ = authenticate(request, session)
    if request.method not in {'GET', 'HEAD', 'OPTIONS'} and context.role not in {'owner', 'editor'}:
        raise HTTPException(403, 'Your organisation role allows viewing records, not importing changes.')
    return context


Context = Annotated[AccessContext, Depends(get_data_context)]


def get_account_context(request: Request, session: AuthDB) -> AccessContext:
    return authenticate(request, session)[0]


CurrentAccount = Annotated[AccessContext, Depends(get_account_context)]


class LoginInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    username: str = Field(min_length=3, max_length=32, pattern=r'^[a-z0-9][a-z0-9._-]*$')
    password: str = Field(min_length=1, max_length=128)

    @field_validator('username', mode='before')
    @classmethod
    def username_key(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class SignupInput(LoginInput):
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=2, max_length=80)
    organisation_name: str = Field(min_length=2, max_length=100)

    @field_validator('display_name', 'organisation_name', mode='before')
    @classmethod
    def clean_label(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('password')
    @classmethod
    def nonblank_password(cls, value):
        if not value.strip():
            raise ValueError('Choose a password with at least 12 characters, not only spaces.')
        return value


def require_auth_request(request: Request):
    # A custom header plus JSON and the origin check prevents login/signup CSRF.
    if request.headers.get('x-sampati-request') != '1':
        raise HTTPException(403, 'Use the Sampati sign-in form for this request.')


def throttle(request: Request, session: Session, username: str, action: str):
    now = utcnow()
    address = request.client.host if request.client else 'local'
    buckets = [(f'{action}:ip:{address}', 30), (f'{action}:account:{address}:{username}', 10)]
    with session.begin():
        for key, limit in buckets:
            digest = token_digest(key)
            session.execute(insert(LoginThrottle).values(key_hash=digest, attempts=0, window_started_at=now).on_conflict_do_nothing())
            record = session.scalar(select(LoginThrottle).where(LoginThrottle.key_hash == digest).with_for_update())
            if record.window_started_at + timedelta(minutes=15) <= now:
                record.window_started_at, record.attempts = now, 0
            if record.attempts >= limit:
                remaining = max(1, int((record.window_started_at + timedelta(minutes=15) - now).total_seconds()))
                raise HTTPException(429, 'Too many sign-in or account-creation attempts. Try again later.', headers={'Retry-After': str(remaining)})
            record.attempts += 1


def clear_cookie(response: Response):
    response.delete_cookie(COOKIE, path='/api', httponly=True, secure=settings.session_cookie_secure, samesite='strict')


def describe_session(saved: UserSession, user: User, workspace: Workspace, role: str, session: Session) -> dict:
    choices = session.execute(select(Workspace, Membership.role).join(Membership, Membership.workspace_id == Workspace.id).where(Membership.user_id == user.id, Workspace.is_demo.is_(False)).order_by(Workspace.name)).all()
    return {
        'user': {'id': user.id, 'username': user.username, 'display_name': user.display_name},
        'workspace': {'id': workspace.id, 'name': workspace.name, 'role': role},
        'workspaces': [{'id': record.id, 'name': record.name, 'role': member_role} for record, member_role in choices],
        'csrf_token': saved.csrf_token, 'expires_at': saved.expires_at.isoformat(),
    }


def issue_session(request: Request, response: Response, session: Session, user: User, workspace: Workspace, role='owner') -> dict:
    previous = request.cookies.get(COOKIE)
    if previous:
        session.execute(delete(UserSession).where(UserSession.token_hash == token_digest(previous)))
    # Expired sessions contain no reusable bearer value and can be removed safely.
    session.execute(delete(UserSession).where(UserSession.expires_at <= utcnow()))
    token = secrets.token_urlsafe(32)
    saved = UserSession(token_hash=token_digest(token), user_id=user.id, workspace_id=workspace.id,
        csrf_token=secrets.token_urlsafe(32), expires_at=utcnow() + timedelta(hours=settings.session_hours))
    session.add(saved)
    session.flush()
    response.set_cookie(COOKIE, token, max_age=settings.session_hours * 3600, path='/api',
        httponly=True, secure=settings.session_cookie_secure, samesite='strict')
    return describe_session(saved, user, workspace, role, session)


@router.get('/session')
def current_session(request: Request, response: Response, session: DB):
    if not request.cookies.get(COOKIE):
        return {'user': None, 'workspace': None, 'workspaces': [], 'csrf_token': None, 'expires_at': None}
    try:
        context, saved, user, workspace = authenticate(request, session, check_csrf=False)
        return describe_session(saved, user, workspace, context.role, session)
    except HTTPException as error:
        if error.status_code not in {401, 403}:
            raise
        clear_cookie(response)
        return {'user': None, 'workspace': None, 'workspaces': [], 'csrf_token': None, 'expires_at': None}


@router.post('/signup', status_code=201, dependencies=[Depends(require_auth_request)])
def signup(body: SignupInput, request: Request, response: Response, session: DB):
    throttle(request, session, body.username, 'signup')
    hashed = password_hash.hash(body.password)
    try:
        with session.begin():
            if session.scalar(select(User.id).where(User.username == body.username)):
                raise HTTPException(409, 'That username is already taken. Choose another one or sign in.')
            user = User(id=str(uuid.uuid4()), username=body.username, display_name=body.display_name, password_hash=hashed)
            workspace = Workspace(id=str(uuid.uuid4()), revision=0, name=body.organisation_name, is_demo=False)
            session.add_all([user, workspace])
            session.flush()
            session.add(Membership(user_id=user.id, workspace_id=workspace.id, role='owner'))
            session.flush()
            result = issue_session(request, response, session, user, workspace)
        return result
    except IntegrityError as error:
        raise HTTPException(409, 'That username is already taken. Choose another one or sign in.') from error


@router.post('/login', dependencies=[Depends(require_auth_request)])
def login(body: LoginInput, request: Request, response: Response, session: DB):
    throttle(request, session, body.username, 'login')
    with session.begin():
        user = session.scalar(select(User).where(User.username == body.username))
        valid = password_hash.verify(body.password, user.password_hash if user else dummy_hash)
        if user is None or not valid:
            raise HTTPException(401, 'The username or password is incorrect.')
        membership = session.scalar(select(Membership).join(Workspace, Workspace.id == Membership.workspace_id).where(Membership.user_id == user.id, Workspace.is_demo.is_(False)).order_by(case((Membership.role == 'owner', 0), else_=1), Membership.workspace_id))
        if membership is None:
            raise HTTPException(403, 'This account does not have an organisation workspace.')
        workspace = session.get(Workspace, membership.workspace_id)
        result = issue_session(request, response, session, user, workspace, membership.role)
    return result


@router.post('/logout', dependencies=[Depends(require_auth_request)])
def logout(request: Request, response: Response, session: DB):
    context, _, _, _ = authenticate(request, session)
    session.execute(delete(UserSession).where(UserSession.token_hash == context.session_hash))
    session.commit()
    clear_cookie(response)
    return {'signed_out': True}
