from pythonjsonlogger.jsonlogger import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        log_record["level"] = record.levelname

        super().add_fields(log_record, record, message_dict)
