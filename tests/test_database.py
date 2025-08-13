from datetime import datetime, timezone


def test_database_schema(app):
    from app.database import init_db, get_db_session, Website, VerificationLog, CaptchaLog
    assert init_db()
    session = get_db_session()
    try:
        # create a website row
        w = Website(
            id='test-site',
            domain='https://example.com',
            token='tok_test',
            name='Example',
            status='active',
            created_at=datetime.now(timezone.utc)
        )
        session.add(w)
        session.commit()

        # insert verification log
        v = VerificationLog(
            website_id='test-site',
            session_id='sess1',
            is_human=True,
            confidence=0.9
        )
        session.add(v)
        session.commit()

        # insert captcha log
        c = CaptchaLog(
            website_id='test-site',
            ip_address='127.0.0.1',
            status='pass'
        )
        session.add(c)
        session.commit()

        assert session.query(Website).count() >= 1
        assert session.query(VerificationLog).count() >= 1
        assert session.query(CaptchaLog).count() >= 1
    finally:
        session.close()


