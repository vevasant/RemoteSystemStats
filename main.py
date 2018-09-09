#!/usr/bin/env python

import paramiko
import re
import sys
import getpass

class RemoteSystemStats:

    def __init__(self,remote_host,private_key_file,username,password):
        self.remote_host = remote_host
        self.private_key_file = private_key_file
        self.username = username
        self.password = password

    def connect(self):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.private_key_file != "":
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key_file)
                client.connect( hostname = self.remote_host , username = self.username , password = self.password, pkey = private_key )
            else:
                client.connect( hostname = self.remote_host , username = self.username , password = self.password)
            return client
        except Exception as e:
            print("Connection Failed.")
            print(str(e))
            sys.exit(1)

    def run_command(self,client,command):
        try:
            stdin , stdout, stderr = client.exec_command(command)
            stdout.channel.recv_exit_status()
            result = stdout.read().rstrip()
            errors = stderr.read()
            if errors:
                print("Errors: " + errors)
                sys.exit(1)
            return result
        except Exception as e:
            print(str(e))
            sys.exit(1)

    def get_cpu_metrics(self,client):
        cpu_usage = self.run_command(client,"echo $[100-$(vmstat 2 2|tail -1|awk '{print $15}')]%")
        num_of_cpus = self.run_command(client,"nproc --all")
        cpu_usage_detail = cpu_usage + " (CPUs - " + num_of_cpus + ")"
        return cpu_usage_detail

    def get_memory_metrics(self,client):
        mem_detail = self.run_command(client,"vmstat -s -S M | grep memory")
        total_memory = re.search(r'\s*(\d+) M total memory',mem_detail).group(1)
        used_memory = re.search(r'\s*(\d+) M used memory',mem_detail).group(1)
        mem_usage ="{:.2f}%".format((int(used_memory)/float(total_memory))*100)+"("+used_memory+"M/"+total_memory+"M)"
        return mem_usage

    def get_disk_metrics(self,client):
        disk_usage = self.run_command(client,"df -hv | grep '.*\/$' | awk '{print $5,\"(\",$3,\"/\",$2,\")\"}'")
        return disk_usage

    def display_statistics(self,client):
        try:
            print("System Statistics")
            print("--#############--")
            while True:
                cpu_metrics = self.get_cpu_metrics(client)
                memory_metrics = self.get_memory_metrics(client)
                disk_metrics = self.get_disk_metrics(client)
                sys.stdout.write("\rCPU Usage - {} , Memory Usage - {}, Disk Usage - {}".format(cpu_metrics,memory_metrics,disk_metrics))
                sys.stdout.flush()
        except (KeyboardInterrupt, SystemExit):
            print("")
        except Exception as e:
            print(str(e))
            sys.exit(1)

def main():
    hostname = raw_input('Target Hostname : ')
    pkey = raw_input('Private Key Path: ')
    username = raw_input('Login User : ')
    password = getpass.getpass('Password : ')
    rs = RemoteSystemStats(hostname,pkey.rstrip(),username,password)
    client = rs.connect()
    try:
        rs.display_statistics(client)
    except Exception as e:
        print(str(e))
    finally:
        if client:
            client.close()

if __name__ == '__main__':
    main()



