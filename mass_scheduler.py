#!/usr/bin/env python3

import argparse
import datetime
import re
import sys

from termcolor import colored

# List of attributes to parse => push onto FIFO queue
attributes = [
    'host_name',
    'service_description',
    'current_state',
    'problem_has_been_acknowledged',
    'plugin_output',
    'scheduled_downtime_depth',
]

# We only care about these keys when Scheduling jobs
key_states = [
    'current_state', 'problem_has_been_acknowledged',
    'scheduled_downtime_depth'
]

# Precompile Regular expression to match lines
attributes_regex = re.compile("|".join(attributes))


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--username')
    parser.add_argument('--msg')
    parser.add_argument('--regex')
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
        print("Error opening file: ", error)
        sys.exit(1)
    else:
        return f


def get_input(msg):
    """Provides user with input prompt, quits on escape key-code"""
    try:
        input_string = input(msg + '\n-> ')
    except (EOFError, KeyboardInterrupt):
        sys.exit(colored("\nQuitting!", 'red'))
    else:
        return input_string


def sanitize(text):
    """Removes whitespace and lowercases text"""
    return text.strip().lower()


def is_unchecked(service):
    """Returns True if all `key_states` in service dictionary are set to 0 """
    return not any(int(service.get(key, 1)) for key in key_states)


def prompt_action(service):
    """Prompts the user for input for each pending service"""

    # Display service description and hostname
    service_info = "{service_description} @ {host_name}".format(**service)
    print(colored('Service:', 'yellow'), service_info)

    # Display plugin output
    output_info = "Output: {plugin_output}".format(**service)
    print(colored('Output:', 'cyan'), output_info)

    # Prompt user for [y/n/s]
    colours = [('y', 'green'), ('n', 'red'), ('s', 'blue')]
    choices = (colored(t, c) for (t, c) in colours)
    return sanitize(get_input('[{}/{}/{}]'.format(*choices)))


def handle_choice(choice, fifo_queue, args):

    # If the user wishes to Schedule Downtime
    if choice.startswith('s'):

        time_now = str(datetime.datetime.now())
        start_time = get_input('Start Date: [Default: now]') or time_now
        end_time = get_input('End Date: [Default: now + 2h]') or time_now

        write_data = ' '.join([start_time, end_time, '\n'])
        fifo_queue.write(write_data)

    # If the user wishes to Acknowledge problem
    elif choice.startswith('y'):
        write_data = ' '.join(["thing", "acknowledged", "boiii\n"])
        fifo_queue.write(write_data)


def main():
    args = parse_missing_args(parse_args(sys.argv[1:]))

    status_file = get_file('status.dat', 'r')
    fifo_queue = get_file('outfile.txt', 'w')

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

                # Only proceed is current service matches search term
                desc = service.get('service_description', False)

                if args.regex.match(desc) and is_unchecked(service):

                    choice = prompt_action(service)
                    handle_choice(choice, fifo_queue, args)

            # Delete attributes set from previous service
            service.clear()
            is_service = False

        if is_service:
            match = re.match(attributes_regex, line)
            if match:
                key = match.group()
                service[key] = line.split("=", maxsplit=1)[-1]

    print(colored('Finished!', 'green'))


if __name__ == '__main__':
    main()
