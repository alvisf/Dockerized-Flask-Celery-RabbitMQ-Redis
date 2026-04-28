import os
import time

from celery import Celery
from celery.result import AsyncResult
from PIL import Image

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
BROKER_URL = os.environ.get("BROKER_URL", "amqp://admin:mypass@rabbit//")

celery = Celery("tasks", backend=REDIS_URL, broker=BROKER_URL)
celery.conf.accept_content = ["json", "msgpack"]
celery.conf.result_serializer = "msgpack"


def get_job(job_id):
    return AsyncResult(job_id, app=celery)


@celery.task()
def crop_image(img_path):
    time.sleep(2)  # simulate processing delay

    im = Image.open(img_path)
    width, height = im.size

    left, right = 4, min(154, width)
    top, bottom = height // 5, 3 * height // 5
    cropped = im.crop((left, top, right, bottom)).resize((300, 300))

    ext = (im.format or "png").lower()
    out_path = os.path.join(os.path.dirname(img_path), f"cropped_img.{ext}")
    cropped.save(out_path)

    return out_path
