"""
Configuration module for Maven Decoder MCP Server
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple

class Config:
    """Configuration settings for the Maven Decoder MCP Server"""

    # Default Maven repository location (used when nothing else overrides it).
    MAVEN_HOME: Path = Path.home() / ".m2" / "repository"
    
    # Server configuration
    SERVER_NAME: str = "maven-decoder"

    # Remote (online) Maven support.
    # Only the canonical index is used by default: the central.sonatype.com
    # mirror silently returns irrelevant results for class (c:/fc:) queries
    # and zero results for quoted terms, so a wrong answer would look like a
    # right one. Point MAVEN_SEARCH_URL at a private index to add fallbacks.
    DEFAULT_SEARCH_URLS: Tuple[str, ...] = (
        "https://search.maven.org/solrsearch/select",
    )
    DEFAULT_REMOTE_REPOSITORIES: Tuple[str, ...] = ("https://repo1.maven.org/maven2",)
    DEFAULT_HTTP_TIMEOUT: float = 30.0
    DEFAULT_REMOTE_SEARCH_LIMIT: int = 20
    # search.maven.org throttles bursts by hanging until the client times
    # out, so a couple of backed-off retries are the difference between a
    # working search and a spurious failure.
    DEFAULT_HTTP_RETRIES: int = 3
    
    # Decompiler settings
    DECOMPILER_TIMEOUT: int = 30  # seconds
    DECOMPILER_PRIORITY: list = ["cfr", "procyon", "fernflower", "javap"]
    
    # Search and analysis limits
    DEFAULT_ARTIFACT_LIMIT: int = 50
    DEFAULT_SEARCH_LIMIT: int = 100
    MAX_DEPENDENCY_DEPTH: int = 5
    
    # Cache settings
    ENABLE_CACHE: bool = True
    CACHE_SIZE: int = 1000
    CACHE_TTL: int = 3600  # seconds
    
    # Logging configuration
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance settings
    MAX_CONCURRENT_OPERATIONS: int = 10
    JAR_ANALYSIS_TIMEOUT: int = 60  # seconds
    
    # Feature flags
    ENABLE_DECOMPILATION: bool = True
    ENABLE_TRANSITIVE_DEPS: bool = True
    ENABLE_BYTECODE_ANALYSIS: bool = False  # Requires additional libraries
    
    # File size limits (in bytes)
    MAX_JAR_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_CLASS_SIZE: int = 1024 * 1024      # 1MB

    @classmethod
    def resolve_maven_repository(cls) -> Path:
        """Resolve the Maven local repository directory.

        Precedence (first set value wins):
        1. ``MAVEN_REPOSITORY`` or ``MAVEN_REPO`` — direct path to the
           repository (e.g. ``F:\\data\\repository``).
        2. ``MAVEN_HOME`` or ``M2_HOME`` — Maven install dir or the repo
           itself. A nested ``repository`` subdir wins when it exists;
           a ``conf/settings.xml`` with ``<localRepository>`` is honored.
        3. ``~/.m2/settings.xml`` ``<localRepository>`` when present.
        4. Fallback: ``~/.m2/repository``.
        """
        for var in ("MAVEN_REPOSITORY", "MAVEN_REPO"):
            value = os.environ.get(var, "").strip()
            if value:
                return cls._expand(value)

        for var in ("MAVEN_HOME", "M2_HOME"):
            value = os.environ.get(var, "").strip()
            if value:
                return cls._resolve_install_dir(cls._expand(value))

        settings_repo = cls._read_settings_local_repo(
            Path.home() / ".m2" / "settings.xml"
        )
        if settings_repo is not None:
            return settings_repo

        return Path.home() / ".m2" / "repository"

    @staticmethod
    def _expand(value: str) -> Path:
        """Expand ``~`` and env vars so Windows/Unix paths both work."""
        return Path(os.path.expandvars(os.path.expanduser(value))).resolve()

    @staticmethod
    def _env_flag(names: Tuple[str, ...], default: bool) -> bool:
        """Read a boolean env var, accepting the usual truthy spellings."""
        for name in names:
            value = os.environ.get(name, "").strip().lower()
            if value:
                return value in ("1", "true", "yes", "on", "enabled")
        return default

    @classmethod
    def is_offline(cls) -> bool:
        """True when all network access must be skipped.

        Set ``MAVEN_OFFLINE=true`` (or ``MAVEN_DECODER_OFFLINE=true``) to run
        the server exactly like the pre-online versions did.
        """
        return cls._env_flag(("MAVEN_OFFLINE", "MAVEN_DECODER_OFFLINE"), False)

    @classmethod
    def auto_download_enabled(cls) -> bool:
        """True when local-repository misses may be fetched from a remote repo."""
        if cls.is_offline():
            return False
        return cls._env_flag(("MAVEN_AUTO_DOWNLOAD",), True)

    @classmethod
    def verify_checksums(cls) -> bool:
        """True when downloaded files are checked against their ``.sha1``."""
        return cls._env_flag(("MAVEN_VERIFY_CHECKSUM",), True)

    @classmethod
    def resolve_search_urls(cls) -> List[str]:
        """Resolve Solr-style search endpoints, most preferred first.

        ``MAVEN_SEARCH_URL`` accepts a comma/whitespace separated list so a
        private index can replace or precede the public ones.
        """
        raw = os.environ.get("MAVEN_SEARCH_URL", "").strip()
        if raw:
            urls = [
                item.strip()
                for item in raw.replace(",", " ").split()
                if item.strip()
            ]
            if urls:
                return urls
        return list(cls.DEFAULT_SEARCH_URLS)

    @classmethod
    def http_retries(cls) -> int:
        """Retry attempts for transient network failures (``MAVEN_HTTP_RETRIES``)."""
        raw = os.environ.get("MAVEN_HTTP_RETRIES", "").strip()
        try:
            retries = int(raw)
        except ValueError:
            return cls.DEFAULT_HTTP_RETRIES
        return max(0, retries)

    @classmethod
    def resolve_remote_repositories(cls) -> List[str]:
        """Resolve remote repository base URLs, most preferred first.

        ``MAVEN_REMOTE_REPOS`` (or ``MAVEN_REMOTE_REPO``) accepts a comma or
        whitespace separated list so a corporate Nexus/Artifactory mirror can
        replace or precede Maven Central.
        """
        for var in ("MAVEN_REMOTE_REPOS", "MAVEN_REMOTE_REPO"):
            raw = os.environ.get(var, "").strip()
            if not raw:
                continue
            repos = [
                item.strip().rstrip("/")
                for item in raw.replace(",", " ").split()
                if item.strip()
            ]
            if repos:
                return repos
        return [repo.rstrip("/") for repo in cls.DEFAULT_REMOTE_REPOSITORIES]

    @classmethod
    def resolve_download_cache(cls) -> Path:
        """Resolve where remotely fetched artifacts are stored.

        The cache uses the standard Maven layout so every existing analysis
        tool works against it unchanged. It is deliberately separate from the
        real local repository to avoid interfering with Maven builds.
        """
        override = os.environ.get("MAVEN_DECODER_CACHE_DIR", "").strip()
        if override:
            return cls._expand(override)

        for var in ("XDG_CACHE_HOME", "LOCALAPPDATA"):
            base = os.environ.get(var, "").strip()
            if base:
                return cls._expand(base) / "maven-decoder-mcp" / "repository"

        return Path.home() / ".cache" / "maven-decoder-mcp" / "repository"

    @classmethod
    def http_timeout(cls) -> float:
        """Per-request timeout in seconds (``MAVEN_HTTP_TIMEOUT``)."""
        raw = os.environ.get("MAVEN_HTTP_TIMEOUT", "").strip()
        try:
            timeout = float(raw)
        except ValueError:
            return cls.DEFAULT_HTTP_TIMEOUT
        return timeout if timeout > 0 else cls.DEFAULT_HTTP_TIMEOUT

    @classmethod
    def remote_credentials(cls) -> Optional[Tuple[str, str]]:
        """Basic-auth credentials for private mirrors, when configured."""
        username = os.environ.get("MAVEN_REMOTE_USERNAME", "").strip()
        password = os.environ.get("MAVEN_REMOTE_PASSWORD", "")
        if username:
            return (username, password)
        return None

    @classmethod
    def max_download_bytes(cls) -> int:
        """Refuse downloads larger than this (``MAVEN_MAX_DOWNLOAD_SIZE``)."""
        raw = os.environ.get("MAVEN_MAX_DOWNLOAD_SIZE", "").strip()
        try:
            limit = int(raw)
        except ValueError:
            return cls.MAX_JAR_SIZE
        return limit if limit > 0 else cls.MAX_JAR_SIZE

    @classmethod
    def get_remote_config(cls) -> dict:
        """Snapshot of the online configuration, useful for logging."""
        return {
            "offline": cls.is_offline(),
            "auto_download": cls.auto_download_enabled(),
            "search_urls": cls.resolve_search_urls(),
            "remote_repositories": cls.resolve_remote_repositories(),
            "cache_dir": str(cls.resolve_download_cache()),
            "timeout": cls.http_timeout(),
            "retries": cls.http_retries(),
            "verify_checksums": cls.verify_checksums(),
            "authenticated": cls.remote_credentials() is not None,
        }

    @classmethod
    def _resolve_install_dir(cls, base: Path) -> Path:
        """Accept either a repo dir or a Maven install dir for HOME vars."""
        candidate = base / "repository"
        if candidate.is_dir():
            return candidate
        settings_repo = cls._read_settings_local_repo(base / "conf" / "settings.xml")
        if settings_repo is not None:
            return settings_repo
        default_repo = Path.home() / ".m2" / "repository"
        if base == default_repo.parent:
            settings_default = cls._read_settings_local_repo(
                default_repo.parent / "settings.xml"
            )
            if settings_default is not None:
                return settings_default
        return base

    @staticmethod
    def _read_settings_local_repo(settings_path: Path) -> Optional[Path]:
        """Parse ``<localRepository>`` from a Maven settings.xml file."""
        try:
            if not settings_path.is_file():
                return None

            root = ET.parse(settings_path).getroot()
            for elem in root.iter():
                if elem.tag.rsplit("}", 1)[-1] != "localRepository":
                    continue
                text = (elem.text or "").strip()
                if not text:
                    return None
                return Path(
                    os.path.expandvars(os.path.expanduser(text))
                ).resolve()
        except OSError:
            return None
        except ET.ParseError:
            return None
        return None

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        if not cls.MAVEN_HOME.exists():
            print(f"Warning: Maven repository not found at {cls.MAVEN_HOME}")
            return False
        
        if not cls.MAVEN_HOME.is_dir():
            print(f"Error: Maven repository path is not a directory: {cls.MAVEN_HOME}")
            return False
        
        return True
    
    @classmethod
    def get_maven_home(cls) -> Path:
        """Get the Maven repository home directory"""
        return cls.MAVEN_HOME
    
    @classmethod
    def set_maven_home(cls, path: str) -> None:
        """Set a custom Maven repository location"""
        cls.MAVEN_HOME = Path(path)
    
    @classmethod
    def get_decompiler_config(cls) -> dict:
        """Get decompiler configuration"""
        return {
            "timeout": cls.DECOMPILER_TIMEOUT,
            "priority": cls.DECOMPILER_PRIORITY,
            "enabled": cls.ENABLE_DECOMPILATION
        }
    
    @classmethod
    def get_limits(cls) -> dict:
        """Get search and analysis limits"""
        return {
            "artifacts": cls.DEFAULT_ARTIFACT_LIMIT,
            "search": cls.DEFAULT_SEARCH_LIMIT,
            "dependency_depth": cls.MAX_DEPENDENCY_DEPTH,
            "max_jar_size": cls.MAX_JAR_SIZE,
            "max_class_size": cls.MAX_CLASS_SIZE
        }

# Environment-specific configuration overrides
if os.environ.get("MAVEN_DECODER_ENV") == "development":
    Config.LOG_LEVEL = "DEBUG"
    Config.ENABLE_BYTECODE_ANALYSIS = True
    Config.CACHE_TTL = 60  # Shorter cache in development

elif os.environ.get("MAVEN_DECODER_ENV") == "production":
    Config.LOG_LEVEL = "WARNING"
    Config.MAX_CONCURRENT_OPERATIONS = 20
    Config.CACHE_SIZE = 5000
