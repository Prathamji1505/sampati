"""Account recovery, membership invitations and owner administration."""
from datetime import timedelta
import secrets
from typing import Annotated, Literal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, delete, func, select
from sqlalchemy.orm import Session

from .auth import CurrentAccount, LoginInput, SignupInput, authenticate, describe_session, issue_session, password_hash, require_auth_request, throttle, token_digest
from .database import get_session
from .models import Invitation, Membership, RecoveryCode, User, UserSession, Workspace, utcnow
from .services import require_workspace

router = APIRouter(tags=['Account and team administration'])
DB = Annotated[Session, Depends(get_session)]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra='forbid')


class WorkspaceChoice(StrictInput):
    workspace_id: str = Field(min_length=1, max_length=64)


class PasswordCheck(StrictInput):
    current_password: str = Field(min_length=1, max_length=128)


class PasswordChange(PasswordCheck):
    new_password: str = Field(min_length=12, max_length=128)


class RecoveryInput(LoginInput):
    password: str = Field(default='', max_length=0, exclude=True)
    recovery_code: str = Field(min_length=12, max_length=100)
    new_password: str = Field(min_length=12, max_length=128)


class InviteInput(StrictInput):
    username: str = Field(min_length=3, max_length=32)
    role: Literal['editor', 'viewer']


class TokenInput(StrictInput):
    token: str = Field(min_length=20, max_length=200)


class RoleInput(StrictInput):
    role: Literal['owner', 'editor', 'viewer']


def owner(context):
    if context.role != 'owner':
        raise HTTPException(403, 'Only an organisation owner can manage members, invitations and source keys.')


def check_new_password(value):
    if not value.strip():
        raise HTTPException(422, 'Choose a password with at least 12 characters, not only spaces.')


@router.post('/api/auth/workspace', dependencies=[Depends(require_auth_request)])
def switch_workspace(body: WorkspaceChoice, context: CurrentAccount, session: DB):
    with session.begin():
        membership = session.get(Membership, (context.actor_id, body.workspace_id))
        target = session.get(Workspace, body.workspace_id)
        if membership is None or target is None or target.is_demo:
            raise HTTPException(403, 'This account is not a member of that organisation.')
        saved = session.get(UserSession, context.session_hash)
        saved.workspace_id, saved.csrf_token = target.id, secrets.token_urlsafe(32)
        session.flush()
        return describe_session(saved, session.get(User, context.actor_id), target, membership.role, session)


@router.get('/api/auth/security')
def security(context: CurrentAccount, session: DB):
    codes = session.scalar(select(func.count()).select_from(RecoveryCode).where(RecoveryCode.user_id == context.actor_id, RecoveryCode.used_at.is_(None)))
    sessions = session.scalar(select(func.count()).select_from(UserSession).where(UserSession.user_id == context.actor_id, UserSession.expires_at > utcnow()))
    return {'recovery_codes_remaining': codes, 'active_sessions': sessions}


@router.post('/api/auth/recovery-codes', dependencies=[Depends(require_auth_request)])
def generate_codes(body: PasswordCheck, context: CurrentAccount, session: DB):
    with session.begin():
        user = session.scalar(select(User).where(User.id == context.actor_id).with_for_update())
        if not password_hash.verify(body.current_password, user.password_hash):
            raise HTTPException(400, 'The current password is incorrect.')
        session.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
        codes = [secrets.token_urlsafe(18) for _ in range(5)]
        session.add_all([RecoveryCode(code_hash=token_digest(code), user_id=user.id) for code in codes])
    return {'codes': codes, 'message': 'Save these somewhere private. Each works once; generating a new set invalidates the previous set.'}


@router.post('/api/auth/password', dependencies=[Depends(require_auth_request)])
def change_password(body: PasswordChange, context: CurrentAccount, request: Request, response: Response, session: DB):
    check_new_password(body.new_password)
    with session.begin():
        user = session.scalar(select(User).where(User.id == context.actor_id).with_for_update())
        if not password_hash.verify(body.current_password, user.password_hash):
            raise HTTPException(400, 'The current password is incorrect.')
        user.password_hash = password_hash.hash(body.new_password)
        session.execute(delete(UserSession).where(UserSession.user_id == user.id))
        session.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
        result = issue_session(request, response, session, user, session.get(Workspace, context.workspace_id), context.role)
    return result


@router.post('/api/auth/recover', dependencies=[Depends(require_auth_request)])
def recover(body: RecoveryInput, request: Request, response: Response, session: DB):
    check_new_password(body.new_password)
    throttle(request, session, body.username, 'recover')
    with session.begin():
        # Match password-change/code-generation lock order: user, then recovery code.
        user = session.scalar(select(User).where(User.username == body.username).with_for_update())
        code = session.scalar(select(RecoveryCode).where(RecoveryCode.code_hash == token_digest(body.recovery_code)).with_for_update())
        if user is None or code is None or code.user_id != user.id or code.used_at is not None:
            raise HTTPException(401, 'The username or recovery code is incorrect or has already been used.')
        membership = session.scalar(select(Membership).where(Membership.user_id == user.id).order_by(case((Membership.role == 'owner', 0), else_=1), Membership.workspace_id))
        if membership is None:
            raise HTTPException(403, 'This account does not currently have an organisation workspace.')
        code.used_at = utcnow()
        user.password_hash = password_hash.hash(body.new_password)
        session.execute(delete(UserSession).where(UserSession.user_id == user.id))
        result = issue_session(request, response, session, user, session.get(Workspace, membership.workspace_id), membership.role)
    return result


