import pytest

from fastai.database import core
from fastai.database.core import PostgresSettings


def test_sample():
    assert core is not None


class TestPostgresSettingsFromFields:
    def test_builds_url_from_fields(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("FASTAI_POSTGRES_HOSTNAME", "localhost")
        monkeypatch.setenv("FASTAI_POSTGRES_PORT", "5432")
        monkeypatch.setenv("FASTAI_POSTGRES_NAME", "mydb")
        monkeypatch.setenv("FASTAI_POSTGRES_USER", "admin")
        monkeypatch.setenv("FASTAI_POSTGRES_PASSWORD", "secret")

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert str(settings.dsn) == (
            "postgresql+asyncpg://admin:secret@localhost:5432/mydb"
        )

    def test_sslmode_included_when_not_prefer(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("FASTAI_POSTGRES_HOSTNAME", "db.neon.tech")
        monkeypatch.setenv("FASTAI_POSTGRES_NAME", "mydb")
        monkeypatch.setenv("FASTAI_POSTGRES_USER", "admin")
        monkeypatch.setenv("FASTAI_POSTGRES_PASSWORD", "secret")
        monkeypatch.setenv("FASTAI_POSTGRES_SSLMODE", "require")

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert "sslmode=require" in str(settings.dsn)

    def test_sslmode_omitted_when_prefer(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("FASTAI_POSTGRES_HOSTNAME", "localhost")
        monkeypatch.setenv("FASTAI_POSTGRES_NAME", "mydb")
        monkeypatch.setenv("FASTAI_POSTGRES_USER", "admin")
        monkeypatch.setenv("FASTAI_POSTGRES_PASSWORD", "secret")

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert "sslmode" not in str(settings.dsn)

    def test_options_included_in_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("FASTAI_POSTGRES_HOSTNAME", "cockroach.cloud")
        monkeypatch.setenv("FASTAI_POSTGRES_NAME", "mydb")
        monkeypatch.setenv("FASTAI_POSTGRES_USER", "admin")
        monkeypatch.setenv("FASTAI_POSTGRES_PASSWORD", "secret")
        monkeypatch.setenv("FASTAI_POSTGRES_OPTIONS", "--cluster=my-routing-id")

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert "options=--cluster=my-routing-id" in str(settings.dsn)

    def test_default_port(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("FASTAI_POSTGRES_HOSTNAME", "localhost")
        monkeypatch.setenv("FASTAI_POSTGRES_NAME", "mydb")
        monkeypatch.setenv("FASTAI_POSTGRES_USER", "admin")
        monkeypatch.setenv("FASTAI_POSTGRES_PASSWORD", "secret")

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.port == 5432


class TestPostgresSettingsFromUrl:
    def test_extracts_parts_from_postgresql_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            "FASTAI_POSTGRES_URL",
            "postgresql://myuser:mypass@db.example.com:5433/proddb",
        )

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.hostname == "db.example.com"
        assert settings.port == 5433
        assert settings.name == "proddb"
        assert settings.user == "myuser"
        assert settings.password.get_secret_value() == "mypass"

    def test_normalizes_postgres_scheme(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            "FASTAI_POSTGRES_URL",
            "postgres://heroku_user:pass@ec2-host.compute-1.amazonaws.com:5432/herokudb",
        )

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.hostname == "ec2-host.compute-1.amazonaws.com"
        assert settings.user == "heroku_user"
        assert "postgresql+asyncpg://" in str(settings.dsn)

    def test_extracts_sslmode_from_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            "FASTAI_POSTGRES_URL",
            "postgresql://user:pass@neon.tech:5432/db?sslmode=require",
        )

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.sslmode == "require"

    def test_extracts_options_from_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            "FASTAI_POSTGRES_URL",
            "postgresql://user:pass@cockroach.cloud:26257/db?sslmode=verify-full&options=--cluster%3Dmy-id",
        )

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.options == "--cluster=my-id"
        assert settings.sslmode == "verify-full"

    def test_url_parts_override_env_defaults(self, monkeypatch: pytest.MonkeyPatch):
        """When a URL is provided, its extracted parts take precedence."""
        monkeypatch.setenv(
            "FASTAI_POSTGRES_URL",
            "postgresql://urluser:urlpass@urlhost:5432/urldb",
        )

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.hostname == "urlhost"
        assert settings.user == "urluser"
        assert settings.name == "urldb"

    def test_default_port_from_url_without_port(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            "FASTAI_POSTGRES_URL",
            "postgresql://user:pass@host/db",
        )

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.port == 5432

    def test_neon_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            "FASTAI_POSTGRES_URL",
            "postgresql://neonuser:neonpass@ep-cool-name-123.us-east-2.aws.neon.tech/neondb?sslmode=require",
        )

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.hostname == "ep-cool-name-123.us-east-2.aws.neon.tech"
        assert settings.sslmode == "require"

    def test_digitalocean_nonstandard_port(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            "FASTAI_POSTGRES_URL",
            "postgresql://doadmin:secret@db-do-user-123-0.b.db.ondigitalocean.com:25060/defaultdb?sslmode=require",
        )

        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

        assert settings.port == 25060
        assert settings.sslmode == "require"
