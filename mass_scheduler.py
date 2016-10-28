#!/usr/bin/env python3

import os
import re
import sys

from argparse import ArgumentParser
from collections import ChainMap
from termcolor import colored
from inspect import getsource

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
    parser = ArgumentParser()
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
        raise SystemExit(error)
    else:
        return f


def get_input(prompt, choices=[], coerces_to=None, constraintfn=None):
    """Provides user with input prompt, quits on escape key-code"""
    try:
        input_string = input(prompt + '\n-> ')
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(colored("\nQuitting!", 'red'))
    else:
        # Check if input matches specified choices
        if choices and input_string not in choices:
            print(colored('Invalid choice!', 'red'))
            get_input(prompt, choices)
        # If coerce target specified, attempt to coerce value to that type
        if coerces_to:
            try:
                input_string = coerces_to(input_string)
            except (TypeError, ValueError):
                print(colored('Invalid type!', 'red'))
                get_input(prompt, choices)
        if constraintfn:
            if not constraintfn(input_string):
                funcbody = getsource(constraintfn).split(':', maxsplit=1)[-1]
                constraint_msg = 'Failed to meet constraint: {}'
                print(colored(constraint_msg.format(funcbody.strip()), 'red'))
                get_input(prompt, choices)
        return input_string


def sanitize(text):
    """Removes whitespace and lowercases text"""
    return text.strip().lower()


def is_unchecked(service):
    """Returns True if all `key_states` in service dictionary are set to 0 """
    return not any(int(service.get(key, 1)) for key in key_states)


def prompt_action(service):
    """Prompts the user for input for each pending service"""

    # Clear the screen
    os.system('clear')

    # Display service description and hostname
    service_info = "{service_description} @ {host_name}".format(**service)
    print(colored('Service:', 'yellow'), service_info)

    # Display plugin output
    output_info = "Output: {plugin_output}".format(**service)
    print(colored('Output:', 'cyan'), output_info)

    # Prompt user for [y/n/s]
    colours = [('y', 'green'), ('n', 'red'), ('s', 'blue')]
    choices = (colored(text, colour) for (text, colour) in colours)
    return sanitize(get_input('[{}/{}/{}]'.format(*choices), ['y', 'n', 's']))


def handle_choice(choice, fifo_queue, service, args):
    # [TODO] Fix indentation

    # If the user wishes to Schedule Downtime
    if choice.startswith('s'):

        start_time = get_input('Start Time: [mins from now]', coerces_to=int)

        end_time = get_input(
            'End Time: [mins from now]',
            coerces_to=int,
            constraintfn=lambda end_time: end_time > start_time
        )

        dates = {'start_time': start_time*60, 'end_time': end_time*60}
        data = ChainMap(service, vars(args), dates)

        write_data = """
        Schedule Service Downtime {host_name} {service_description}
        {start_time} {end_time} {username} {msg}
        """

        fifo_queue.write(write_data.format(**data))

    # If the user wishes to Acknowledge problem

    elif choice.startswith('y'):
        data = ChainMap(service, vars(args))
        write_data = """
        Acknowledge service problem {host_name} {service_description}
        {username} {msg}
        """
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

                # Only proceed is current service matches search term
                desc = service.get('service_description', False)

                if args.regex.match(desc) and is_unchecked(service):

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
