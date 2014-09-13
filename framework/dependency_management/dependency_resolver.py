
class ServiceLocator:

    registry = {}

    @classmethod
    def register_component(cls, name, component):
        cls.registry[name] = component

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
        ServiceLocator.register_component(self.COMPONENT_NAME, self)

    @classmethod
    def get_component(cls, component_name):
        if ServiceLocator.already_registered(component_name):
            return ServiceLocator.get_component(component_name)
        else:
            raise ComponentNotFoundException("Component not found in ServiceLocator: " + component_name)


class ComponentNotFoundException(Exception):

    def __init__(self, message):
        self.message = message