@router.get('/api/team')
def team(context: CurrentAccount, session: DB):
    members = session.execute(select(User, Membership.role).join(Membership, Membership.user_id == User.id).where(Membership.workspace_id == context.workspace_id).order_by(User.display_name)).all()
    invitations = []
    if context.role == 'owner':
        invitations = session.execute(select(Invitation, User.username).join(User, User.id == Invitation.target_user_id).where(Invitation.workspace_id == context.workspace_id).order_by(Invitation.expires_at.desc()).limit(50)).all()
    return {'members': [{'user_id': user.id, 'username': user.username, 'display_name': user.display_name, 'role': role} for user, role in members],
        'invitations': [{'id': item.id, 'username': username, 'role': item.role, 'expires_at': item.expires_at, 'state': 'revoked' if item.revoked else 'accepted' if item.consumed_at else 'expired' if item.expires_at <= utcnow() else 'pending'} for item, username in invitations]}


@router.post('/api/team/invitations')
def invite(body: InviteInput, context: CurrentAccount, session: DB):
    owner(context)
    with session.begin():
        require_workspace(session, context.workspace_id, lock=True)
        target = session.scalar(select(User).where(User.username == body.username.strip().lower()))
        if target is None:
            raise HTTPException(404, 'Ask this person to create a Sampati account first, then enter their username.')
        if session.get(Membership, (target.id, context.workspace_id)):
            raise HTTPException(409, 'This account is already a member of the organisation.')
        token = secrets.token_urlsafe(32)
        record = Invitation(id=str(uuid.uuid4()), workspace_id=context.workspace_id, target_user_id=target.id, issuer_id=context.actor_id,
            token_hash=token_digest(token), role=body.role, expires_at=utcnow() + timedelta(days=3), revoked=False)
        session.add(record)
    return {'id': record.id, 'token': token, 'expires_at': record.expires_at, 'username': target.username}


@router.post('/api/team/invitations/accept')
def accept_invitation(body: TokenInput, context: CurrentAccount, session: DB):
    with session.begin():
        invitation = session.scalar(select(Invitation).where(Invitation.token_hash == token_digest(body.token)))
        if invitation is None or invitation.target_user_id != context.actor_id or invitation.revoked or invitation.consumed_at or invitation.expires_at <= utcnow():
            raise HTTPException(400, 'This invitation is invalid, expired, already used, or belongs to another account.')
        require_workspace(session, invitation.workspace_id, lock=True)
        invitation = session.scalar(select(Invitation).where(Invitation.id == invitation.id).with_for_update().execution_options(populate_existing=True))
        if invitation.revoked or invitation.consumed_at or invitation.expires_at <= utcnow():
            raise HTTPException(400, 'This invitation is no longer available.')
        issuer = session.get(Membership, (invitation.issuer_id, invitation.workspace_id))
        if issuer is None or issuer.role != 'owner':
            raise HTTPException(400, 'The invitation issuer no longer manages this organisation.')
        membership = session.get(Membership, (context.actor_id, invitation.workspace_id))
        if membership is None:
            membership = Membership(user_id=context.actor_id, workspace_id=invitation.workspace_id, role=invitation.role)
            session.add(membership)
        invitation.consumed_at = utcnow()
        session.flush()
        saved = session.get(UserSession, context.session_hash)
        saved.workspace_id, saved.csrf_token = invitation.workspace_id, secrets.token_urlsafe(32)
        session.flush()
        return describe_session(saved, session.get(User, context.actor_id), session.get(Workspace, invitation.workspace_id), membership.role, session)


@router.delete('/api/team/invitations/{invitation_id}')
def revoke_invitation(invitation_id: str, context: CurrentAccount, session: DB):
    owner(context)
    with session.begin():
        require_workspace(session, context.workspace_id, lock=True)
        item = session.scalar(select(Invitation).where(Invitation.id == invitation_id, Invitation.workspace_id == context.workspace_id))
        if item is None:
            raise HTTPException(404, 'Invitation not found.')
        item.revoked = True
    return {'revoked': True}


def editable_member(session, context, user_id, new_role=None):
    owner(context)
    require_workspace(session, context.workspace_id, lock=True)
    member = session.get(Membership, (user_id, context.workspace_id))
    if member is None:
        raise HTTPException(404, 'Member not found in this organisation.')
    count = session.scalar(select(func.count()).select_from(Membership).where(Membership.workspace_id == context.workspace_id, Membership.role == 'owner'))
    if member.role == 'owner' and new_role != 'owner' and count <= 1:
        raise HTTPException(409, 'Keep at least one owner in the organisation.')
    return member


@router.patch('/api/team/members/{user_id}')
def update_role(user_id: str, body: RoleInput, context: CurrentAccount, session: DB):
    with session.begin():
        member = editable_member(session, context, user_id, body.role)
        member.role = body.role
    return {'role': body.role}


@router.delete('/api/team/members/{user_id}')
def remove_member(user_id: str, context: CurrentAccount, session: DB):
    with session.begin():
        member = editable_member(session, context, user_id)
        session.delete(member)
    return {'removed': True}
