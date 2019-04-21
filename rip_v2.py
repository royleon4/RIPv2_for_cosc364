''' 
COSC364 Assignment 1 
Routing Information Protocol
(RIPv2)
'''

import sys, re, time, random
import threading
import socket, select
import pickle, struct



input_ports = []
output_ports = {}
router_id, loop = 0, 0
table = {}
listen_list = []
neighbors = []


#CONSTANTS
##TIMERS_FOR_RIPv2 = [30, 180, 120]
UPDATE = 30 / 30
TIMEOUT = (180) / 30 + UPDATE
GARBAGE = (120) / 30 + TIMEOUT
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
        neighbors.append(dest)
        
        
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
        table[dest] = [via, metric, 0.00, "directly connected"]

def show_table():
    #print("|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|")
    print("{:^49}".format("ROUTER_ID: " + str(router_id)))
    print("\nLoop:", loop)
    
    print("| ID   | via |metric| time  | message            ")
    print(" ------------------------------------------------>")
    for key, value in sorted(table.items()):
        print("|{:^6}|{:^5}|{:^6}|{:^7.3f}|{:^20}".format(key, value[0], value[1], value[2], value[3]))
    print("|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\n")


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

def trigger_update():
    send_message()
    

def update_table(pack):
    from_id = struct.unpack("H", pack["id"])[0]
    #print(from_id)
    #updating the neighbor first
    if from_id in table:
        table[from_id][3] = "regular update"
        table[from_id][2] = 0         
        
    else:
        details = [from_id, pack["metric"], 0, "new neighbor"]
        table[from_id] = details
        neighbors.append(from_id)
             
        
    for dest, distance in pack["data"].items():
        #print("in update table:", dest)
        #print("table:", table)
        
        #print("dest:", dest)
        #print("tb:", table)
        new_metric = min(distance + table[from_id][1], INFINITY)
        if dest in table:
            if new_metric < INFINITY and dest not in neighbors:   
                metric = table[dest][1]
                if new_metric < metric:
                    table[dest][1] = min(new_metric, INFINITY)
                    table[dest][0] = from_id
                    table[dest][3] = "metric updated"
                    table[dest][2] = 0
                elif table[dest][0] == from_id:
                    table[dest][3] = "regular update"
                    table[dest][2] = 0
                        
            else:
                if table[dest][0] == from_id:
                    table[dest][2] = max(table[dest][2], TIMEOUT)
                    if table[dest][1] != INFINITY:
                        table[dest][1] == INFINITY
                        send_message()
                        time.sleep(0.2)  
        else:
            if new_metric < INFINITY:
                #details = [from_id, new_metric, 0, "newly created"]
                table[dest] = [from_id, new_metric, 0, "newly created"]
            
        
    pass

def refresh_table():
    to_remove = []
    start = time.time()
    time.sleep(random.uniform(0.8, 0.2))
    output_ids = []
       
    for key in table.keys():
        elapsed = time.time() - start 
        table[key][2] += elapsed
        time_recorded = table[key][2]
        if time_recorded >= GARBAGE:
            to_remove.append(key)
        elif time_recorded > UPDATE and time_recorded < TIMEOUT:
            table[key][3] = "Possibly lost"
            
        elif time_recorded >= TIMEOUT:
            table[key][3] = "Invalid"
            table[key][1] = INFINITY
            
    
    for key in to_remove:
        table.pop(key)
        if key in neighbors:
            neighbors.remove(key)
            
        #output_ports.pop(key)
        


def recieve_msg(timeout):
    readable,write,error = select.select(listen_list,[],[], timeout)
    print("received packs:\n")
    for recieved in readable:
        #recieved.settimeout(10)
        data, addr = recieved.recvfrom(1024)
        #print(data)
        pack = pickle.loads(data)
        #print("received:", pack)
        if is_valid_pack(pack):
            
            print(pack)
            update_table(pack)
    print("=================================")
        
        
    pass


def create_pack(dest_id, port):
    pack = {}
    #print("TABLE:", table)
    pack["ver"] = 2
    pack["id"] = struct.pack("H", router_id)
    pack["metric"] = output_ports[port][0]
    #pack["from_id"] = router_id
    #print("dfdgs", struct.unpack("H",  pack["id"]))
    pack["data"] = {}
    for dest, item in table.items():
        via = item[0]
        metric = item[1]
        if (not via == dest_id and dest != dest_id) or\
           metric == INFINITY:
            pack["data"][dest] = item[1]
    return pack



def send_message():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for port in output_ports.keys():
        send_to = output_ports[port][1]
        pack = create_pack(send_to, port)
        packet = pickle.dumps(pack, protocol=2)
        sock.sendto(packet, (HOST, port))

def exchange_info():
    def regular_update():
        while 1:
            interval = random.uniform(UPDATE*0.8, UPDATE*0.2)
            time.sleep(interval)
            send_message()
        
        
    regu_upda = threading.Thread(target = regular_update)
    regu_upda.start()
    
    global loop
    while 1:
        #time.sleep(2)
        loop += 1
        
        refresh_table()
        show_table()
        #
        recieve_msg(UPDATE) #timeout is 5 seconds
        
        
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
