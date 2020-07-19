import json
import traceback

from pythonjsonlogger.jsonlogger import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, json_default=json_translate, json_encoder=json.JSONEncoder, **kwargs
        )

    def add_fields(self, log_record, record, message_dict):
        log_record["level"] = record.levelname

        super().add_fields(log_record, record, message_dict)


def json_translate(obj):
    if isinstance(obj, Exception):
        return {
            "name": obj.__class__.__name__,
            "message": str(obj),
            "traceback": traceback.format_exc().splitlines(),
        }
