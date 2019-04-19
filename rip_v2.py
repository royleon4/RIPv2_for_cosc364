''' 
COSC364 Assignment 1 
Routing Information Protocol
(RIPv2)
'''

import sys
import re
import os


input_ports = []
output_ports = dict()
router_id = 0


def domain_check(value, mini, maxi):
    
    """
    """
    return value >= mini and value <= maxi
    

def syntax_check(config_data):
    """
    checks the router_id is within the range[1-64000],
    and the port number is within range[1024, 64000]
    """
    error = 0
    entry_keys = ["router-id", "input-ports", "output-ports"]
    entries = re.split("\n+", config_data.read())
    format_check = dict()
    format_check["router-id"] = r"\w+-\w+(,[ ]*[0-9]+)[ ]*\Z"
    format_check["input-ports"] = r"\w+-\w+(,[ ]*[0-9]+)+[ ]*\Z"
    format_check["output-ports"] = r"\w+-\w+(,[ ]*[0-9]+-[0-9]+-[0-9]+)+[ ]*\Z"

    for line in entries:
        
        #this can handle white trailing spaces with a correct format and
        #ignore lines with ugly trailing caharacters
        #print("line  ", line)
        entry = [value.strip() for value in line.split(",")]
        key, values = entry[0], entry[1:]

        if re.match(format_check.get(key, ""), line):
            
            if key == entry_keys[0] and domain_check(int(entry[1]), 1, 64000):
                router_id = entry[1]
                
            elif key == entry_keys[1]:
                for number in values:
                    num = int(number)
                    if not domain_check(int(entry[1]), 1024, 64000):
                        print("input port should reside in [1024, 64000].")
                        exit(1)
                    input_ports.append(num)
                    
                    
            elif key == entry_keys[2]:
                for num in values:
                    digits = [int(number) for number in num.split("-")]
                    if not (domain_check(digits[0], 1, 64000) and \
                       domain_check(digits[1], 1, 16) and \
                       domain_check(digits[2], 1, 64000)):
                        print("output port should reside in [1024, 64000]. router id should reside in [1, 64000]")
                        exit(1)
                    output_ports[digits[0]] = [digits[1], digits[2]]
            else:
                
                #print("undesired information given, shown below.\n", line)
                pass
                        
                    
        else:
            print("Error: Invalid format,\nplease use the following format:\n"
                  "router-id, {%d}"
                  "input-ports, {%d}, {%d}, {%d}"
                  "output-ports, {%d}-{%d}-{%d}"
                  "/plus: numbers should all be positive. ")
            error = 1
            

    if router_id == 0:
        print("invalid router_id")
        error = 1
    if len(input_ports) == 0:
        print("no input ports supplied")
        error = 1

    if len(output_ports) == 0:
        print("no output ports supplied")
        error = 1
    for key in output_ports.keys():
        if key in input_ports:
            print("output port should not be the same with input port")
            error = 1

    if error: exit(1)

    return 1




def main_program(file_name):
    """the main RIPv2 program, logistics"""
    file_object=open(file_name, 'r')
    if not syntax_check(file_object):
        print("Invalid file supplied.")
        exit(1)
        


if __name__ == "__main__":
    n_args = (len(sys.argv))
    #print(sys.argv)
    if n_args == 2: main_program(sys.argv[1])
    else: print("Daemon takes exactly one configuration file.") 
