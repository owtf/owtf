from framework.dependency_management.interfaces import AbstractInterface


class ServiceLocator:
    """Object whose responsibility is to be able to store and retrieve components from memory.
       Acts as a global access point to all the components in the OWTF framework.
    """

    registry = {}

    components_implementing_interfaces = [
        "command_register",
        "db",
        "db_config",
        "db_error",
        "db_plugin",
        "config",
        "error_handler",
        "mapping_db",
        "plugin_handler",
        "plugin_output",
        "requester",
        "resource",
        "shell",
        "timer",
        "transaction",
        "url_manager",
        "worker_manager",
        "zap_api",
        "zest",
        "target",
        "reporter"
    ]

    @classmethod
    def register_component(cls, name, component):
        """Registers a component in the registry.

        :param str name: Name of the component.
        :param object component: Instance of the component.
        """

        if cls._component_should_implement_interface(name):
            assert isinstance(component, AbstractInterface)
        if name not in cls.registry:
            cls.registry[name] = component

    @classmethod
    def _component_should_implement_interface(cls, name):
        return name in cls.components_implementing_interfaces

    @classmethod
    def get_component(cls, name):
        """Retrieves a component from the registry.

        :param: str name: Name of the component.
        """
        if name in cls.registry:
            return cls.registry[name]
        else:
            return None

    @classmethod
    def already_registered(cls, name):
        return cls.registry.has_key(name)


class BaseComponent():
    """Base class for all components. Provides the feature of accessing directly to the Service Locator"""

    def register_in_service_locator(self):
        """Register the current component in the service locator. The subclass must define a COMPONENT_NAME
           constant with the name of the component.
        """

        ServiceLocator.register_component(self.COMPONENT_NAME, self)  # Defined in subclasses

    @classmethod
    def get_component(cls, component_name):
        """Retrieves a component from the Service Locator

        :param str component_name: Name of the component.

        :raises: :class: `ComponentNotFoundException` -- If the component is not registered.

        :return: The component instance registered with the given name.
        """
        if ServiceLocator.already_registered(component_name):
            return ServiceLocator.get_component(component_name)
        else:
            raise ComponentNotFoundException("Component not found in ServiceLocator: " + component_name)


class ComponentNotFoundException(Exception):

    def __init__(self, message):
        self.message = message
