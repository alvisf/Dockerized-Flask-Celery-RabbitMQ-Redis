import json
from flask import Flask, request
from flask import render_template, make_response
import tasks
import os
from PIL import Image
from datetime import datetime

APP = Flask(__name__)
APP.config['UPLOAD_FOLDER'] = 'static/worker-img'

@APP.route('/',methods = ['GET','POST'])
def index(): 
    '''
    Render Home Template and Post request to Upload the image to Celery task.
    '''
    if request.method == 'GET':
        return render_template("index.html")
    if request.method == 'POST':
        img = request.files['image']
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        img.save(os.path.join(APP.config['UPLOAD_FOLDER'],img.filename))
        loc = "static/worker-img/"+img.filename
        job = tasks.image_demension.delay(loc)
        return render_template("download.html",JOBID=job.id)


@APP.route('/progress')
def progress():
    '''
    Get the progress of our task and return it using a JSON object
    '''
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        if job.state == 'PROGRESS':
            return json.dumps(dict(
                state=job.state,
                progress=job.result['current'],
            ))
        elif job.state == 'SUCCESS':
            return json.dumps(dict(
                state=job.state,
                progress=1.0,
            ))
    return '{}'

@APP.route('/result.png')
def result():
    '''
    Pull our generated .png binary from redis and return it
    '''
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        png_output = job.get()
        png_output="../"+png_output
        return png_output
    else:
        return 404




if __name__ == '__main__':
    APP.run(host='0.0.0.0')
