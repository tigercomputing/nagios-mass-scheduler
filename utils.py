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

attributes = (
    'current_state',
    'problem_has_been_acknowledged',
    'scheduled_downtime_depth',
    'host_name',
    'plugin_output',
    'service_description',
    'last_check'
)


def parse_attrs(body):
    # Splits line in half at the leftmost '=' symbol
    split_lines = [line.split('=', maxsplit=1) for line in body]
    # Filters out status lines not in attributes tuple
    return filter(lambda l: l[0] in attributes, split_lines)


def is_interesting(service):
    # If the service state is OK, we don't care
    if int(service['current_state']) == 0:
        return False
    # Skip if already acknowledged
    if int(service['problem_has_been_acknowledged']) != 0:
        return False
    # Skip if currently in scheduled downtime
    if int(service['scheduled_downtime_depth']) != 0:
        return False
    return True


def parse_service(position, lines):
    # Parses text between bracket delimiters
    header, *body = lines[slice(*position)]
    if header == 'servicestatus {':
        return {k: v for k, v in parse_attrs(body)}


def get_positions(lines):
    # Loops through entire file recording postions of {} delims
    start_positions, end_positions = [], []
    for lineno, line in enumerate(lines):
        if line.endswith('{'):
            start_positions.append(lineno)
        elif line.startswith('}'):
            end_positions.append(lineno)
    # Zips line numbers into tuple pairs [(start, end), ...)]
    return list(zip(start_positions, end_positions))


def get_services(nagios_file_path):

    # Open file in context-manager, as there's no garauntee file will be
    # garbage collected in all python implementations inside a list-comp
    with open(nagios_file_path) as f:
        # Fetch lines (whitespace removed) from nagios file
        lines = [line.strip() for line in f]

    # Parse each section
    services = [parse_service(s, lines) for s in get_positions(lines)]

    # Remove None values
    services = filter(None, services)

    # Filter by interesting services
    filtered = list(filter(is_interesting, services))

    # Assign each a primary key value
    [s.update({'pk': i}) for i, s in enumerate(filtered)]
    return filtered
