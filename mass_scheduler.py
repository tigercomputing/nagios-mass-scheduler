#!/usr/bin/env python3

import re
import sys
import time

from argparse import ArgumentParser
from collections import ChainMap
from termcolor import colored

# List of attributes to parse => push onto FIFO queue
attributes = [
    'current_state',
    'host_name',
    'plugin_output',
    'problem_has_been_acknowledged',
    'scheduled_downtime_depth',
    'service_description',
]

# Precompile Regular expression to match lines
attributes_regex = re.compile("|".join(attributes))


def parse_args(args):
    parser = ArgumentParser()
    parser.add_argument('-u', '--username')
    parser.add_argument('-m', '--msg')
    parser.add_argument('-r', '--regex')
    return parser.parse_args(args)


def parse_missing_args(args):
    """Attempts to fetch missing arguments by prompting user"""

    while not args.username:
        args.username = get_input('Enter your Username: ')
    while not args.msg:
        args.msg = get_input('Enter message used for acknowledgement:')
    while not args.regex:
        args.regex = get_input('Enter desired search regex:')

    # Pre-Compile the regular expression
    args.regex = re.compile(r'{}'.format(args.regex))
    return args


def get_file(fname, flags):
    """Attempts to open a file on the system"""
    try:
        f = open(fname, flags)
    except (OSError, IOError) as error:
        raise SystemExit(error)
    else:
        return f


def get_input(prompt, choices={}):
    """Provides user with input prompt, quits on escape key-code"""
    try:
        input_string = input(prompt + '\n-> ')
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(colored("\nQuitting!", 'red'))
    else:
        # Retry if input_string is empty
        return input_string or get_input(colored('Retry', 'red'), choices)


def sanitize(text):
    """Removes whitespace and lowercases text"""
    return text.strip().lower()


def is_interesting(service):
    """Should the service be available for acknowledging?"""

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

def prompt_action(service):
    """Prompts the user for input for each pending service"""

    # Display service description and hostname
    service_info = "{service_description} @ {host_name}".format(**service)
    print(colored('Service:', 'yellow'), service_info)

    # Display plugin output
    output_info = "Output: {plugin_output}".format(**service)
    print(colored('Output:', 'cyan'), output_info)

    # Prompt user for [y/n/s]
    choices, colours = ('y', 'n', 's'), ('green', 'red', 'blue')
    text = (colored(t, c) for (t, c) in zip(choices, colours))
    choice = sanitize(get_input('[{}/{}/{}]'.format(*text)))

    # Retry if the choice is invalid
    return choice if choice in choices else prompt_action(service)


def get_date(prompt):
    while True:
        try:
            return int(get_input(prompt))
        except ValueError:
            print(colored('Invalid date', 'red'))


def handle_choice(choice, fifo_queue, service, args):
    now = int(time.time())

    # If the user wishes to Schedule Downtime
    if choice.startswith('s'):
        duration = get_date('Duration [mins from now]')

        dates = {
            'start_time': now,
            'duration': duration * 60,
            'end_time': now + duration * 60,
        }
        data = ChainMap(service, vars(args), dates)

        write_data = "[{start_time}] SCHEDULE_SVC_DOWNTIME;{host_name};" \
            "{service_description};{start_time};{end_time};1;0;{duration};" \
            "{username};{msg}\n"

        fifo_queue.write(write_data.format(**data))

    # If the user wishes to Acknowledge problem
    elif choice.startswith('y'):

        write_data = "[{time}] ACKNOWLEDGE_SVC_PROBLEM;{host_name};" \
            "{service_description};1;0;0;{username};{msg}\n"

        data = ChainMap(service, vars(args), {'time': now})
        fifo_queue.write(write_data.format(**data))


def main():
    status_file = get_file('status.dat', 'r')
    fifo_queue = get_file('outfile.txt', 'w')

    args = parse_missing_args(parse_args(sys.argv[1:]))

    # Store attributes in a dictionary
    service = {}

    # Read in lines into a generator object
    lines = (line.strip() for line in status_file)

    is_service = False

    for line in lines:

        # Skip comments and blank lines
        if line.startswith('#') or line == '':
            continue

        # Reached the start of a 'servicestatus' block
        elif line.startswith('servicestatus') and line.endswith('{'):
            is_service = True

        # Reached the end of a 'servicestatus' block
        elif line.startswith('}'):

            # Acknowledge previously parsed service
            if is_service:

                # Only proceed if current service matches search term
                desc = service.get('service_description', False)

                if is_interesting(service) and args.regex.match(desc):

                    choice = prompt_action(service)
                    handle_choice(choice, fifo_queue, service, args)

            # Delete attributes set from previous service
            service.clear()
            is_service = False

        if is_service:
            match = re.match(attributes_regex, line)
            if match:
                key = match.group()
                service[key] = line.split('=', maxsplit=1)[-1]

    print(colored('Finished!', 'green'))


if __name__ == '__main__':
    main()
