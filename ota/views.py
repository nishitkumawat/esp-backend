from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Device, Firmware
import json


@csrf_exempt
def ota_check(request, device_id):

    version = request.GET.get("version", "")

    device, _ = Device.objects.get_or_create(device_id=device_id)
    device.current_version = version
    device.save()

    fw = Firmware.objects.filter(released=True).order_by("-created_at").first()

    if not fw or fw.version == version:
        return JsonResponse({"update": False})

    return JsonResponse({
        "update": True,
        "version": fw.version,
        "url": request.build_absolute_uri(fw.file.url),
        "checksum": fw.checksum
    })


@csrf_exempt
def ota_status(request, device_id):

    try:
        data = json.loads(request.body.decode())
    except:
        return JsonResponse({"ok": False}, status=400)

    version = data.get("version", "")

    Device.objects.filter(device_id=device_id).update(
        current_version=version
    )

    return JsonResponse({"ok": True})
