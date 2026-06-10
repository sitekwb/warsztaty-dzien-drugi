"""Test that the SQLAlchemy session factory wires correctly to SQLite."""

from sqlalchemy import text

from minibank.db.session import SessionLocal, engine


def test_session_factory_yields_working_connection(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.db import session as session_module
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)

    with session_module.SessionLocal() as s:
        result = s.execute(text("SELECT 1")).scalar()
        assert result == 1
