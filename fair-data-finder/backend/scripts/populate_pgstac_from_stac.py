"""Populate the Fair Data Finder with collections and items from another STAC API.

Data is written through the Fair Data Finder API (not directly into the
database), so RBAC checks, validation and item ownership all apply.

The script is laid out as notebook-style cells (`# %%`). Run it top to bottom,
or cell by cell in VS Code's interactive window.

PLAN — code still to be written.
"""

# %% Step 1 — Settings
# Everything you may want to change lives here, nowhere else:
#   SOURCE_URL       the STAC API we read from (e.g. https://earth-search.aws.element84.com/v1)
#   TARGET_URL       our own API (e.g. http://localhost:8000/api)
#   DMS_TOKEN        session cookie copied from the browser after logging in;
#                    sent to both the source API and our API
#   COLLECTION_IDS   which collections to copy (empty list = all of them)
#   MAX_ITEMS        max items per collection (keeps test runs small)
#   BATCH_SIZE       how many items to send in one bulk request

SOURCE_URL = "https://dev-fairdatafinder.deltares.nl/api/"
TARGET_URL = "http://localhost:8000/api"
DMS_TOKEN = ""  # paste the DMS_TOKEN cookie value from your browser after logging in
COLLECTION_IDS: list[str] = []
MAX_ITEMS = 100
BATCH_SIZE = 50


# %% Step 2 — Open two HTTP clients
# A client remembers a base URL, headers and cookies, so later steps only need
# to give the path (e.g. "/collections"). httpx is already installed via
# fastapi[standard]. The timeout (seconds) stops a slow server from hanging us.
import ssl

import httpx
import truststore

# Use the operating system's certificate store instead of Python's bundled list.
# Without this, networks or antivirus that re-sign HTTPS traffic (e.g. ESET)
# cause "CERTIFICATE_VERIFY_FAILED", because Windows trusts them but Python does not.
ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

# Source: the STAC API we read from. It also needs the DMS_TOKEN cookie, because
# this app protects every endpoint except the landing page and login.
# rstrip("/") removes a trailing slash from the URL, so "base_url + /collections"
# never becomes "...//collections".
source = httpx.Client(
    base_url=SOURCE_URL.rstrip("/"),
    cookies={"DMS_TOKEN": DMS_TOKEN},
    verify=ssl_context,
    timeout=60,
)

# Target: our own API. It identifies us through the DMS_TOKEN cookie, which
# is sent automatically with every request made by this client.
target = httpx.Client(
    base_url=TARGET_URL.rstrip("/"),
    cookies={"DMS_TOKEN": DMS_TOKEN},
    verify=ssl_context,
    timeout=60,
)


# %% Step 3 — Check both APIs are reachable and accept our token
# The landing page "/" is public, so it would succeed even with a bad token.
# "/collections" needs a valid login, so it tests URL and token together.
# limit=1 keeps the answer tiny: we only care about the status code.
# raise_for_status() stops the script on 4xx/5xx (e.g. 401 = bad or expired token).
response_source = source.get("/collections", params={"limit": 1})
response_source.raise_for_status()
print("source:", response_source.status_code)

response_target = target.get("/collections", params={"limit": 1})
response_target.raise_for_status()
print("target:", response_target.status_code)


# %% Step 4 — Read the collections from the source
# GET /collections returns {"collections": [...], "links": [...]}. If the list is
# paged, one link has rel="next"; we follow it until there is none.
# A "next" href is a full URL, and httpx uses a full URL as-is (it ignores base_url).
collections = []
url = "/collections"

# page = {
#    "collections": [ {...A...}, {...B...} ],   # the data we want
#    "links": [ {"rel": "next", "href": "..."}, ... ]   # navigation
#}

while url:
    response = source.get(url)
    response.raise_for_status()
    page = response.json()
    collections += page["collections"]
    url = next((link["href"] for link in page["links"] if link["rel"] == "next"), None)

# Keep only the collections listed in COLLECTION_IDS; an empty list means "all".
wanted_ids = COLLECTION_IDS or [collection["id"] for collection in collections]
collections = [c for c in collections if c["id"] in wanted_ids]
print(f"Read {len(collections)} collection(s):", [c["id"] for c in collections])


# %% Step 5 — Clean each collection
# We want an exact copy, so every link is kept EXCEPT the ones our API builds
# itself from its own address. Those would otherwise appear twice, and the
# source's copy would point at the source server instead of ours.
own_link_rels = ["self", "root", "parent", "items", "collection"]
for collection in collections:
    collection["links"] = [link for link in collection["links"] if link["rel"] not in own_link_rels]
print("Cleaned", len(collections), "collection(s)")


# %% Step 6 — Create the collections in our API
# POST each collection to our /collections endpoint. The status code tells us what happened:
#   201 = created, 409 = already exists (fine, skipped), 403 = our user lacks
#   the collection:create permission, 401 = bad or expired token.
# We do not stop on errors; we record every status code and look at them together.
collection_status = {}
for collection in collections:
    response = target.post("/collections", json=collection)
    collection_status[collection["id"]] = response.status_code
    print(collection["id"], response.status_code)
    if response.status_code not in (201, 409):
        print("   ", response.text[:300])


# %% Step 7 — Copy the items, collection by collection
# For each collection we read one page of items from the source and immediately
# write it to our API with one bulk request, then follow the "next" link.
# The first request sets the page size with limit=BATCH_SIZE; later "next" links
# already contain it. We stop at the last page or after MAX_ITEMS items.
# Items keep all their links except the ones our API builds itself (see Step 5).
# Writing through the bulk endpoint makes our API record us as the owner.
items_copied = {}
for collection in collections:
    collection_id = collection["id"]
    copied = 0
    url = f"/collections/{collection_id}/items"
    params = {"limit": BATCH_SIZE}
    while url and copied < MAX_ITEMS:
        response = source.get(url, params=params)
        response.raise_for_status()
        page = response.json()

        items = page["features"][: MAX_ITEMS - copied]
        for item in items:
            item["links"] = [link for link in item["links"] if link["rel"] not in own_link_rels]

        # The bulk endpoint expects {"items": {item_id: item}, "method": "insert" or "upsert"}
        # "upsert" updates items that already exist, so re-running the script is safe.
        body = {"items": {item["id"]: item for item in items}, "method": "upsert"}
        if items:  # a collection without items has nothing to send
            response = target.post(f"/collections/{collection_id}/bulk_items", json=body)
            response.raise_for_status()

        copied += len(items)
        url = next((link["href"] for link in page["links"] if link["rel"] == "next"), None)
        params = None
    items_copied[collection_id] = copied
    print(collection_id, "->", copied, "item(s) copied")


# %% Step 8 — Summary
# collection_status (Step 6) holds the HTTP status of each collection POST, and
# items_copied (Step 7) the number of items written per collection.
# .get(status, ...) turns a known code into words and shows anything else as FAILED.
for collection_id, status in collection_status.items():
    outcome = {201: "created", 409: "already existed"}.get(status, f"FAILED (status {status})")
    print(f"{collection_id}: collection {outcome}, {items_copied.get(collection_id, 0)} item(s) copied")
print("Total items copied:", sum(items_copied.values()))
