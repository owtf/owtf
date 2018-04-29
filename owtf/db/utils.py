import math
from collections import namedtuple

from sqlalchemy.sql import and_, or_


def filter_none(kwargs):
    """
    Remove all `None` values froma  given dict. SQLAlchemy does not
    like to have values that are None passed to it.
    :param kwargs: Dict to filter
    :return: Dict without any 'None' values
    """
    n_kwargs = {}
    for k, v in kwargs.items():
        if v:
            n_kwargs[k] = v
    return n_kwargs


def session_query(model):
    """
    Returns a SQLAlchemy query object for the specified `model`.
    If `model` has a ``query`` attribute already, that object will be returned.
    Otherwise a query will be created and returned based on `session`.
    :param model: sqlalchemy model
    :return: query object for model
    """
    from owtf.db.session import get_scoped_session

    session = get_scoped_session()

    return model.query if hasattr(model, "query") else session.query(model)


def create_query(model, kwargs):
    """
    Returns a SQLAlchemy query object for specified `model`. Model
    filtered by the kwargs passed.
    :param model:
    :param kwargs:
    :return:
    """
    s = session_query(model)
    return s.filter_by(**kwargs)


def find_all(query, model, kwargs):
    """
    Returns a query object that ensures that all kwargs
    are present.
    :param query:
    :param model:
    :param kwargs:
    :return:
    """
    conditions = []
    kwargs = filter_none(kwargs)
    for attr, value in kwargs.items():
        if not isinstance(value, list):
            value = value.split(",")

        conditions.append(get_model_column(model, attr).in_(value))

    return query.filter(and_(*conditions))


def get_model_column(model, field):
    if field in getattr(model, "sensitive_fields", ()):
        raise AttrNotFound(field)
    column = model.__table__.columns._data.get(field, None)
    if column is None:
        raise AttrNotFound(field)

    return column


def find_any(query, model, kwargs):
    """
    Returns a query object that allows any kwarg
    to be present.
    :param query:
    :param model:
    :param kwargs:
    :return:
    """
    or_args = []
    for attr, value in kwargs.items():
        or_args.append(or_(get_model_column(model, attr) == value))
    exprs = or_(*or_args)
    return query.filter(exprs)


def filter(query, model, terms):
    """
    Helper that searched for 'like' strings in column values.
    :param query:
    :param model:
    :param terms:
    :return:
    """
    column = get_model_column(model, terms[0])
    return query.filter(column.ilike("%{}%".format(terms[1])))


def sort(query, model, field, direction):
    """
    Returns objects of the specified `model` in the field and direction
    given
    :param query:
    :param model:
    :param field:
    :param direction:
    """
    column = get_model_column(model, field)
    return query.order_by(column.desc() if direction == "desc" else column.asc())


def apply_pagination(query, page_number=None, page_size=None):
    """Apply pagination to a SQLAlchemy query object.
    :param page_number:
        Page to be returned (starts and defaults to 1).
    :param page_size:
        Maximum number of results to be returned in the page (defaults
        to the total results).
    :returns:
        A 2-tuple with the paginated SQLAlchemy query object and
        a pagination namedtuple.
        The pagination object contains information about the results
        and pages: ``page_size`` (defaults to ``total_results``),
        ``page_number`` (defaults to 1), ``num_pages`` and
        ``total_results``.
    Basic usage::
        query, pagination = apply_pagination(query, 1, 10)
        >>> len(query)
        10
        >>> pagination.page_size
        10
        >>> pagination.page_number
        1
        >>> pagination.num_pages
        3
        >>> pagination.total_results
        22
        >>> page_size, page_number, num_pages, total_results = pagination
    """
    total_results = query.count()
    query = _limit(query, page_size)

    # Page size defaults to total results
    if page_size is None or (page_size > total_results and total_results > 0):
        page_size = total_results

    query = _offset(query, page_number, page_size)

    # Page number defaults to 1
    if page_number is None:
        page_number = 1

    num_pages = _calculate_num_pages(page_number, page_size, total_results)

    Pagination = namedtuple("Pagination", ["page_number", "page_size", "num_pages", "total_results"])
    return query, Pagination(page_number, page_size, num_pages, total_results)


def _limit(query, page_size):
    if page_size is not None:
        if page_size < 0:
            raise Exception("Page size should not be negative: {}".format(page_size))

        query = query.limit(page_size)

    return query


def _offset(query, page_number, page_size):
    if page_number is not None:
        if page_number < 1:
            raise Exception("Page number should be positive: {}".format(page_number))

        query = query.offset((page_number - 1) * page_size)

    return query


def _calculate_num_pages(page_number, page_size, total_results):
    if page_size == 0:
        return 0

    return math.ceil(total_results / page_size)
