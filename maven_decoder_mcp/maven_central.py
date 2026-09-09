"""
Remote Maven repository access for the Maven Decoder MCP Server.

Adds online capability on top of the local ``~/.m2`` analysis:

* Search Maven Central (or a configured mirror) for artifacts and classes.
* List every published version of an artifact, not only the installed ones.
* Download jars/sources/POMs into a local cache that uses the standard Maven
  layout, so all existing offline analysis tools work on remote artifacts.

Networking is intentionally synchronous (``requests``); the MCP server wraps
these calls in ``asyncio.to_thread`` so the event loop stays responsive.
"""

import hashlib
import logging
import os
import shutil
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

from .config import Config

logger = logging.getLogger(__name__)

USER_AGENT = "maven-decoder-mcp"

# Packaging values that are published as a plain ``.jar`` on the repository.
_JAR_LIKE_PACKAGING = {"jar", "bundle", "maven-plugin", "ejb", "war", "ear", "test-jar"}


class MavenRemoteError(RuntimeError):
    """Raised when a remote repository operation cannot be completed."""


class OfflineError(MavenRemoteError):
    """Raised when a remote operation is attempted while offline."""


class MavenCentralClient:
    """Client for searching and downloading from remote Maven repositories."""

    def __init__(self,
                 search_urls: Optional[Sequence[str]] = None,
                 repositories: Optional[Sequence[str]] = None,
                 cache_dir: Optional[Path] = None,
                 timeout: Optional[float] = None,
                 offline: Optional[bool] = None,
                 auth: Optional[Tuple[str, str]] = None,
                 max_download_bytes: Optional[int] = None,
                 verify_checksums: Optional[bool] = None,
                 retries: Optional[int] = None):
        self.search_urls = list(search_urls) if search_urls else Config.resolve_search_urls()
        self.retries = Config.http_retries() if retries is None else max(0, retries)
        self.repositories = [
            repo.rstrip("/")
            for repo in (repositories or Config.resolve_remote_repositories())
        ]
        self.cache_dir = Path(cache_dir) if cache_dir else Config.resolve_download_cache()
        self.timeout = timeout if timeout is not None else Config.http_timeout()
        self.offline = Config.is_offline() if offline is None else offline
        self.auth = auth if auth is not None else Config.remote_credentials()
        self.max_download_bytes = (
            max_download_bytes if max_download_bytes is not None
            else Config.max_download_bytes()
        )
        self.verify_checksums = (
            Config.verify_checksums() if verify_checksums is None else verify_checksums
        )
        self._session: Optional[requests.Session] = None

    # ------------------------------------------------------------------
    # HTTP plumbing
    # ------------------------------------------------------------------

    @property
    def session(self) -> requests.Session:
        """Lazily created session so connections are reused across calls."""
        if self._session is None:
            session = requests.Session()
            session.headers.update({"User-Agent": USER_AGENT})
            if self.auth:
                session.auth = self.auth
            self._session = session
        return self._session

    def _ensure_online(self, operation: str) -> None:
        if self.offline:
            raise OfflineError(
                f"Cannot {operation}: offline mode is enabled "
                "(unset MAVEN_OFFLINE to allow network access)"
            )

    @property
    def search_url(self) -> str:
        """The preferred search endpoint."""
        return self.search_urls[0]

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None,
             stream: bool = False) -> requests.Response:
        """GET with retries, translating transport errors.

        Public Maven search endpoints throttle bursts of requests, so a
        timeout is retried with a short backoff before giving up.
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.retries + 1):
            try:
                return self.session.get(
                    url, params=params, timeout=self.timeout, stream=stream
                )
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.retries:
                    delay = 1.5 * (2 ** attempt)
                    logger.info(
                        "Request to %s failed (%s); retrying in %.1fs "
                        "(attempt %d of %d)",
                        url,
                        exc,
                        delay,
                        attempt + 1,
                        self.retries + 1,
                    )
                    time.sleep(delay)

        raise MavenRemoteError(f"Request to {url} failed: {last_error}") from last_error

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @staticmethod
    def build_search_query(query: Optional[str] = None,
                           group_id: Optional[str] = None,
                           artifact_id: Optional[str] = None,
                           class_name: Optional[str] = None,
                           fully_qualified_class: Optional[str] = None,
                           packaging: Optional[str] = None) -> str:
        """Build a Solr query string for the Maven Central search API."""
        clauses: List[str] = []

        if group_id:
            clauses.append(f'g:"{group_id}"')
        if artifact_id:
            clauses.append(f'a:"{artifact_id}"')
        if fully_qualified_class:
            clauses.append(f'fc:"{fully_qualified_class}"')
        if class_name:
            clauses.append(f'c:"{class_name}"')
        if packaging:
            clauses.append(f'p:"{packaging}"')
        if query:
            clauses.append(query.strip())

        if not clauses:
            raise ValueError(
                "At least one of query, group_id, artifact_id, class_name, "
                "or fully_qualified_class is required"
            )

        return " AND ".join(clauses)

    def search(self, query: Optional[str] = None,
               group_id: Optional[str] = None,
               artifact_id: Optional[str] = None,
               class_name: Optional[str] = None,
               fully_qualified_class: Optional[str] = None,
               packaging: Optional[str] = None,
               limit: int = 20,
               start: int = 0,
               all_versions: bool = False) -> Dict[str, Any]:
        """Search the remote index for artifacts.

        By default the index returns one row per artifact (its latest
        version). Set ``all_versions`` to list every published version of the
        matching artifacts instead.
        """
        self._ensure_online("search remote repositories")

        solr_query = self.build_search_query(
            query=query,
            group_id=group_id,
            artifact_id=artifact_id,
            class_name=class_name,
            fully_qualified_class=fully_qualified_class,
            packaging=packaging,
        )

        params: Dict[str, Any] = {
            "q": solr_query,
            "rows": max(1, min(int(limit), 200)),
            "start": max(0, int(start)),
            "wt": "json",
        }
        if all_versions:
            params["core"] = "gav"

        errors: List[str] = []
        for index, search_url in enumerate(self.search_urls):
            try:
                payload = self._query_index(search_url, params)
            except MavenRemoteError as exc:
                errors.append(str(exc))
                if index + 1 < len(self.search_urls):
                    logger.warning(
                        "Search failed against %s (%s); trying %s next",
                        search_url, exc, self.search_urls[index + 1],
                    )
                continue

            body = payload.get("response", {}) or {}
            docs = body.get("docs", []) or []

            return {
                "query": solr_query,
                "search_url": search_url,
                "total_found": body.get("numFound", len(docs)),
                "start": params["start"],
                "returned": len(docs),
                "artifacts": [self._normalize_doc(doc) for doc in docs],
            }

        raise MavenRemoteError(
            "Search failed against every configured endpoint: " + "; ".join(errors)
        )

    def _query_index(self, search_url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query one search endpoint and return its decoded payload."""
        response = self._get(search_url, params=params)

        if response.status_code != 200:
            raise MavenRemoteError(
                f"{search_url} -> HTTP {response.status_code}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise MavenRemoteError(
                f"{search_url} returned a non-JSON response"
            ) from exc

    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a raw Solr document into a stable, readable shape."""
        group_id = doc.get("g", "")
        artifact_id = doc.get("a", "")
        version = doc.get("v") or doc.get("latestVersion") or ""

        extensions = doc.get("ec", []) or []
        result: Dict[str, Any] = {
            "group_id": group_id,
            "artifact_id": artifact_id,
            "version": version,
            "packaging": doc.get("p", ""),
            "coordinates": f"{group_id}:{artifact_id}:{version}" if version
            else f"{group_id}:{artifact_id}",
            "has_sources": "-sources.jar" in extensions,
            "has_javadoc": "-javadoc.jar" in extensions,
            "available_files": extensions,
        }

        if doc.get("latestVersion"):
            result["latest_version"] = doc["latestVersion"]
        if doc.get("versionCount"):
            result["version_count"] = doc["versionCount"]
        if doc.get("timestamp"):
            result["timestamp"] = doc["timestamp"]
        return result

    # ------------------------------------------------------------------
    # Version listing
    # ------------------------------------------------------------------

    def get_versions(self, group_id: str, artifact_id: str,
                     limit: int = 100) -> Dict[str, Any]:
        """List published versions of an artifact.

        ``maven-metadata.xml`` is preferred because it works against plain
        repository mirrors that expose no search index; the search API is used
        as a fallback.
        """
        self._ensure_online("list remote versions")

        metadata = self._fetch_versions_from_metadata(group_id, artifact_id)
        if metadata is not None:
            versions = metadata["versions"]
            return {
                "artifact": f"{group_id}:{artifact_id}",
                "source": "maven-metadata.xml",
                "repository": metadata["repository"],
                "latest": metadata.get("latest"),
                "release": metadata.get("release"),
                "last_updated": metadata.get("last_updated"),
                "total_versions": len(versions),
                "versions": list(reversed(versions))[:limit],
            }

        search_result = self.search(
            group_id=group_id,
            artifact_id=artifact_id,
            limit=limit,
            all_versions=True,
        )
        versions = [item["version"] for item in search_result["artifacts"] if item["version"]]
        return {
            "artifact": f"{group_id}:{artifact_id}",
            "source": "search-index",
            "repository": search_result["search_url"],
            "latest": versions[0] if versions else None,
            "total_versions": search_result["total_found"],
            "versions": versions,
        }

    def _fetch_versions_from_metadata(self, group_id: str,
                                      artifact_id: str) -> Optional[Dict[str, Any]]:
        """Read ``maven-metadata.xml`` from the first repository that has it."""
        relative = f"{group_id.replace('.', '/')}/{artifact_id}/maven-metadata.xml"

        for repository in self.repositories:
            url = f"{repository}/{relative}"
            try:
                response = self._get(url)
            except MavenRemoteError as exc:
                logger.debug("Metadata fetch failed for %s: %s", url, exc)
                continue

            if response.status_code != 200:
                continue

            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as exc:
                logger.debug("Malformed metadata at %s: %s", url, exc)
                continue

            versioning = root.find("versioning")
            if versioning is None:
                continue

            versions = [
                elem.text.strip()
                for elem in versioning.findall("versions/version")
                if elem.text and elem.text.strip()
            ]
            if not versions:
                continue

            return {
                "repository": repository,
                "versions": versions,
                "latest": self._element_text(versioning, "latest"),
                "release": self._element_text(versioning, "release"),
                "last_updated": self._element_text(versioning, "lastUpdated"),
            }

        return None

    @staticmethod
    def _element_text(parent: ET.Element, tag: str) -> Optional[str]:
        elem = parent.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
        return None

    def get_latest_version(self, group_id: str, artifact_id: str) -> Optional[str]:
        """Return the newest published version, or ``None`` when unknown."""
        try:
            info = self.get_versions(group_id, artifact_id, limit=1)
        except MavenRemoteError:
            return None
        return info.get("release") or info.get("latest") or (
            info["versions"][0] if info.get("versions") else None
        )

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def cached_path(self, group_id: str, artifact_id: str, version: str,
                    classifier: Optional[str] = None,
                    extension: str = "jar") -> Path:
        """Path this artifact occupies in the cache (Maven layout)."""
        suffix = f"-{classifier}" if classifier else ""
        return (
            self.cache_dir
            / Path(group_id.replace(".", "/"))
            / artifact_id
            / version
            / f"{artifact_id}-{version}{suffix}.{extension}"
        )

    def download_artifact(self, group_id: str, artifact_id: str, version: str,
                          classifier: Optional[str] = None,
                          extension: str = "jar",
                          force: bool = False) -> Path:
        """Download one artifact file into the cache and return its path.

        Already cached files are reused unless ``force`` is set.
        """
        target = self.cached_path(group_id, artifact_id, version, classifier, extension)
        if target.exists() and not force:
            logger.debug("Cache hit for %s", target)
            return target

        self._ensure_online(f"download {group_id}:{artifact_id}:{version}")

        suffix = f"-{classifier}" if classifier else ""
        relative = (
            f"{group_id.replace('.', '/')}/{artifact_id}/{version}/"
            f"{artifact_id}-{version}{suffix}.{extension}"
        )

        errors: List[str] = []
        for repository in self.repositories:
            url = f"{repository}/{relative}"
            try:
                downloaded = self._download_to(url, target)
            except MavenRemoteError as exc:
                errors.append(str(exc))
                continue
            if downloaded is not None:
                logger.info("Downloaded %s from %s", relative, repository)
                return downloaded
            errors.append(f"{url} -> not found")

        raise MavenRemoteError(
            f"Could not download {group_id}:{artifact_id}:{version}"
            + (f":{classifier}" if classifier else "")
            + f" ({extension}) from any configured repository. Tried: "
            + "; ".join(errors)
        )

    def _download_to(self, url: str, target: Path) -> Optional[Path]:
        """Stream ``url`` into ``target``; ``None`` when the file is absent."""
        response = self._get(url, stream=True)

        if response.status_code == 404:
            response.close()
            return None
        if response.status_code != 200:
            response.close()
            raise MavenRemoteError(f"{url} -> HTTP {response.status_code}")

        declared = response.headers.get("Content-Length")
        if declared and declared.isdigit() and int(declared) > self.max_download_bytes:
            response.close()
            raise MavenRemoteError(
                f"{url} is {int(declared)} bytes, exceeding the "
                f"{self.max_download_bytes} byte limit (set MAVEN_MAX_DOWNLOAD_SIZE)"
            )

        target.parent.mkdir(parents=True, exist_ok=True)

        digest = hashlib.sha1()
        written = 0
        tmp_fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".part")
        tmp_path = Path(tmp_name)

        try:
            with os.fdopen(tmp_fd, "wb") as handle:
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    written += len(chunk)
                    if written > self.max_download_bytes:
                        raise MavenRemoteError(
                            f"{url} exceeds the {self.max_download_bytes} byte "
                            "download limit (set MAVEN_MAX_DOWNLOAD_SIZE)"
                        )
                    digest.update(chunk)
                    handle.write(chunk)

            self._verify_checksum(url, digest.hexdigest())
            # Atomic publish so readers never observe a partial file.
            shutil.move(str(tmp_path), str(target))
            return target
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise
        finally:
            response.close()

    def _verify_checksum(self, url: str, actual_sha1: str) -> None:
        """Compare against the published ``.sha1`` when one is available."""
        if not self.verify_checksums:
            return

        try:
            response = self._get(f"{url}.sha1")
        except MavenRemoteError as exc:
            logger.debug("Checksum fetch failed for %s: %s", url, exc)
            return

        if response.status_code != 200:
            return

        expected = response.text.strip().split()[0] if response.text.strip() else ""
        if len(expected) != 40:
            return

        if expected.lower() != actual_sha1.lower():
            raise MavenRemoteError(
                f"Checksum mismatch for {url}: expected {expected}, got {actual_sha1}"
            )

    def ensure_artifact(self, group_id: str, artifact_id: str, version: str,
                        classifier: Optional[str] = None,
                        extension: str = "jar") -> Optional[Path]:
        """Best-effort fetch: return the cached path or ``None`` on failure."""
        try:
            return self.download_artifact(
                group_id, artifact_id, version, classifier, extension
            )
        except MavenRemoteError as exc:
            logger.debug(
                "ensure_artifact(%s:%s:%s, classifier=%s, ext=%s) failed: %s",
                group_id, artifact_id, version, classifier, extension, exc,
            )
            return None

    def download_bundle(self, group_id: str, artifact_id: str, version: str,
                        include_sources: bool = False,
                        include_javadoc: bool = False,
                        classifier: Optional[str] = None,
                        force: bool = False) -> Dict[str, Any]:
        """Download the main jar plus POM and any requested extra artifacts."""
        downloaded: Dict[str, str] = {}
        failures: Dict[str, str] = {}

        def attempt(label: str, cls: Optional[str], extension: str,
                    required: bool) -> None:
            try:
                path = self.download_artifact(
                    group_id, artifact_id, version, cls, extension, force=force
                )
                downloaded[label] = str(path)
            except MavenRemoteError as exc:
                failures[label] = str(exc)
                if required:
                    raise

        attempt("pom", None, "pom", required=False)

        if classifier:
            attempt("classified_jar", classifier, "jar", required=True)
        else:
            packaging = self._packaging_from_cached_pom(group_id, artifact_id, version)
            if packaging in _JAR_LIKE_PACKAGING or packaging is None:
                attempt("jar", None, "jar", required=False)

        if include_sources:
            attempt("sources", "sources", "jar", required=False)
        if include_javadoc:
            attempt("javadoc", "javadoc", "jar", required=False)

        if not downloaded:
            raise MavenRemoteError(
                f"Nothing could be downloaded for {group_id}:{artifact_id}:{version}. "
                + "; ".join(f"{key}: {value}" for key, value in failures.items())
            )

        return {
            "artifact": f"{group_id}:{artifact_id}:{version}",
            "cache_dir": str(self.cache_dir),
            "downloaded": downloaded,
            "unavailable": failures,
        }

    def _packaging_from_cached_pom(self, group_id: str, artifact_id: str,
                                   version: str) -> Optional[str]:
        """Read ``<packaging>`` from the cached POM, when it is present."""
        pom_path = self.cached_path(group_id, artifact_id, version, None, "pom")
        if not pom_path.exists():
            return None
        try:
            root = ET.parse(pom_path).getroot()
        except (ET.ParseError, OSError):
            return None
        for elem in root:
            if elem.tag.rsplit("}", 1)[-1] == "packaging" and elem.text:
                return elem.text.strip()
        return "jar"

    def close(self) -> None:
        """Release pooled HTTP connections."""
        if self._session is not None:
            self._session.close()
            self._session = None
