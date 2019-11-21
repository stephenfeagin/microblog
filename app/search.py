"""
app/search.py
"""
from typing import List, Tuple

from flask import current_app

from . import db


def add_to_index(index: str, model: db.Model) -> None:
    """Add a database entry to a given Elasticsearch index"""

    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index: str, model: db.Model) -> None:
    """Remove a database entry from a given Elasticsearch index"""

    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index: str, query: str, page: int, per_page: int) -> Tuple[List[int], int]:
    """Searches a given Elasticsearch index for a provided query
    :param index: Name of the Elasticsearch index to search
    :type index: str
    :param query: Query string to search
    :type query: str
    :param page: Results page number
    :type page: int
    :param per_page: Number of results provided per page
    :type per_page: int

    :return: A tuple containing the IDs of the hits and the total number of results
    :rtype: Tuple[List[int], int]
    """
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        body={
            "query": {"multi_match": {"query": query, "fields": ["*"]}},
            "from": (page - 1) * per_page,
            "size": per_page,
        },
    )
    ids = [int(hit["_id"]) for hit in search["hits"]["hits"]]
    return ids, search["hits"]["total"]["value"]
