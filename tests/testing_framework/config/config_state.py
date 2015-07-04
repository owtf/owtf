from collections import defaultdict
import copy

class ConfigState():
    """
    Makes a deep copy of the configuration object in order to preserve
    its state for later restoring.
    """
    def __init__(self, config_obj):
        self.Config = deepcopy(config_obj.Config)
        self.TargetConfig = deepcopy(config_obj.TargetConfig)
        self.Targets = deepcopy(config_obj.Targets)

    @staticmethod
    def restore_state(config_obj, state_obj):
        config_obj.Config = deepcopy(state_obj.Config)
        config_obj.TargetConfig = deepcopy(config_obj.TargetConfig)
        config_obj.Targets = deepcopy(config_obj.Targets)


def deepcopy(obj):
    if isinstance(obj, defaultdict) or isinstance(obj, dict):
        obj_copy = defaultdict(list)
        for key, value in obj.items():
            obj_copy[key] = deepcopy(value)
        return obj_copy
    else:
        return copy.deepcopy(obj)
