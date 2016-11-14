#!/usr/bin/env python3

"""
This file is part of mass-scheduler.

mass-scheduler is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

mass-scheduler is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
mass-scheduler.  If not, see <http://www.gnu.org/licenses/>.

Copyright {c} 2016 Tiger Computing Ltd
"""

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash
)

from collections import ChainMap
from time import time
from utils import get_services
from datetime import datetime

import socket

application = Flask(__name__)

# Poor mans check to prevent Debug in production
if socket.gethostname() == 'rutland':
    application.debug = True

# set the secret key.  keep this really secret:
application.secret_key = '\xf9\x00\x9c\x15Q\x8a0\xc5\xbc\xa0@\x8f\xe8ky=\x92\xec\x01'


downtime_string = "[{start_time}] SCHEDULE_SVC_DOWNTIME;{host_name};"\
    "{service_description};{start_time};{end_time};1;0;"\
    "{duration};{username};{message}\n"


acknowledge_string = "[{time}] ACKNOWLEDGE_SVC_PROBLEM;{host_name};" \
    "{service_description};1;0;0;{username};{message}\n"


@application.route('/', methods=['POST', 'GET'])
def index():

    if request.method == 'POST':
        form = request.form

        service_ids = [int(v) for k, v in form.items() if k[:7] == ('service')]
        services = [session['services'][i] for i in service_ids]

        now = int(time())
        fifo_queue = open('outfile.txt', 'a')

        # Parse duration from the form
        duration = form.get('duration', None)

        # If duration has been specified
        if duration:

            time_format = '%d-%m-%Y %H:%M'
            end_time = datetime.strptime(form['duration'], time_format)
            end_time_timestamp = int(end_time.timestamp())

            dates = {
                'start_time': now,
                'duration': end_time_timestamp - now,
                'end_time': end_time_timestamp,
            }

            for service in services:
                data = ChainMap(service, form, dates)
                fifo_queue.write(downtime_string.format(**data))

        else:
            for service in services:
                data = ChainMap(service, {'time': now}, form)
                fifo_queue.write(acknowledge_string.format(**data))

        flash('Request processed!')
        return redirect(url_for('index'))

    # Fetch the nagios services and store in session
    services = get_services()
    session['services'] = services

    return render_template('index.html', services=services)

if __name__ == '__main__':
    application.run()
