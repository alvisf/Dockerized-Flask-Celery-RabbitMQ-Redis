# Using Celery with Flask for Asynchronous Content Generation

This tutorial explains how to configure Flask, Celery, RabbitMQ and Redis, together with Docker to build a web service that dynamically generates content and loads this contend when it is ready to be displayed. We'll focus mainly on Celery and the servies that surround it. Docker is a bit more straightforward.

## Contents

1. [Part 1 - Project Structure](https://github.com/timlardner/Docker-FlaskCeleryRabbitRedis/tree/readme#part-1---project-structure)
1. [Part 2 - Creating the Flask application](https://github.com/timlardner/Docker-FlaskCeleryRabbitRedis/tree/readme#part-2---creating-the-flask-application)
1. [Part 3 - Expanding our web app to use Celery](https://github.com/timlardner/Docker-FlaskCeleryRabbitRedis/tree/readme#part-3---expanding-our-web-app-to-use-celery)
1. [Part 4 - Using Docker to package our application](https://github.com/timlardner/Docker-FlaskCeleryRabbitRedis/tree/readme#part-4---using-docker-to-package-our-application)

## Part 1 - Project Structure

The finished project structure will be as follows:
```
.
├── Dockerfile
├── docker-compose.yml
├── README.md
├── app
│   ├── app.py
│   ├── tasks.py
│   └── templates
│       ├── home.html
│       └── index.html
├── scripts
│   ├── run_celery.sh
│   └── run_web.sh
└── requirements.txt
```

## Part 2 - Creating the Flask application

First we create an folder for our app. For this example, our folder is simply called `app`. Within this folder, create an `app.py` file and an empty folder named `templates` where our HTML templates will be stored.

For our app, we first include some basic Flask libraries and create an instance of the app:

```python
from io import BytesIO
from flask import Flask, request
from flask import render_template, make_response

APP = Flask(__name__)
```

We define three routes for Flask to implement: a landing page, a secondary page that embeds and image, and a route for the image itself. Our image route generates an image dynamically. For this example, it generates a plot using `matplotlib` and some delays are also included so that the time taken to create the image is more apparent.

```python
@APP.route('/')
def index():
    return render_template('index.html')
```

```python
@APP.route('/image_page')
def image_page():
    job = tasks.get_data_from_strava.delay()
    return render_template('home.html')
```

```python
@APP.route('/result.png')
def result():
	import time
	import random
    import datetime
    from io import BytesIO
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
	from matplotlib.figure import Figure
	from matplotlib.dates import DateFormatter

	time.sleep(2)
    fig = Figure()
    ax_handle = fig.add_subplot(111)
    x_axis = []
    y_axis = []
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=1)
    current_task.update_state(state='PROGRESS', meta={'current':0.5})
    for _ in range(10):
        x_axis.append(now)
        now += delta
        y_axis.append(random.randint(0, 1000))
    ax_handle.plot_date(x_axis, y_axis, '-')
    ax_handle.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    current_task.update_state(state='PROGRESS', meta={'current':0.8})
    png_output = BytesIO()
    canvas.print_png(png_output)
    out = png_output.getvalue()
    response = make_response(out)
    response.headers['Content-Type'] = 'image/png'
    return response
```

Next, we need to open our `templates` folder and create the following two templates:

#### home.html
```html
<a href="{{ url_for('.image_page') }}">Whatever you click to get data from Strava...</a>
```

#### index.html
```html
<div id="imgpl"><img src="result.png"></div>
```

If we add the following code then run the script, we can load up our webpage and test the image generation.

```python
if __name__ == '__main__':
    APP.run(host='0.0.0.0')
``` 

We see that our page load takes a while to complete because the request to `result.png` doesn't return until the image generation has completed.

## Part 3 - Expanding our web app to use Celery

In our `app` directory, create the `tasks.py` file that will contain our Celery tasks. We add the neccessary Celery includes:

```python
from celery import Celery, current_task
from celery.result import AsyncResult
```

Assuming that our RabbitMQ service is on a host that we can reference by `rabbit` and our Redis service is on a host referred to by `redis` we can create an instance of Celery using the following:

```python
REDIS_URL = 'redis://redis:6379/0'
BROKER_URL = 'amqp://admin:mypass@rabbit//'

CELERY = Celery('tasks',
                backend=REDIS_URL,
                broker=BROKER_URL)
```

We then need to change the default serializer for results. Celery with versions 4.0 and above use JSON as a serializer, which doesn't support serialization of binary data. We can either switch back to the old default serializer (pickle) or use the newer MessagePack which supports binary data and is very efficient.

Since we're changing the serializer, we also need to tell Celery to accept the results from a non-default serializer (as well as still accepting those from JSON).

```python
CELERY.conf.accept_content = ['json', 'msgpack']
CELERY.conf.result_serializer = 'msgpack'
```

First, we'll implement a function that returns a jobs given an ID. This allows our app and the Celery tasks to talk to each other:

```python
def get_job(job_id):
    return AsyncResult(job_id, app=CELERY)
```

Next, we define the asynchronous function and move the image generation code from `app.py` and add the function decorator that allows the method to be queued for execution:

```python
@CELERY.task()
def get_data_from_strava():
    current_task.update_state(state='PROGRESS', meta={'current':0.1})
    time.sleep(2)
    current_task.update_state(state='PROGRESS', meta={'current':0.3})
    fig = Figure()
    ax_handle = fig.add_subplot(111)
    x_axis = []
    y_axis = []
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=1)
    current_task.update_state(state='PROGRESS', meta={'current':0.5})
    for _ in range(10):
        x_axis.append(now)
        now += delta
        y_axis.append(random.randint(0, 1000))
    ax_handle.plot_date(x_axis, y_axis, '-')
    ax_handle.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    current_task.update_state(state='PROGRESS', meta={'current':0.8})
    png_output = BytesIO()
    canvas.print_png(png_output)
    out = png_output.getvalue()
    return out
```

Instead of building a response, we return the binary image which will be stored on Redis. We also update the task at various points with a progress indicator that can be queried from the Flask app.

We add a new route to `app.py` that checks the progress and returns the state as a JSON object so that we can write an ajax function that our client can query before loading the final image when it's ready.

```python
@APP.route('/progress')
def progress():
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
```

Extend our `templates/home.html` with the following Javascript code:

```JavaScript
<script src="//code.jquery.com/jquery-2.1.1.min.js"></script>
<script>
function poll() {
    $.ajax("{{url_for('.progress', jobid=JOBID)}}", {
        dataType: "json"
        , success: function(resp) {
            if(resp.progress >= 0.99) {
                $("#imgpl").html('<img src="result.png?jobid={{JOBID}}">');
                return;
            } else {
                setTimeout(poll, 500.0);
            }
        }
    });
}
$(function() {
    var JOBID = "{{ JOBID }}";
    poll();
});
</script>
```

The `poll` function repeatedly requires the `/progress` route of our web app and when it reports that the image has been generated, it replaces the HTML code within the placeholder with the URL of the image, which is then loaded dynamically from our modified `/result.png` route:

```python
@APP.route('/result.png')
def result():
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        png_output = job.get()
        response = make_response(png_output)
        response.headers['Content-Type'] = 'image/png'
        return response
    else:
        return 404
```

At this stage we have a working web app with asynchronous image generation.

## Part 4 - Using Docker to package our application

Our app requires 4 separate containers for each of our servies:
* Flask
* Celery
* RabbitMQ
* Redis

Docker provides prebuilt containers for [RabbitMQ](https://hub.docker.com/_/rabbitmq/) and [Redis](https://hub.docker.com/_/redis/). These both work well and we'll use them as is.

For Flask and Celery, we'll build two identical containers from a simple `Dockerfile`.

```bash
# Pull the latest version of the Python container.
FROM python:latest

# Add the requirements.txt file to the image.
ADD requirements.txt /app/requirements.txt

# Set the working directory to /app/.
WORKDIR /app/

# Install Python dependencies.
RUN pip install -r requirements.txt

# Create an unprivileged user for running our Python code.
RUN adduser --disabled-password --gecos '' app  
```

We pull all of this together with a Docker compose file, `docker-compose.yml`. While early versions of compose needed to expose ports for each service, we can link the services together using the `links` keyword. The `depends` keyword ensures that all of our services start in the correct order.

To create and run the container, use:

    docker-compose build
    docker-compose up

One of the major benefits of Docker is that we can run multiple instances of a container if required. To run multiple instances of our Celery consumers, do:

    docker-compose scale worker=N

where N is the desired number of backend worker nodes.

Visit http://localhost:5000 to view our complete application.
