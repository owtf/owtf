from framework.dependency_management.interfaces import AbstractInterface


class ServiceLocator:

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
        "vulnexp_db",
        "worker_manager",
        "zap_api",
        "zest",
        "target",
        "reporter"
    ]

    @classmethod
    def register_component(cls, name, component):
        if cls.component_should_implement_interface(name):
            assert isinstance(component, AbstractInterface)
        if name not in cls.registry:
            cls.registry[name] = component

    @classmethod
    def component_should_implement_interface(cls, name):
        return name in cls.components_implementing_interfaces

    @classmethod
    def get_component(cls, name):
        if name in cls.registry:
            return cls.registry[name]
        else:
            return None

    @classmethod
    def already_registered(cls, name):
        return cls.registry.has_key(name)


class BaseComponent():
    def register_in_service_locator(self):
        ServiceLocator.register_component(self.COMPONENT_NAME, self)  # Defined in subclasses

    @classmethod
    def get_component(cls, component_name):
        if ServiceLocator.already_registered(component_name):
            return ServiceLocator.get_component(component_name)
        else:
            raise ComponentNotFoundException("Component not found in ServiceLocator: " + component_name)


class ComponentNotFoundException(Exception):

    def __init__(self, message):
        self.message = message