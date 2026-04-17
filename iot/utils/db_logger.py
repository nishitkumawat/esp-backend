import logging
import traceback

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            from django.apps import apps
            ErrorLog = apps.get_model('iot', 'ErrorLog')

            message = record.getMessage()

            full_traceback = ""

            # If exception exists, capture real traceback
            if record.exc_info:
                full_traceback = "".join(
                    traceback.format_exception(*record.exc_info)
                )
            else:
                full_traceback = self.format(record)

            ErrorLog.objects.create(
                message=message[:1000],
                traceback=full_traceback[:20000]
            )

        except Exception:
            pass