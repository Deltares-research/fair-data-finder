#!/usr/bin/env python3
"""Migrate STAC collections and items from a live stac api to pgSTAC.

Usage:
    python migrate_to_pgstac.py [options]

Output:
    output/collections.ndjson
    output/{collection_id}_items.ndjson
    output/migration_report.json
"""

import argparse
import asyncio
import json
import time

import orjson
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx
from pypgstac.db import PgstacDB
from pypgstac.load import Loader, Methods
from tqdm import tqdm

MAX_CONCURRENCY: int = 5
OUTPUT_DIR: Path = Path("output")


@dataclass
class Config:
    source_url: str
    database_url: str
    dms_token: str
    page_size: int
    request_delay: float

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "STAC-Migration-Script/1.0"}
        if self.dms_token:
            headers["Cookie"] = f"DMS_TOKEN={self.dms_token}"
        return headers


def parse_args() -> tuple[Config, bool]:
    parser = argparse.ArgumentParser(
        description="Migrate STAC data from a live stac API to a local pgSTAC database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and write NDJSON files but skip loading into pgSTAC.",
    )
    parser.add_argument(
        "--source-url",
        default="https://devs4w.deltares-fairdata.com/api",
        help="Source STAC API base URL",
    )
    parser.add_argument(
        "--database-url",
        default="postgresql://postgres:postgres@postgres:5432/postgres",
        help=(
            "pgSTAC PostgreSQL connection string, e.g. "
            "postgresql://<user>:<password>@<host>:<port>/<dbname>. "
            "Use host 'postgres' when running via `docker compose exec backend`, "
            "or 'localhost:5433' when running from the host machine."
        ),
    )
    parser.add_argument(
        "--dms-token",
        default="",
        help="Auth cookie for the source API",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="Items per page when fetching",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.1,
        help="Seconds to wait between paginated requests",
    )
    args = parser.parse_args()

    config = Config(
        source_url=args.source_url.rstrip("/"),
        database_url=args.database_url,
        dms_token=args.dms_token,
        page_size=args.page_size,
        request_delay=args.request_delay,
    )
    return config, args.dry_run


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------


async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    max_retries: int = 3,
) -> dict:
    """GET a URL, retrying with exponential backoff on server errors."""
    for attempt in range(max_retries):
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            is_last = attempt == max_retries - 1
            if is_last or (isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500):
                raise
            wait = 2 ** attempt
            tqdm.write(f"  Retry {attempt + 1}/{max_retries} for {url} (waiting {wait}s): {exc}")
            await asyncio.sleep(wait)
    raise RuntimeError("unreachable")


async def fetch_collections(client: httpx.AsyncClient, config: Config) -> list[dict]:
    """Fetch all collections from the source STAC API."""
    data = await fetch_with_retry(client, f"{config.source_url}/collections", config.headers)
    if isinstance(data, list):
        return data
    return data.get("collections", [])


async def fetch_items_for_collection(
    client: httpx.AsyncClient,
    collection_id: str,
    config: Config,
    semaphore: asyncio.Semaphore,
    progress_bar: tqdm,
) -> tuple[str, list[dict]]:
    """Fetch all items for one collection, paging via the 'next' link."""
    async with semaphore:
        items: list[dict] = []
        url: str | None = (
            f"{config.source_url}/collections/{collection_id}/items?limit={config.page_size}"
        )

        while url:
            data = await fetch_with_retry(client, url, config.headers)
            items.extend(data.get("features", []))

            next_link = next((lnk for lnk in data.get("links", []) if lnk.get("rel") == "next"), None)
            url = next_link["href"] if next_link else None

            if url:
                await asyncio.sleep(config.request_delay)

        progress_bar.update(1)
        progress_bar.set_postfix(last=collection_id, items=len(items))
        return collection_id, items


