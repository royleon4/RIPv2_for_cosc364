''' 
COSC364 Assignment 1 
Routing Information Protocol
(RIPv2)
'''

import os, sys, re, time, random

import socket, select
import pickle, struct



input_ports = []
output_ports = {}
router_id, loop = 0, 0
table = {}
listen_list = []



#CONSTANTS
##TIMERS_FOR_RIPv2 = [30, 180, 120]
UPDATE = 30 / 6
TIMEOUT = 180 / 6
GARBAGE = (120 + 30) / 6
INFINITY = 16
HOST = "127.0.0.1"


def domain_check(value, mini, maxi):
    
    """
    check if a number is inside a specific range
    """
    if not int(value) >= mini and int(value) <= maxi:
        print("The number", value, "does not reside between", mini, "and", maxi)
        exit(1)
    
    return int(value) >= mini and int(value) <= maxi
    

def syntax_check(config_data):
    """
    checks the router_id is within the range[1-64000],
    and the port number is within range[1024, 64000]
    """
    
    ##CHECK FORMAT CORRECT###############################
    format_check = r"\w+-\w+(,[ ]*[0-9]+(-[0-9]+)*)+[ ]*\Z"
    entries = re.split("\n+", config_data.read())
    local_table = dict()
    
    for line in entries:
        #print(line)
        entry = [value.strip() for value in line.split(",")]
        key, values = entry[0], entry[1:]
        local_table[key] = values
        
        if not re.match(format_check, line):
            #print(line)
            print("invalid format:\n",line)

        #print("passed:", line)
    #####################################################
    ##CHECK REQUIRED iNFO ARE GIVEN######################
    entry_keys = ["router-id", "input-ports", "output-ports"]
    fullfilled = set(entry_keys) - set(local_table.keys())
    if len(fullfilled) != 0:
        print("missing keys:", fullfilled)
        exit(1)
    #####################################################
    
    
    ##CHECK NUMBERS ARE INSIDE THE DOMAIN################
    ##ALSO SAVE INFO IF ALL CORRECT######################
    routes = [list(map(int, item.split("-"))) for item in local_table["output-ports"]] #convert to int
    #input_ports = [int(number) for number in local_table["input-ports"]]
    for number in local_table["input-ports"]:
        input_ports.append(int(number))
    
    
    #print("loca: ", input_ports)
    
    #print("rids=",routes)
    for route in routes:
        oport = route[0]
        metric = route[1]
        dest = route[2]
        
        domain_check(oport, 1024, 64000)
        domain_check(metric, 1, 16)
        domain_check(dest, 1, 64000)
        if oport in input_ports:
            print("Port:", oport, "was specified in input ports!")
            exit(1)
        output_ports[oport] = [metric, dest]
        
        
    #print(local_table["router-id"])
    domain_check(local_table["router-id"][0], 1, 64000)
    global router_id
    router_id = int(local_table["router-id"][0])
    #os.environ["router_id"] = int(local_table["router-id"][0])
    #####################################################
    #print("iport:",input_ports)
    return 1
        
    
    
    
    
    
    #error = 0
    #entry_keys = ["router-id", "input-ports", "output-ports"]
    #
    #format_check = dict()
    #format_check["router-id"] = r"\w+-\w+(,[ ]*[0-9]+)[ ]*\Z"
    #format_check["input-ports"] = r"\w+-\w+(,[ ]*[0-9]+)+[ ]*\Z"
    #format_check["output-ports"] = r"\w+-\w+(,[ ]*[0-9]+-[0-9]+-[0-9]+)+[ ]*\Z"

    #for line in entries:
        
        ##this can handle white trailing spaces with a correct format and
        ##ignore lines with ugly trailing caharacters
        #entry = [value.strip() for value in line.split(",")]
        #key, values = entry[0], entry[1:]

        #if re.match(format_check.get(key, ""), line):

            #if key == entry_keys[0] and domain_check(int(entry[1]), 1, 64000):
                #router_id = entry[1]
                
            #elif key == entry_keys[1]:
                #for number in values:
                    #num = int(number)
                    #if not domain_check(int(entry[1]), 1024, 64000):
                        #print("input port should reside in [1024, 64000].")
                        #exit(1)
                    #input_ports.append(num)
                    
                    
            #elif key == entry_keys[2]:
                #for num in values:
                    #digits = [int(number) for number in num.split("-")]
                    #if not (domain_check(digits[0], 1, 64000) and \
                       #domain_check(digits[1], 1, 16) and \
                       #domain_check(digits[2], 1, 64000)):
                        #print("output port should reside in [1024, 64000]. router id should reside in [1, 64000]")
                        #exit(1)
                    #output_ports[digits[0]] = [digits[1], digits[2]]
            #else:
                
                ##print("undesired information given, shown below.\n", line)
                #pass
                        
                    
        #else:
            #print("Error: Invalid format,\nplease use the following format:\n"
                  #"router-id, {%d}"
                  #"input-ports, {%d}, {%d}, {%d}"
                  #"output-ports, {%d}-{%d}-{%d}"
                  #"/plus: numbers should all be positive. ")
            #error = 1
            

    #if router_id == 0:
        #print("invalid router_id")
        #error = 1
    #if len(input_ports) == 0:
        #print("no input ports supplied")
        #error = 1

    #if len(output_ports) == 0:
        #print("no output ports supplied")
        #error = 1
    #for key in output_ports.keys():
        #if key in input_ports:
            #print("output port should not be the same with input port")
            #error = 1

    #if error: exit(1)

    #return 1


