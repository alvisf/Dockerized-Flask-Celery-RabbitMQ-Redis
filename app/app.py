import json
import os

from flask import Flask, request, render_template, abort

from . import tasks

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join("app", "static", "worker-img")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    img = request.files.get("image")
    if not img or img.filename == "":
        return render_template("index.html", error="No file selected"), 400

    path = os.path.join(app.config["UPLOAD_FOLDER"], img.filename)
    img.save(path)
    job = tasks.crop_image.delay(path)
    return render_template("download.html", JOBID=job.id)


@app.route("/progress")
def progress():
    jobid = request.values.get("jobid")
    if not jobid:
        return json.dumps({}), 400

    job = tasks.get_job(jobid)
    if job.state == "PROGRESS":
        return json.dumps({"state": job.state, "progress": job.result["current"]})
    if job.state == "SUCCESS":
        return json.dumps({"state": job.state, "progress": 1.0})
    return json.dumps({"state": job.state, "progress": 0.0})


@app.route("/result.png")
def result():
    jobid = request.values.get("jobid")
    if not jobid:
        abort(404)

    job = tasks.get_job(jobid)
    png_output = job.get()
    return f"../{png_output}"


if __name__ == "__main__":
    app.run(host="0.0.0.0")
