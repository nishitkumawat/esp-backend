import logging

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            from django.apps import apps  # ✅ lazy import
            ErrorLog = apps.get_model('iot', 'ErrorLog')

            ErrorLog.objects.create(
                message=record.getMessage(),
                traceback=self.format(record)
            )
        except Exception:
            pass  # prevent infinite crash loop