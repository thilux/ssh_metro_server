

class JsonTemplate(object):
    """
    Super class representing a JSON representable object. It provides methods for dict to object instance transformation
    and vice versa.

    It makes use of eval and exec to generate data in a seamless way, based on the different subclass specifications.
    """

    class EmptyTemplate():
        def __init__(self):
            pass

    mandatory_fields = []
    optional_fields = []
    read_only_fields = []

    @classmethod
    def get_instance_from_json(cls, json_dict):
        if cls.__validate_json(json_dict):
            instance_init_vals = ''
            for field in (cls.mandatory_fields + cls.optional_fields):
                if field in json_dict:
                    if type(json_dict[field]) == str:
                        instance_init_vals += '%s="%s",' % (field, eval('json_dict["%s"]' % field))
                    else:
                        instance_init_vals += '%s=%s,' % (field, eval('json_dict["%s"]' % field))

            instance_init_vals = ''.join(instance_init_vals[:-1])
            instance_model = 'cls(%s)' % instance_init_vals
            return eval(instance_model)
        else:
            raise TypeError('Invalid format for type: %s' % cls.__name__)

    @classmethod
    def __validate_json(cls, json_str):
        for field in cls.mandatory_fields:
            if field not in json_str:
                return False

        for dict_key in json_str:
            if dict_key not in (cls.mandatory_fields + cls.optional_fields):
                return False
        return True

    def get_dict(self):
        result_dict = dict()
        for field in (self.mandatory_fields + self.optional_fields + self.read_only_fields):
            exec('result_dict["%s"] = self.%s' % (field, field))
        return result_dict


class ServerInfo(JsonTemplate):
    """
    The object representation of the server information. It holds information of the Metro Server server information.
    """

    mandatory_fields = ['host', 'operating_system', 'ip']

    def __init__(self, host, operating_system, ip):
        self.host = host
        self.operating_system = operating_system
        self.ip = ip


class Metro(JsonTemplate):
    """
    The object representation of a Metro. It holds information on the original host and port plus the server host and
    port for clients to connect through SSH.
    """

    mandatory_fields = ['username', 'password', 'original_host']
    optional_fields = ['original_port', ]  # 'metro_host', 'metro_port'] -> These should not be accepted in the request
    read_only_fields = ['metro_host', 'metro_port']

    def __init__(self, username, password, original_host, original_port=22, metro_host=None, metro_port=None):
        self.username = username
        self.password = password
        self.original_host = original_host
        self.original_port = original_port
        self.metro_host = metro_host
        self.metro_port = metro_port
