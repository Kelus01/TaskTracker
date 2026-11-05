import json
import logging
import re
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GitHubApiError(Exception):
    pass


@dataclass(frozen=True)
class GitHubCommitData:
    sha: str
    message: str
    author: str
    committed_at: datetime
    html_url: str


class GitHubApiClient:
    api_base_url = "https://api.github.com"
    commits_per_request = 20

    def fetch_commits(self, repository: str) -> list[GitHubCommitData]:
        normalized_repository = repository.strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", normalized_repository):
            raise GitHubApiError("GitHub repository must use the owner/repository format.")
        cache_key = f"github:commits:{normalized_repository.casefold()}"
        cached_commits = cache.get(cache_key)
        if cached_commits is not None:
            return cached_commits

        owner, repo = normalized_repository.split("/", maxsplit=1)
        url = (
            f"{self.api_base_url}/repos/{quote(owner, safe='')}/"
            f"{quote(repo, safe='')}/commits?per_page={self.commits_per_request}"
        )
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "TaskTracker",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        try:
            with urlopen(request, timeout=settings.GITHUB_API_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read())
        except HTTPError as exc:
            logger.warning("GitHub API returned HTTP %s for repository sync.", exc.code)
            raise GitHubApiError(f"GitHub API returned HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, socket.timeout) as exc:
            logger.warning("GitHub API request failed: %s", type(exc).__name__)
            raise GitHubApiError("GitHub API is unavailable or timed out.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("GitHub API returned invalid JSON.")
            raise GitHubApiError("GitHub API returned an invalid response.") from exc

        try:
            if not isinstance(payload, list):
                raise ValueError("Expected a list of commits.")
            commits = [self._parse_commit(item) for item in payload]
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("GitHub API returned an unexpected commit payload.")
            raise GitHubApiError("GitHub API returned an invalid commit response.") from exc

        cache.set(cache_key, commits, timeout=settings.GITHUB_CACHE_TTL_SECONDS)
        return commits

    @staticmethod
    def _parse_commit(item: dict) -> GitHubCommitData:
        commit = item["commit"]
        details = commit["committer"]
        committed_at = datetime.fromisoformat(details["date"].replace("Z", "+00:00"))
        if committed_at.tzinfo is None:
            committed_at = committed_at.replace(tzinfo=timezone.utc)

        author = item.get("author")
        author_name = author.get("login") if isinstance(author, dict) else None
        if not author_name:
            author_name = commit["author"]["name"]

        return GitHubCommitData(
            sha=item["sha"],
            message=commit["message"],
            author=author_name[:200],
            committed_at=committed_at,
            html_url=item["html_url"],
        )
