"""
owtf.managers.url
~~~~~~~~~~~~~~~~~
The DB stores HTTP transactions, unique URLs and more.
"""
from owtf.db.session import get_count, get_scoped_session
from owtf.lib.exceptions import InvalidParameterType
from owtf.managers.target import is_url_in_scope, target_required
from owtf.models.url import Url
from owtf.utils.strings import str2bool
from owtf.settings import (
    is_file_regex,
    is_image_regex,
    is_small_file_regex,
    is_ssi_regex,
    is_url_regex,
)

num_urls_before = 0


def is_regex_url(url, regexp):
    """ Wrapper method to search URL for different properties based on regex

    :param url: URL
    :type url: `str`
    :param regexp: Regular expression for the property
    :type url: `str`
    :return: True/False
    :rtype: `bool`
    """
    return len(regexp.findall(url)) > 0


def small_file_url(url):
    """ Checks if small file url

    :param url: URL
    :type url: `str`
    :return: True/False
    :rtype: `bool`
    """
    return is_regex_url(url, is_small_file_regex)


def file_url(url):
    """ Checks if it is a file url

    :param url: URL
    :type url: `str`
    :return: True/False
    :rtype: `bool`
    """
    return is_regex_url(url, is_file_regex)


def image_url(url):
    """ Checks if it is an image url

    :param url: URL
    :type url: `str`
    :return: True/False
    :rtype: `bool`
    """
    return is_regex_url(url, is_image_regex)


def ssi_url(url):
    """ Checks if SSI url

    :param url: URL
    :type url: `str`
    :return: True/False
    :rtype: `bool`
    """
    return is_regex_url(url, is_ssi_regex)


@target_required
def add_urls_to_db(session, url, visited, found=None, target_id=None):
    """Adds a URL to the DB

    :param url: URL to be added
    :type url: `str`
    :param visited: Visited or not
    :type visited: `bool`
    :param found: True/False
    :type found: `bool`
    :param target_id: Target ID
    :type target_id: `int`
    :return: None
    :rtype: None
    """
    if is_url(url):  # New URL
        # Make sure URL is clean prior to saving in DB, nasty bugs
        # can happen without this
        url = url.strip()
        scope = is_url_in_scope(url)
        session.merge(Url(target_id=target_id, url=url, visited=visited, scope=scope))
        session.commit()


def get_urls_to_visit():
    """Gets urls to visit for a target

    :param target: Target
    :type target: `str`
    :return: List of not visited URLs
    :rtype: `list`
    """
    session = get_scoped_session()
    urls = session.query(Url.url).filter_by(visited=False).all()
    urls = [i[0] for i in urls]
    return urls


def is_url(url):
    """Check if valid URL

    :param url: URL
    :type url: `str`
    :return: True/False
    :rtype: `bool`
    """
    return is_regex_url(url, is_url_regex)


@target_required
def add_url(session, url, found=None, target_id=None):
    """Adds a URL to the relevant DBs if not already added

    :param url: URL to be added
    :type url: `str`
    :param found: Visited or not
    :type found: `bool`
    :param target_id: target ID
    :type target_id: `int`
    :return: None
    :rtype: None
    """
    visited = False
    if found is not None:  # Visited URL -> Found in [ True, False ]
        visited = True
    return add_urls_to_db(session, url, visited, found=found, target_id=target_id)


@target_required
def import_processed_url(session, urls_list, target_id=None):
    """Imports a processed URL from the DB

    :param urls_list: List of URLs
    :type urls_list: `list`
    :param target_id: Target ID
    :type target_id: `int`
    :return: None
    :rtype: None
    """
    for url, visited, scope in urls_list:
        session.merge(Url(target_id=target_id, url=url, visited=visited, scope=scope))
    session.commit()


@target_required
def import_urls(session, url_list, target_id=None):
    """Extracts and classifies all URLs passed. Expects a newline separated
    URL list

    :param url_list: List of urls
    :type url_list: `list`
    :param target_id: target ID
    :type target_id: `int`
    :return: List of imported URLS
    :rtype: `list`
    """
    imported_urls = []
    for url in url_list:
        if is_url(url):
            imported_urls.append(url)
            session.merge(Url(url=url, target_id=target_id))
    session.commit()
    return imported_urls  # Return imported urls


def url_gen_query(session, criteria, target_id, for_stats=False):
    """Generate query based on criteria and target ID

    :param criteria: Filter criteria
    :type criteria: `dict`
    :param target_id: Target ID
    :type target_id: `int`
    :param for_stats: True/False
    :type for_stats: `bool`
    :return:
    :rtype:
    """
    query = session.query(Url).filter_by(target_id=target_id)
    # Check if criteria is url search
    if criteria.get("search", None):
        if criteria.get("url", None):
            if isinstance(criteria.get("url"), list):
                criteria["url"] = criteria["url"][0]
            query = query.filter(Url.url.like("%%{!s}%%".format(criteria["url"])))
    else:  # If not search
        if criteria.get("url", None):
            if isinstance(criteria.get("url"), str):
                query = query.filter_by(url=criteria["url"])
            if isinstance(criteria.get("url"), list):
                query = query.filter(Url.url.in_(criteria["url"]))
    # For the following section doesn't matter if filter/search because
    # it doesn't make sense to search in a boolean column :P
    if criteria.get("visited", None):
        if isinstance(criteria.get("visited"), list):
            criteria["visited"] = criteria["visited"][0]
        query = query.filter_by(visited=str2bool(criteria["visited"]))
    if criteria.get("scope", None):
        if isinstance(criteria.get("scope"), list):
            criteria["scope"] = criteria["scope"][0]
        query = query.filter_by(scope=str2bool(criteria["scope"]))
    if not for_stats:  # Query for stats can't have limit and offset
        try:
            if criteria.get("offset", None):
                if isinstance(criteria.get("offset"), list):
                    criteria["offset"] = criteria["offset"][0]
                query = query.offset(int(criteria["offset"]))
            if criteria.get("limit", None):
                if isinstance(criteria.get("limit"), list):
                    criteria["limit"] = criteria["limit"][0]
                query = query.limit(int(criteria["limit"]))
        except ValueError:
            raise InvalidParameterType("Invalid parameter type for transaction db")
    return query


@target_required
def get_all_urls(session, criteria, target_id=None):
    """Get all URLs based on criteria and target ID

    :param criteria: Filter criteria
    :type criteria: `dict`
    :param target_id: Target ID
    :type target_id: `int`
    :return: List of URL dicts
    :rtype: `list`
    """
    query = url_gen_query(session, criteria, target_id)
    results = query.all()
    return [url_obj.to_dict() for url_obj in results]


@target_required
def search_all_urls(session, criteria, target_id=None):
    """Search all URLs based on criteria and target ID

    .. note::
        Three things needed
            + Total number of urls
            + Filtered url
            + Filtered number of url

    :param criteria: Filter criteria
    :type criteria: `dict`
    :param target_id: Target ID
    :type target_id: `int`
    :return: Search result dict
    :rtype: `dict`
    """
    total = get_count(session.query(Url).filter_by(target_id=target_id))
    filtered_url_objs = url_gen_query(session, criteria, target_id).all()
    filtered_number = get_count(
        url_gen_query(session, criteria, target_id, for_stats=True)
    )
    results = {
        "records_total": total,
        "records_filtered": filtered_number,
        "data": [url_obj.to_dict() for url_obj in filtered_url_objs],
    }
    return results
