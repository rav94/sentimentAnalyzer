import configparser
import io
import os

class PropertyReader(object):
    def read_properties_file(self):
        base_file_path = os.path.abspath(os.path.dirname(__file__))
        env_property_file_path = os.path.join(base_file_path, "env.properties")

        with open(env_property_file_path) as f:
            config = io.StringIO()
            config.write('[dummy_section]\n')
            config.write(f.read().replace('%', '%%'))
            config.seek(0, os.SEEK_SET)

            cp = configparser.SafeConfigParser()
            cp.readfp(config)

            return dict(cp.items('dummy_section'))