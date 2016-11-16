# Nagios Mass-Scheduler

## Introduction

`nagios-mass-scheduler` is a small Python Flask application to make
scheduling or acknowledging of multiple services easier. It can accept
an author, comment and optional downtime (expressed as a target time,
not a number of seconds).

## Installation

1. Copy the source to somewhere convenient, for example `/srv/mass-scheduler`
1. Install the Python dependencies listed in `requirements.txt`
1. Use `npm` to install JavaScript dependencies: `cd static && npm install`
1. Adjust the file locations for `outfile.txt` in `app.py` and `test.dat` in `utils.py`

### Connecting the web server

An excercise for the reader. For Apache, `mod_wsgi3` is recommended
with the following example configuration:

```
WSGIDaemonProcess mass-scheduler python-path=/srv/mass-scheduler user=www-data group=www-data threads=5
WSGIScriptAlias /mass-scheduler /srv/mass-scheduler/wsgi.py
WSGIScriptReloading On
<Directory /srv/mass-scheduler>
    WSGIProcessGroup mass-scheduler
    WSGIApplicationGroup %{GLOBAL}
    AllowOverride none
</Directory>
```

### Permissions

Whichever user runs `nagios-mass-scheduler` will need to be able to read
the status file and write to the command file.
