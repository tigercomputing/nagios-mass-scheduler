from functools import partial

attributes = (
    'current_state',
    'problem_has_been_acknowledged',
    'scheduled_downtime_depth',
    'host_name',
    'plugin_output',
    'service_description',
)


def parse_attrs(body):
    split_lines = [line.split('=', maxsplit=1) for line in body]
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
    header, *body = lines[slice(*position)]
    if header == 'servicestatus {':
        return {k: v for k, v in parse_attrs(body)}


def get_positions(lines):
    start_positions, end_positions = [], []
    for lineno, line in enumerate(lines):
        if line.endswith('{'):
            start_positions.append(lineno)
        elif line.startswith('}'):
            end_positions.append(lineno)
    return start_positions, end_positions


def get_services():
    lines = [line.strip() for line in open('status.dat')]
    sections = list(zip(*get_positions(lines)))[1:]
    services = []
    for service in map(partial(parse_service, lines=lines), sections):
        if service:
            services.append(service)

    filtered = list(filter(is_interesting, services))
    [s.update({'pk': i}) for i, s in enumerate(filtered)]
    return filtered