def init_table():
    print(output_ports)
    for item in output_ports.values():
        #print("dsafds", item)
        dest = item[1]
        via = dest
        metric = item[0]
        table[dest] = [via, metric, 0.00, "data loaded"]

def show_table():
    #print("|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|")
    print("ROUTER_ID:", router_id)
    print("\nLoop:", loop)
    
    print("| ID   | via |metric| time  | message            ")
    print(" ------------------------------------------------>")
    for key, value in table.items():
        print("|{:^6}|{:^5}|{:^6}|{:^7.3f}|{:^20}".format(key, value[0], value[1], value[2], value[3]))
    print("|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|")


def init_router():
    #print(input_ports)
    for port in input_ports:
        #print(port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((HOST, port))
        listen_list.append(sock)

def is_valid_pack(packet):
    ## the metric is not greater than 16
    for i in ["ver", "id", "data"]:
        if i not in packet:
            return False
    if packet["ver"] == 2 and len(packet["id"]) == 2\
       and type(packet["data"]) == type(dict()):
        return True
    return False

def update_table(pack):
    from_id = struct.unpack("H", pack["id"])[0]
    #print(from_id)
    for dest, new_metric in pack["data"].items():
        if new_metric <= 16:
            if dest in table:
                metric = table[dest][1]
                #via = table[dest][0]
                table[dest][1] = min(metric, new_metric+table[from_id][1])
                if new_metric > metric:
                    table[dest][0] = from_id
                    table[dest][3] = "metric updated"
                table[dest][3] = "regular update"
                
            else:
                details = [from_id, new_metric + table[from_id][1], 0, "newly created"]
                table[dest] = details
                
            table[dest][2] = 0
    pass

def recieve_msg(timeout):
    readable,write,error = select.select(listen_list,[],[], timeout)
    for recieved in readable:
        #recieved.settimeout(10)
        data, addr = recieved.recvfrom(1024)
        pack = pickle.loads(data)
        #print("received:", pack)
        if is_valid_pack(pack):
            update_table(pack)
        
        
    pass


def create_pack(dest_id):
    pack = {}
    pack["ver"] = 2
    pack["id"] = struct.pack("H", router_id)
    #print("dfdgs", struct.unpack("H",  pack["id"]))
    pack["data"] = {}
    for dest, item in table.items():
        via = item[0]
        metric = item[1]
        if not via == dest_id and dest != dest_id:
            pack["data"][dest] = item[1]
    return pack



def send_message():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for port in output_ports.keys():
        send_to = output_ports[port][1]
        pack = create_pack(send_to)
        packet = pickle.dumps(pack)
        sock.sendto(packet, (HOST, port))

def exchange_info():
    global loop
    while 1:
        start = time.time()
        to_update = random.uniform(UPDATE*0.8, UPDATE*0.2)
        time_passed = time.time() - start
        
        while time_passed < to_update:
            recieve_msg(time_passed)
            time_passed = time.time() - start
        loop += 1
        show_table()
        send_message()    
        
        
def main_program(file_name):
    """the main RIPv2 program, logistics"""
    file_object=open(file_name, 'r')
    if not syntax_check(file_object):
        print("Invalid file supplied.")
        exit(1)
    init_table()

    print(table)
    #print("iport:",input_ports)
    init_router()
    exchange_info()
    


if __name__ == "__main__":
    n_args = (len(sys.argv))
    #print(sys.argv)
    if n_args == 2: main_program(sys.argv[1])
    else: print("Daemon takes exactly one configuration file.") 
