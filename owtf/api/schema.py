import json
from functools import wraps

import jsonschema
import tornado.gen


try:
    from tornado.concurrent import is_future
except ImportError:
    # For tornado 3.x.x
    from tornado.concurrent import Future
    is_future = lambda x: isinstance(x, Future)

from owtf.utils.http import container, deep_update
from owtf.lib.exceptions import APIError


class NoObjectDefaults(Exception):
    """ Raised when a schema type object ({"type": "object"}) has no "default"
    key and one of their properties also don't have a "default" key.
    """


def get_object_defaults(object_schema):
    """
    Extracts default values dict (nested) from an type object schema.

    :param object_schema: Schema type object
    :type  object_schema: dict
    :returns: Nested dict with defaults values
    """
    default = {}
    for k, schema in object_schema.get('properties', {}).items():

        if schema.get('type') == 'object':
            if 'default' in schema:
                default[k] = schema['default']

            try:
                object_defaults = get_object_defaults(schema)
            except NoObjectDefaults:
                if 'default' not in schema:
                    raise NoObjectDefaults
            else:
                if 'default' not in schema:
                    default[k] = {}

                default[k].update(object_defaults)
        else:
            if 'default' in schema:
                default[k] = schema['default']

    if default:
        return default

    raise NoObjectDefaults


def input_schema_clean(input_, input_schema):
    """
    Updates schema default values with input data.

    :param input_: Input data
    :type  input_: dict
    :param input_schema: Input schema
    :type  input_schema: dict
    :returns: Nested dict with data (default values updated with input data)
    :rtype: dict
    """
    if input_schema.get('type') == 'object':
        try:
            defaults = get_object_defaults(input_schema)
        except NoObjectDefaults:
            pass
        else:
            return deep_update(defaults, input_)
    return input_


def validate(input_schema=None, output_schema=None,
             input_example=None, output_example=None,
             validator_cls=None,
             format_checker=None, on_empty_404=False,
             use_defaults=False):
    """Parameterized decorator for schema validation

    :type validator_cls: IValidator class
    :type format_checker: jsonschema.FormatChecker or None
    :type on_empty_404: bool
    :param on_empty_404: If this is set, and the result from the
        decorated method is a false value, a 404 will be raised.
    :type use_defaults: bool
    :param use_defaults: If this is set, will put 'default' keys
        from schema to self.body (If schema type is object). Example:
            {
                'published': {'type': 'bool', 'default': False}
            }
        self.body will contains 'published' key with value False if no one
        comes from request, also works with nested schemas.
    """
    @container
    def _validate(rh_method):
        """Decorator for RequestHandler schema validation

        This decorator:

            - Validates request body against input schema of the method
            - Calls the ``rh_method`` and gets output from it
            - Validates output against output schema of the method
            - Calls ``JSendMixin.success`` to write the validated output

        :type  rh_method: function
        :param rh_method: The RequestHandler method to be decorated
        :returns: The decorated method
        :raises ValidationError: If input is invalid as per the schema
            or malformed
        :raises TypeError: If the output is invalid as per the schema
            or malformed
        :raises APIError: If the output is a false value and
            on_empty_404 is True, an HTTP 404 error is returned
        """
        @wraps(rh_method)
        @tornado.gen.coroutine
        def _wrapper(self, *args, **kwargs):
            # In case the specified input_schema is ``None``, we
            #   don't json.loads the input, but just set it to ``None``
            #   instead.
            if input_schema is not None:
                # Attempt to json.loads the input
                try:
                    # TODO: Assuming UTF-8 encoding for all requests,
                    #   find a nice way of determining this from charset
                    #   in headers if provided
                    encoding = "UTF-8"
                    input_ = json.loads(self.request.body.decode(encoding))
                except ValueError as e:
                    raise jsonschema.ValidationError(
                        "Input is malformed; could not decode JSON object."
                    )

                if use_defaults:
                    input_ = input_schema_clean(input_, input_schema)

                # Validate the received input
                jsonschema.validate(
                    input_,
                    input_schema,
                    cls=validator_cls,
                    format_checker=format_checker
                )
            else:
                input_ = None

            # A json.loads'd version of self.request["body"] is now available
            #   as self.body
            setattr(self, "body", input_)
            # Call the requesthandler method
            output = rh_method(self, *args, **kwargs)
            # If the rh_method returned a Future a la `raise Return(value)`
            #   we grab the output.
            if is_future(output):
                output = yield output

            # if output is empty, auto return the error 404.
            if not output and on_empty_404:
                raise APIError(404, "Resource not found.")

            if output_schema is not None:
                # We wrap output in an object before validating in case
                #  output is a string (and ergo not a validatable JSON object)
                try:
                    jsonschema.validate(
                        {"result": output},
                        {
                            "type": "object",
                            "properties": {
                                "result": output_schema
                            },
                            "required": ["result"]
                        }
                    )
                except jsonschema.ValidationError as e:
                    # We essentially re-raise this as a TypeError because
                    #  we don't want this error data passed back to the client
                    #  because it's a fault on our end. The client should
                    #  only see a 500 - Internal Server Error.
                    raise TypeError(str(e))

            # If no ValidationError has been raised up until here, we write
            #  back output
            self.success(output)

        setattr(_wrapper, "input_schema", input_schema)
        setattr(_wrapper, "output_schema", output_schema)
        setattr(_wrapper, "input_example", input_example)
        setattr(_wrapper, "output_example", output_example)

        return _wrapper
    return _validate
