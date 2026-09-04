from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import aiohttp
from core.constants import REQUEST_TIMEOUT
from database.models import Artist, Influence

logger = logging.getLogger(__name__)

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "SonataBot/1.0 (https://github.com/henri-bot/sonata-bot; contact: henri@example.com)"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}
INFLUENCE_TTL = timedelta(days=7)


async def search_artist_wikidata(artist_name: str) -> str | None:
    """Search for an artist on Wikidata and return their QID."""
    params = {
        "action": "wbsearchentities",
        "search": artist_name,
        "language": "en",
        "type": "item",
        "format": "json",
        "limit": 1,
    }

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                WIKIDATA_API,
                params=params,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                headers=HEADERS,
            ) as response,
        ):
            if response.status == 200:
                data = await response.json()
                entities = data.get("search", [])

                for entity in entities:
                    if entity.get("id"):
                        return entity["id"]

                return None

            logger.error(
                "Wikidata search failed with status code: %s",
                response.status,
            )

            return None

    except Exception:
        logger.exception("Failed to search Wikidata for artist %s", artist_name)

        return None


async def get_influences(qid: str) -> list[str]:
    """Get artists that influenced the given artist (P737 claims)."""
    cached = _get_cached_relations(qid, direction="incoming")
    if cached is not None:
        return cached

    query = f"""
    SELECT ?item ?itemLabel WHERE {{
      wd:{qid} wdt:P737 ?item.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """

    bindings = await _query_sparql(query)
    return _store_and_label(qid, bindings, direction="influence")


async def get_followers(qid: str) -> list[str]:
    """Get artists influenced by the given artist (reverse P737)."""
    cached = _get_cached_relations(qid, direction="outgoing")
    if cached is not None:
        return cached

    query = f"""
    SELECT ?item ?itemLabel WHERE {{
      ?item wdt:P737 wd:{qid}.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """

    bindings = await _query_sparql(query)
    return _store_and_label(qid, bindings, direction="follower")


def _get_cached_relations(qid: str, direction: str) -> list[str] | None:
    try:
        artist = Artist.get_or_none(Artist.wikidata_qid == qid)
        if not artist or not artist.last_influences_refresh:
            return None

        last_refresh = artist.last_influences_refresh
        if isinstance(last_refresh, str):
            for fmt in (
                "%Y-%m-%d %H:%M:%S.%f%z",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ):
                try:
                    last_refresh = datetime.strptime(last_refresh, fmt)  # noqa: DTZ007
                    break
                except ValueError:
                    continue
            else:
                return None

        if last_refresh.tzinfo is None:
            last_refresh = last_refresh.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) - last_refresh > INFLUENCE_TTL:
            return None

        if direction == "incoming":
            return [
                rel.from_artist.name
                for rel in Influence.select().where(Influence.to_artist == artist)
                if rel.from_artist.name
            ]

        return [
            rel.to_artist.name
            for rel in Influence.select().where(Influence.from_artist == artist)
            if rel.to_artist.name
        ]
    except Exception:
        logger.exception("Failed to load cached influences for %s", qid)
        return None


def _store_and_label(
    source_qid: str, bindings: list[dict], direction: str
) -> list[str]:
    names: list[str] = []
    source_artist, _ = Artist.get_or_create(
        wikidata_qid=source_qid, defaults={"name": None}
    )

    for binding in bindings:
        qid = binding.get("item", {}).get("value", "").split("/")[-1]
        label = binding.get("itemLabel", {}).get("value", "")

        if not qid or not label:
            continue

        if label.startswith("Q") and label[1:].isdigit():
            continue

        artist, _ = Artist.get_or_create(wikidata_qid=qid, defaults={"name": label})
        if artist.name != label:
            artist.name = label
            artist.save()

        if direction == "influence":
            Influence.get_or_create(from_artist=artist, to_artist=source_artist)
        else:
            Influence.get_or_create(from_artist=source_artist, to_artist=artist)

        names.append(label)

    source_artist.last_influences_refresh = datetime.now(timezone.utc)
    source_artist.save()

    return names


async def _query_sparql(query: str) -> list[dict]:
    """Execute a SPARQL query and return bindings."""
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                WIKIDATA_SPARQL,
                data={"query": query, "format": "json"},
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                headers={**HEADERS, "Accept": "application/sparql-results+json"},
            ) as response,
        ):
            if response.status == 200:
                data = await response.json()
                return data.get("results", {}).get("bindings", [])

            logger.error(
                "Wikidata SPARQL query failed with status code: %s",
                response.status,
            )

            return []

    except Exception:
        logger.exception("Failed to execute Wikidata SPARQL query")

        return []
