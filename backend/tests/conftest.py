import os
import uuid

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from backend.app.config import ROOT
from backend.app.database import Base, get_session, make_engine
from backend.app.main import app
from backend.app.models import Workspace, WORKSPACE_ID
from backend.app.auth import get_auth_session


@pytest.fixture
def client():
    load_dotenv(ROOT / '.env')
    url = os.environ.get('TEST_DATABASE_URL', '')
    if not url or not (make_url(url).database or '').endswith('_test'):
        pytest.fail('Set TEST_DATABASE_URL to a dedicated database ending in _test; development data is never used.')
    schema = 'test_' + uuid.uuid4().hex
    administration = make_engine(url)
    with administration.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA {schema}'))
    engine = make_engine(url, connect_args={'options': f'-csearch_path={schema}'})
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    with sessions.begin() as session:
        session.add(Workspace(id=WORKSPACE_ID, revision=0, name='Demo workspace', is_demo=True))

    def isolated_session():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = isolated_session
    app.dependency_overrides[get_auth_session] = isolated_session
    try:
        with TestClient(app) as instance:
            instance.test_sessions = sessions
            yield instance
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
        with administration.begin() as connection:
            # The name is a fixed prefix plus a UUID generated above, never user input.
            connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        administration.dispose()
