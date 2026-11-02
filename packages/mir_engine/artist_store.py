"""
artist_store.py — Read and write per-artist result files (tracks.csv, profile.json, listening_notes.csv).

Artist data is private and never committed to this public repo. Two backends:
  - LocalArtistStore:  a directory on disk (MIR_ARTIST_DATA_DIR), used by the compute scripts.
  - GitHubArtistStore: a private GitHub repo read and written through the contents API with a token,
                       so the hosted dashboard can reach the data without it living in this repo.

Layout in both: <root>/<artist>/{tracks.csv, profile.json, listening_notes.csv}.
"""

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REQUIRED_FILES = ("tracks.csv", "profile.json")


class LocalArtistStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    @property
    def label(self) -> str:
        return f"local folder {self.root}"

    def list_artists(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(
            p.name for p in self.root.iterdir() if all((p / f).exists() for f in REQUIRED_FILES)
        )

    def read_text(self, artist: str, name: str) -> str | None:
        path = self.root / artist / name
        return path.read_text() if path.exists() else None

    def write_text(self, artist: str, name: str, text: str, message: str = "") -> None:
        path = self.root / artist / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


class GitHubArtistStore:
    API = "https://api.github.com"

    def __init__(self, repo: str, token: str, branch: str = "main", prefix: str = ""):
        self.repo, self.token, self.branch = repo, token, branch
        self.prefix = prefix.strip("/")

    @property
    def label(self) -> str:
        return f"private GitHub repo {self.repo}"

    def _path(self, *parts: str) -> str:
        return "/".join(p for p in (self.prefix, *parts) if p)

    def _request(self, method: str, path: str, body: dict | None = None, raw: bool = False):
        url = f"{self.API}/repos/{self.repo}/contents/{urllib.parse.quote(path)}"
        if method == "GET":
            url += f"?ref={urllib.parse.quote(self.branch)}"
        req = urllib.request.Request(
            url,
            method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "diaspora-mir-engine",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        return data.decode() if raw else json.loads(data)

    def _get_or_none(self, path: str, raw: bool = False):
        try:
            return self._request("GET", path, raw=raw)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def list_artists(self) -> list[str]:
        entries = self._get_or_none(self._path()) or []
        artists = []
        for entry in entries:
            if entry.get("type") != "dir":
                continue
            files = {f["name"] for f in self._get_or_none(entry["path"]) or []}
            if all(f in files for f in REQUIRED_FILES):
                artists.append(entry["name"])
        return sorted(artists)

    def read_text(self, artist: str, name: str) -> str | None:
        return self._get_or_none(self._path(artist, name), raw=True)

    def write_text(self, artist: str, name: str, text: str, message: str = "") -> None:
        path = self._path(artist, name)
        existing = self._get_or_none(path)
        body = {
            "message": message or f"Update {path}",
            "content": base64.b64encode(text.encode()).decode(),
            "branch": self.branch,
        }
        if existing:
            body["sha"] = existing["sha"]
        self._request("PUT", path, body)


def store_from_settings(settings: dict, local_root: Path) -> LocalArtistStore | GitHubArtistStore | None:
    """GitHub store when a repo and token are configured, else the local folder if it exists, else None."""
    if settings.get("github_repo") and settings.get("github_token"):
        return GitHubArtistStore(
            settings["github_repo"],
            settings["github_token"],
            branch=settings.get("github_branch") or "main",
            prefix=settings.get("github_prefix") or "",
        )
    if Path(local_root).is_dir():
        return LocalArtistStore(local_root)
    return None
