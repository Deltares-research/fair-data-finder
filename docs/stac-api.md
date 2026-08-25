# STAC API

## Search endpoint

The search endpoint implements the [STAC API Item Search](https://api.stacspec.org/v1.0.0/item-search/) operation.

```
GET  /api/search
POST /api/search
```

Interactive documentation is available at `http://localhost:8000/api/api.html` (Swagger UI) when the backend is running.

## CQL2 filter extension

For advanced filtering, this implementation supports the [STAC Filter Extension](https://github.com/stac-api-extensions/filter) with `filter-lang: cql2-json`.

The request body can include a `filter` object written in CQL2 JSON. The operators used in this implementation are:

| Operator | Description |
|----------|-------------|
| `and` | Combines multiple conditions |
| `like` | Matches text values |
| `>=` | Compares values such as dates |
| `s_intersects` | Checks whether an Item geometry intersects a GeoJSON geometry |

In this syntax, `op` and `args` come from the Filter Extension and CQL2 JSON expression structure, not from the core STAC Item Search parameters.

### Example — spatial filter

```json
{
  "filter-lang": "cql2-json",
  "filter": {
    "op": "s_intersects",
    "args": [
      { "property": "geometry" },
      {
        "type": "Polygon",
        "coordinates": [[[4.0, 51.0], [5.0, 51.0], [5.0, 52.0], [4.0, 52.0], [4.0, 51.0]]]
      }
    ]
  }
}
```

### Example — combined filter

```json
{
  "filter-lang": "cql2-json",
  "filter": {
    "op": "and",
    "args": [
      {
        "op": "like",
        "args": [{ "property": "properties.title" }, "%water%"]
      },
      {
        "op": ">=",
        "args": [{ "property": "properties.datetime" }, "2020-01-01T00:00:00Z"]
      }
    ]
  }
}
```
