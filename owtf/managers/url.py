"""
owtf.db.url_manager
~~~~~~~~~~~~~~~~~~~

The DB stores HTTP transactions, unique URLs and more.
"""

from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import URLManagerInterface
from owtf.lib.exceptions import InvalidParameterType
from owtf.lib.general import *
from owtf.managers.target import target_required
from owtf.db import models


class URLManager(BaseComponent, URLManagerInterface):
    num_urls_before = 0

    COMPONENT_NAME = "url_manager"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.target = self.get_component("target")
        self.db = self.get_component("db")
        # Compile regular expressions once at the beginning for speed purposes:
        self.is_file_regex = re.compile(self.config.get_val('REGEXP_FILE_URL'), re.IGNORECASE)
        self.is_small_file_regex = re.compile(self.config.get_val('REGEXP_SMALL_FILE_URL'), re.IGNORECASE)
        self.is_image_regex = re.compile(self.config.get_val('REGEXP_IMAGE_URL'), re.IGNORECASE)
        self.is_url_regex = re.compile(self.config.get_val('REGEXP_VALID_URL'), re.IGNORECASE)
        self.is_ssi_regex = re.compile(self.config.get_val('REGEXP_SSI_URL'), re.IGNORECASE)

    def is_regex_url(self, url, regexp):
        """ Wrapper method to search URL for different properties based on regex

        :param url: URL
        :type url: `str`
        :param regexp: Regular expression for the property
        :type url: `str`
        :return: True/False
        :rtype: `bool`
        """
        return len(regexp.findall(url)) > 0

    def small_file_url(self, url):
        """ Checks if small file url

        :param url: URL
        :type url: `str`
        :return: True/False
        :rtype: `bool`
        """
        return self.is_regex_url(url, self.is_small_file_regex)

    def file_url(self, url):
        """ Checks if it is a file url

        :param url: URL
        :type url: `str`
        :return: True/False
        :rtype: `bool`
        """
        return self.is_regex_url(url, self.is_file_regex)

    def image_url(self, url):
        """ Checks if it is an image url

        :param url: URL
        :type url: `str`
        :return: True/False
        :rtype: `bool`
        """
        return self.is_regex_url(url, self.is_image_regex)

    def ssi_url(self, url):
        """ Checks if SSI url
        
        :param url: URL
        :type url: `str`
        :return: True/False
        :rtype: `bool`
        """
        return self.is_regex_url(url, self.is_ssi_regex)

    @target_required
    def add_to_db(self, url, visited, found=None, target_id=None):
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
        if self.is_url(url):  # New URL
            # Make sure URL is clean prior to saving in DB, nasty bugs
            # can happen without this
            url = url.strip()
            scope = self.target.is_url_in_scope(url)
            self.db.session.merge(models.Url(target_id=target_id, url=url, visited=visited, scope=scope))
            self.db.session.commit()

    def get_urls_to_visit(self, target=None):
        """Gets urls to visit for a target

        :param target: Target
        :type target: `str`
        :return: List of not visited URLs
        :rtype: `list`
        """
        urls = self.db.session.query(models.Url.url).filter_by(visited=False).all()
        urls = [i[0] for i in urls]
        return urls

    def is_url(self, url):
        """Check if valid URL

        :param url: URL
        :type url: `str`
        :return: True/False
        :rtype: `bool`
        """
        return self.is_regex_url(url, self.is_url_regex)

    @target_required
    def add_url(self, url, found=None, target_id=None):
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
        return self.add_to_db(url, visited, found=found, target_id=target_id)

    @target_required
    def import_processed_url(self, urls_list, target_id=None):
        """Imports a processed URL from the DB

        :param urls_list: List of URLs
        :type urls_list: `list`
        :param target_id: Target ID
        :type target_id: `int`
        :return: None
        :rtype: None
        """
        for url, visited, scope in urls_list:
            self.db.session.merge(models.Url(target_id=target_id, url=url, visited=visited, scope=scope))
        self.db.session.commit()

    @target_required
    def import_urls(self, url_list, target_id=None):
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
            if self.is_url(url):
                imported_urls.append(url)
                self.db.session.merge(models.Url(url=url, target_id=target_id))
        self.db.session.commit()
        return imported_urls  # Return imported urls

    def derive_url_dict(self, url_obj):
        """Fetch URL dict from object

        :param url_obj: URL object
        :type url_obj:
        :return: URL dict
        :rtype: `dict`
        """
        udict = dict(url_obj.__dict__)
        udict.pop("_sa_instance_state")
        return udict

    def derive_url_dicts(self, url_obj_list):
        """Derive a list of url dicts from the obj list

        :param url_obj_list: List of URL objects
        :type url_obj_list: `list`
        :return: List of URL dicts
        :rtype: `list`
        """
        dict_list = []
        for url_obj in url_obj_list:
            dict_list.append(self.derive_url_dict(url_obj))
        return dict_list

    def gen_query(self, criteria, target_id, for_stats=False):
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
        query = self.db.session.query(models.Url).filter_by(target_id=target_id)
        # Check if criteria is url search
        if criteria.get('search', None):
            if criteria.get('url', None):
                if isinstance(criteria.get('url'), list):
                    criteria['url'] = criteria['url'][0]
                query = query.filter(models.Url.url.like('%%%s%%' % criteria['url']))
        else:  # If not search
            if criteria.get('url', None):
                if isinstance(criteria.get('url'), str):
                    query = query.filter_by(url=criteria['url'])
                if isinstance(criteria.get('url'), list):
                    query = query.filter(models.Url.url.in_(criteria['url']))
        # For the following section doesn't matter if filter/search because
        # it doesn't make sense to search in a boolean column :P
        if criteria.get('visited', None):
            if isinstance(criteria.get('visited'), list):
                criteria['visited'] = criteria['visited'][0]
            query = query.filter_by(visited=self.config.ConvertStrToBool(criteria['visited']))
        if criteria.get('scope', None):
            if isinstance(criteria.get('scope'), list):
                criteria['scope'] = criteria['scope'][0]
            query = query.filter_by(scope=self.config.ConvertStrToBool(criteria['scope']))
        if not for_stats:  # Query for stats can't have limit and offset
            try:
                if criteria.get('offset', None):
                    if isinstance(criteria.get('offset'), list):
                        criteria['offset'] = criteria['offset'][0]
                    query = query.offset(int(criteria['offset']))
                if criteria.get('limit', None):
                    if isinstance(criteria.get('limit'), list):
                        criteria['limit'] = criteria['limit'][0]
                    query = query.limit(int(criteria['limit']))
            except ValueError:
                raise InvalidParameterType("Invalid parameter type for transaction db")
        return query

    @target_required
    def get_all(self, criteria, target_id=None):
        """Get all URLs based on criteria and target ID

        :param criteria: Filter criteria
        :type criteria: `dict`
        :param target_id: Target ID
        :type target_id: `int`
        :return: List of URL dicts
        :rtype: `list`
        """
        query = self.gen_query(criteria, target_id)
        results = query.all()
        return self.derive_url_dicts(results)

    @target_required
    def search_all(self, criteria, target_id=None):
        """Search all URLs based on criteria and target ID

        .note::
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
        total = self.db.session.query(models.Url).filter_by(target_id=target_id).count()
        filtered_url_objs = self.gen_query(criteria, target_id).all()
        filtered_number = self.gen_query(criteria, target_id, for_stats=True).count()
        results = {
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self.derive_url_dicts(filtered_url_objs)
        }
        return results