async def extract(client: httpx.AsyncClient, config: Config) -> tuple[list[dict], dict[str, list[dict]]]:
    """Fetch all collections and their items concurrently."""
    print(f"Fetching collections from {config.source_url} ...")
    collections = await fetch_collections(client, config)
    print(f"Found {len(collections)} collection(s)\n")

    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    items_by_collection: dict[str, list[dict]] = {}

    with tqdm(total=len(collections), desc="Fetching items", unit="collection") as progress_bar:
        tasks = [
            fetch_items_for_collection(client, col["id"], config, semaphore, progress_bar)
            for col in collections
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for col, result in zip(collections, results):
        if isinstance(result, Exception):
            tqdm.write(f"  ERROR '{col['id']}': {result}")
            items_by_collection[col["id"]] = []
        else:
            _, items = result
            items_by_collection[col["id"]] = items

    return collections, items_by_collection


# ---------------------------------------------------------------------------
# Transform / Write
# ---------------------------------------------------------------------------


def write_ndjson(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_output(
    collections: list[dict],
    items_by_collection: dict[str, list[dict]],
) -> tuple[Path, list[Path]]:
    """Write collections and per-collection items to NDJSON files."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    collections_path = OUTPUT_DIR / "collections.ndjson"
    write_ndjson(collections_path, collections)
    print(f"Wrote {len(collections)} collections → {collections_path}")

    items_paths: list[Path] = []
    for collection_id, items in items_by_collection.items():
        if items:
            path = OUTPUT_DIR / f"{collection_id}_items.ndjson"
            write_ndjson(path, items)
            items_paths.append(path)
            print(f"  {collection_id}: {len(items)} items → {path.name}")

    return collections_path, items_paths


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------


def _iter_ndjson(path: Path) -> list[dict]:
    """Read an NDJSON file as a list of dicts using the standard json module."""
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_into_pgstac(
    collections_path: Path,
    items_paths: list[Path],
    database_url: str,
) -> dict[str, int]:
    """Load NDJSON files into pgSTAC using pypgstac."""
    loaded: dict[str, int] = {"collections": 0, "items": 0}

    with PgstacDB(dsn=database_url) as db:
        loader = Loader(db=db)

        collections = _iter_ndjson(collections_path)
        loader.load_collections(iter(collections), insert_mode=Methods.insert_ignore)
        loaded["collections"] = len(collections)

        for path in tqdm(items_paths, desc="Loading items into pgSTAC", unit="collection"):
            items = _iter_ndjson(path)
            loader.load_items(iter(items), insert_mode=Methods.insert_ignore)
            loaded["items"] += len(items)

    return loaded


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def write_report(
    start_time: float,
    config: Config,
    collections: list[dict],
    items_by_collection: dict[str, list[dict]],
    loaded: dict[str, int] | None,
    errors: list[str],
) -> None:
    total_items = sum(len(v) for v in items_by_collection.values())
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - start_time, 2),
        "source_url": config.source_url,
        "collections": {
            "extracted": len(collections),
            "loaded": loaded["collections"] if loaded else 0,
        },
        "items": {
            "extracted": total_items,
            "loaded": loaded["items"] if loaded else 0,
        },
        "errors": errors,
    }

    OUTPUT_DIR.mkdir(exist_ok=True)
    report_path = OUTPUT_DIR / "migration_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print("\n" + "=" * 52)
    print("Migration Summary")
    print("=" * 52)
    print(f"  Duration    : {report['duration_seconds']}s")
    print(f"  Collections : {report['collections']['extracted']} extracted, {report['collections']['loaded']} loaded")
    print(f"  Items       : {report['items']['extracted']} extracted, {report['items']['loaded']} loaded")
    if errors:
        print(f"  Errors      : {len(errors)}")
        for err in errors:
            print(f"    - {err}")
    print(f"\n  Full report : {report_path}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def run(config: Config, dry_run: bool) -> None:
    start_time = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:
        collections, items_by_collection = await extract(client, config)

    errors = [
        f"{cid}: 0 items fetched"
        for cid, items in items_by_collection.items()
        if not items
    ]

    print()
    collections_path, items_paths = write_output(collections, items_by_collection)

    loaded: dict[str, int] | None = None
    if dry_run:
        print("\n--dry-run: skipping pgSTAC load.")
    else:
        print("\nLoading into pgSTAC ...")
        loaded = load_into_pgstac(collections_path, items_paths, config.database_url)
        print(f"Loaded {loaded['collections']} collections and {loaded['items']} items.")

    write_report(start_time, config, collections, items_by_collection, loaded, errors)


if __name__ == "__main__":
    config, dry_run = parse_args()
    asyncio.run(run(config, dry_run))
