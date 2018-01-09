import datetime
import decimal
import json
import traceback


class MoreTypesJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder that allows for more common Python data types.
    In addition to the defaults handled by ``json``, this also supports:
        * ``datetime.datetime``
        * ``datetime.date``
        * ``datetime.time``
        * ``decimal.Decimal``
    """
    def default(self, data):
        if isinstance(data, (datetime.datetime, datetime.date, datetime.time)):
            return data.isoformat()
        elif isinstance(data, decimal.Decimal):
            return str(data)
        else:
            return super(MoreTypesJSONEncoder, self).default(data)


def format_traceback(exc_info):
    stack = traceback.format_stack()
    stack = stack[:-2]
    stack.extend(traceback.format_tb(exc_info[2]))
    stack.extend(traceback.format_exception_only(exc_info[0], exc_info[1]))
    stack_str = "Traceback (most recent call last):\n"
    stack_str += "".join(stack)
    # Remove the last \n
    stack_str = stack_str[:-1]
    return stack_str


class Serializer(object):
    """
    A base serialization class.

    Defines the protocol expected of a serializer, but only raises
    ``NotImplementedError``.

    Either subclass this or provide an object with the same
    ``deserialize/serialize`` methods on it.
    """
    def deserialize(self, body):
        """
        Handles deserializing data coming from the user.

        Should return a plain Python data type (such as a dict or list)
        containing the data.

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized data
        :rtype: ``list`` or ``dict``
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def serialize(self, data):
        """
        Handles serializing data being sent to the user.

        Should return a plain Python string containing the serialized data
        in the appropriate format.

        :param data: The body for the response
        :type data: string

        :returns: A serialized version of the data
        :rtype: string
        """
        raise NotImplementedError("Subclasses must implement this method.")


class JSONSerializer(Serializer):
    def deserialize(self, body):
        """
        The low-level deserialization.

        Underpins ``deserialize``, ``deserialize_list`` &
        ``deserialize_detail``.

        Has no built-in smarts, simply loads the JSON.

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized data
        :rtype: ``list`` or ``dict``
        """
        if isinstance(body, bytes):
            return json.loads(body.decode('utf-8'))
        return json.loads(body)

    def serialize(self, data):
        """
        The low-level serialization.

        Underpins ``serialize``, ``serialize_list`` &
        ``serialize_detail``.

        Has no built-in smarts, simply dumps the JSON.

        :param data: The body for the response
        :type data: string

        :returns: A serialized version of the data
        :rtype: string
        """
        return json.dumps(data, cls=MoreTypesJSONEncoder)
