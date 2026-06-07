import os
from pluginbase import PluginBase


class LoadPlugins(object):
    def __init__(self, name):
        self.name = name
        self.load_plugins()

    def load_plugins(self):
        from base import BASE_DIR
        find_path = os.path.normcase(os.path.join(BASE_DIR, "src/plugins"))

        self.plugin_base = PluginBase(package='appRun_plugins', searchpath=[find_path])

        self.plugin_source = self.plugin_base.make_plugin_source(searchpath=[find_path], identifier=self.name)


if __name__ == "__main__":
    pass
