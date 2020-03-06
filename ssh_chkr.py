#!/usr/bin/python3

"""Script which used to check SSH-host connections from a text file"""
import paramiko
import sys
import geoip2.database
import argparse
from timeit import default_timer as timer


def main():
    parser = cmd_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    input_f = namespace.input_file
    output_f = namespace.output_file
    input_list = InputList()
    output_list = OutputList()
    host = Host()
    io = InputOutput(input_f, output_f, input_list, output_list)
    input_list.handling_list(output_list, host, io)
    print(f'Filtered: {input_list.bad_host_count} bad hosts. \
        Passed the test: {output_list.count_of_good_hosts} hosts')


def cmd_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', default='ssh_nocheck.txt')
    parser.add_argument('-o', '--output_file', default='goods.txt')
    return parser


class InputList:
    def __init__(self):
        self.host_count = 0
        self.bad_host_count = 0
        self.current_line_count = 0

    def hosts_counter(self, io):
        print(f'Counting host in file: {io.input_file}')
        for line in io.read_data_from_file(flag='r'):
            self.host_count += 1
        return self.host_count

    def handling_list(self, output_list, host, io):
        print(f'Found {self.hosts_counter(io)} hosts in list of file {io.input_file}')
        for line in io.read_data_from_file(flag='r'):
            self.current_line_count += 1
            print(f'handling line# {self.current_line_count}')
            check_result = host.check_host_data(line)
            if check_result:
                host.extract_host_data_from_line(line)
                connection = host.connect_to_host()
                if connection:
                    prepare_data = output_list.prepare_data_to_write(line, host)
                    write_line = io.write_data_to_file(prepare_data, output_list, flag='a')
                    if write_line:
                        print(f'recorded line# {output_list.count_of_good_hosts} of {self.host_count}')
                else:
                    self.bad_host_count += 1
            else:
                self.bad_host_count += 1

    """def prepare_data_to_write(self, line, host):
        joined = ' '.join(line) + ' '
        location = str(host.get_location(host.ip)) + ' '
        accesstime = str(host.host_access_time)
        new_line = joined + location + accesstime + '\n'
        return new_line"""


class OutputList:
    def __init__(self):
        self.count_of_good_hosts = 0

    def write_data(self, io, data):
        io.write_data_to_file(data, flag='a')

    def prepare_data_to_write(self, line, host):
        joined = ' '.join(line) + ' '
        location = str(host.get_location(host.ip)) + ' '
        accesstime = str(host.host_access_time)
        new_line = joined + location + accesstime + '\n'
        return new_line


class Host:
    def __init__(self):
        self.user = None
        self.password = None
        self.ip = None
        self.port = None
        self.location = None
        self.start_time = timer()
        self.host_access_time = 0

    def check_host_data(self, line):
        print(f'Checking data of host {line[2]}')
        if len(line) == 4:
            return True
        else:
            print('no valid data in line')
            return False

    def check_host(self, line):
        if self.extract_host_data_from_line(line):
            print(f'Trying to connect to {self.ip}')
            self.connect_to_host()
            return True
        else:
            return False

    def extract_host_data_from_line(self, data):
        self.user = data[0]
        self.password = data[1]
        self.ip = data[2]
        self.port = data[3]
        return True

    def connect_to_host(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=self.ip, username=self.user, password=self.password, port=self.port, timeout=3)
            print(f'Connected to host {self.ip}\
                    Access time to host: {self.access_time()} seconds')
            return True
        except paramiko.AuthenticationException:
            print(f'Authentication failed when connecting to {self.ip}')
            print('Host marked as bad')
            return False
        except ConnectionError:
            print(f'Could not connect to {self.ip}')
            return False

    def access_time(self):
        self.host_access_time = timer() - self.start_time
        return round(self.host_access_time, 2)

    def get_location(self, ip):
        reader = geoip2.database.Reader('GeoLite2-Country.mmdb')
        response = reader.country(ip)
        return response.country.names['en']

class InputOutput:
    def __init__(self, input_f, output_f, input_list, output_list):
        self.output_file = output_f
        self.input_file = input_f
        self.output_list = output_list
        self.input_list = input_list

    def read_data_from_file(self, flag):
        try:
            with open(self.input_file, flag) as file:
                for line in file:
                    yield line.strip().split(' ')
        except IOError:
            print('can\'t read from file, IO error')
            exit(1)

    def write_data_to_file(self, line, output_list, flag):
        try:
            with open(self.output_file, flag) as file:
                file.write(line)
                output_list.count_of_good_hosts += 1
            return True
        except IOError:
            print('Can\'t write to output file, IO error')
            exit(1)

if __name__ == "__main__":
    main()
