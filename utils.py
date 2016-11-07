attributes = (
    'current_state',
    'problem_has_been_acknowledged',
    'scheduled_downtime_depth',
    'host_name',
    'plugin_output',
    'service_description',
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


def get_services():

    # Open file in context-manager, as there's no garauntee file will be
    # garbage collected in all python implementations inside a list-comp
    with open('test.dat') as f:
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
