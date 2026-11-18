"""Local settings with explicit development-only security options."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from scripts.check_raw_connection import RawConfig, load_config, read_env_file
from .errors import PipelineError

SOURCE_ENDPOINT = "tcp:DESKTOP-OBDFK6B,1433"
SOURCE_INSTANCE = "SQLEXPRESS"
SOURCE_DATABASE = "WideWorldImporters"

# Historical diagnostics only; normal ingestion does not require this identity.
SOURCE_PRINCIPAL = "DESKTOP-OBDFK6B\\wwi_extract"
SOURCE_SID = bytes.fromhex("0105000000000005150000003CF5FF806E0A76B5BDAC3020EF030000")


@dataclass(frozen=True)
class Settings:
    target: RawConfig = field(repr=False)
    batch_size: int = 500
    login_timeout: int = 5
    query_timeout: int = 60

    development: bool = False
    trust_server_certificate: bool = False
    allow_admin_source: bool = False

    def __post_init__(self) -> None:
        if (self.trust_server_certificate or self.allow_admin_source) and not self.development:
            raise PipelineError("DEVELOPMENT_ONLY_SETTING")

    @property
    def source_connection_string(self) -> str:
        return ("DRIVER={ODBC Driver 18 for SQL Server};SERVER=" + SOURCE_ENDPOINT
                + ";DATABASE=" + SOURCE_DATABASE + ";Trusted_Connection=yes;Encrypt=yes;"
                  "TrustServerCertificate=" + ("yes" if self.trust_server_certificate else "no") + ";APP=retail_wwi_full_load;")

    def summary(self) -> dict[str, object]:
        return {"source": SOURCE_ENDPOINT, "instance": SOURCE_INSTANCE, "database": SOURCE_DATABASE,
                "source_identity": "CURRENT_WINDOWS_USER", "encrypt": True,
                "trust_server_certificate": self.trust_server_certificate, "development": self.development,
                "allow_admin_source": self.allow_admin_source,
                "target_host": self.target.host, "target_port": self.target.port,
                "target_database": self.target.database, "target_user": self.target.user,
                "batch_size": self.batch_size, "login_timeout": self.login_timeout,
                "query_timeout": self.query_timeout}


def settings(env_file: Path | None, batch_size: int | None = None) -> Settings:
    values = read_env_file(env_file) if env_file else {}
    values.update(os.environ)
    for key, allowed in (("WWI_SQLSERVER_HOST", {"", SOURCE_ENDPOINT}),
                         ("WWI_SQLSERVER_DATABASE", {"", SOURCE_DATABASE}),
                         ("WWI_SQLSERVER_AUTH_MODE", {"", "Windows", "WINDOWS", "Integrated"}),
                         ("WWI_SQLSERVER_ENCRYPT", {"", "yes", "true", "1"}),
                         ("WWI_SQLSERVER_TRUST_SERVER_CERTIFICATE", {"", "no", "false", "0", "yes", "true", "1"})):
        if values.get(key, "") not in allowed: raise PipelineError("UNSAFE_SOURCE_CONFIGURATION")
    count = batch_size if batch_size is not None else int(values.get("WWI_BATCH_SIZE", "500"))
    login = int(values.get("WWI_LOGIN_TIMEOUT", "5")); query = int(values.get("WWI_QUERY_TIMEOUT", "60"))
    if not 1 <= count <= 10000 or not 1 <= login <= 120 or not 1 <= query <= 3600:
        raise PipelineError("INVALID_BATCH_OR_TIMEOUT")
    target=load_config(values)
    if target.port!=55434: raise PipelineError("TARGET_PROFILE_NOT_APPROVED")
    mode = values.get("APP_ENV", "production")
    if mode not in {"production", "development"}: raise PipelineError("INVALID_APP_ENV")
    def flag(key: str) -> bool:
        value = values.get(key, "no").lower()
        if value not in {"yes", "true", "1", "no", "false", "0"}: raise PipelineError("INVALID_BOOLEAN_CONFIGURATION")
        return value in {"yes", "true", "1"}
    trust = flag("WWI_SQLSERVER_TRUST_SERVER_CERTIFICATE")
    admin = flag("WWI_ALLOW_ADMIN_SOURCE")
    if (trust or admin) and mode != "development": raise PipelineError("DEVELOPMENT_ONLY_SETTING")
    return Settings(target, count, login, query, mode == "development", trust, admin)
