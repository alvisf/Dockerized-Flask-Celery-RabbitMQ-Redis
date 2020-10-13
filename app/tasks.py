''' Tasks related to our celery functions '''

import time
import random
import datetime

from io import BytesIO
from celery import Celery, current_task
from celery.result import AsyncResult
# from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
# from matplotlib.figure import Figure
# from matplotlib.dates import DateFormatter

from PIL import Image  
import os
import time

REDIS_URL = 'redis://redis:6379/0'
BROKER_URL = 'amqp://admin:mypass@rabbit//'

CELERY = Celery('tasks',
                backend=REDIS_URL,
                broker=BROKER_URL)

CELERY.conf.accept_content = ['json', 'msgpack']
CELERY.conf.result_serializer = 'msgpack'

def get_job(job_id):
    '''
    To be called from our web app.
    The job ID is passed and the celery job is returned.
    '''
    return AsyncResult(job_id, app=CELERY)

@CELERY.task()
# def get_data_from_strava():
#     '''
#     Generate a random image.
#     A sleep makes this task take artifically longer.
#     '''
#     current_task.update_state(state='PROGRESS', meta={'current':0.1})
#     time.sleep(2)
#     current_task.update_state(state='PROGRESS', meta={'current':0.3})
#     fig = Figure()
#     ax_handle = fig.add_subplot(111)
#     x_axis = []
#     y_axis = []
#     now = datetime.datetime.now()
#     delta = datetime.timedelta(days=1)
#     current_task.update_state(state='PROGRESS', meta={'current':0.5})
#     for _ in range(10):
#         x_axis.append(now)
#         now += delta
#         y_axis.append(random.randint(0, 1000))
#     ax_handle.plot_date(x_axis, y_axis, '-')
#     ax_handle.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
#     fig.autofmt_xdate()
#     canvas = FigureCanvas(fig)
#     current_task.update_state(state='PROGRESS', meta={'current':0.8})
#     png_output = BytesIO()
#     canvas.print_png(png_output)
#     out = png_output.getvalue()
#     return out

def image_demension(img):
    time.sleep(2)
    im = Image.open(img)  
    width, height = im.size  

    # im.show()
    # # Size of the image in pixels (size of orginal image)  
    # # (This is not mandatory)  
    # # width, height = im.size  

    # Setting the points for cropped image  
    left = 4
    top = height / 5
    right = 154
    bottom = 3 * height / 5

    # Cropped image of above dimension  
    # (It will not change orginal image)  
    im1 = im.crop((left, top, right, bottom)) 
    newsize = (300, 300) 
    im1 = im1.resize(newsize) 
    width, height = im1.size  
    location=os.path.join('static/worker-img','cropped_img.'+im.format.lower())
    im1.save(os.path.join('static/worker-img','cropped_img.'+im.format.lower()))   
    print(width,height)
    print("pass")

    return location
