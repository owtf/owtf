
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