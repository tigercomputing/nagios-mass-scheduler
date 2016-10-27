#!/usr/bin/env python3

import argparse
import datetime
import os
import re
import sys

from termcolor import colored

# Location of nagios status file
status_file = 'test.dat'

# Size of the terminal window (for pretty printing)
term_size = os.get_terminal_size()

# List of attributes to parse => push onto FIFO queue
attributes = [
    'host_name',
    'service_description',
    'current_state',
    'problem_has_been_acknowledged',
    'plugin_output',
    'scheduled_downtime_depth',
]

# Precompile Regular expression to match lines
attributes_regex = re.compile("|".join(attributes))


# We only care about these keys when Scheduling jobs
key_states = [
    'current_state', 'problem_has_been_acknowledged',
    'scheduled_downtime_depth'
]


def get_file(fname):
    """Attempts to open a file on the system"""
    try:
        f = open(fname, 'r')
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


class MassScheduler():

    def __init__(self):
        self.args = self.parse_args(sys.argv[1:])
        self.user = self.args.user
        self.msg = self.args.msg
        self.search = self.args.search
        self.parse_missing_args()

    def parse_args(self, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('--user')
        parser.add_argument('--msg')
        parser.add_argument('--search')
        return parser.parse_args(args)

    def parse_missing_args(self):
        """Attempts to fetch missing arguments by prompting user"""
        while not self.user:
            self.user = get_input('Enter your Username: ')

        while not self.msg:
            self.msg = get_input('Enter message used for acknowledgement:')

        while not self.search:
            search_msg = get_input('Enter desired search regex:')
            self.search = re.compile(r'{}'.format(search_msg))

    def schedule_downtime(self):
        pass

    def is_unchecked(self):
        """
        Returns True if problem hasn't been acknowledged, no state has been
        set, and no downtime has been scheduled
        """
        return not any(int(self.info_dict.get(key, 1)) for key in key_states)

    def prompt_user_action(self):

        # Display service description and hostname
        service_string = colored('Service: ', 'yellow')
        service_info = "{service_description} @ {host_name}"
        print(service_string, service_info.format(**self.info_dict))

        # Display plugin output
        output_string = colored('Output: ', 'cyan')
        output_info = "Output: {plugin_output}"
        print(output_string, output_info.format(**self.info_dict))

        # Prompt user for [y/n/s]
        colours = [('y', 'green'), ('n', 'red'), ('s', 'blue')]
        choices = (colored(t, c) for (t, c) in colours)
        decision = sanitize(get_input('[{}/{}/{}]'.format(*choices)))

        # If the user wishes to Schedule Downtime
        if decision.startswith('s'):

            start_time = get_input('Start Date: [Default: now]')
            print(start_time or datetime.datetime.now())

            end_time = get_input('End Date: [Default: now + 2h]')
            print(end_time or datetime.datetime.now())

        # If the user wishes to Acknowledge problem
        elif decision.startswith('y'):
            # Write to command FIFO queue
            pass

    def main(self):

        # Store attributes in a dictionary
        self.info_dict = {}

        # Read in lines into a generator object
        lines = (line.strip() for line in get_file(status_file))

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
                    desc = self.info_dict.get('service_description', False)

                    if self.search.match(desc) and self.is_unchecked():

                        self.prompt_user_action()

                # Delete attributes set from previous service
                self.info_dict.clear()
                is_service = False

            if is_service:
                match = re.match(attributes_regex, line)
                if match:
                    key = match.group()
                    self.info_dict[key] = line.split("=", maxsplit=1)[-1]

        print(colored('Finished!', 'green'))


if __name__ == '__main__':
    scheduler = MassScheduler().main()
