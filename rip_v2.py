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



def domain_check(value, mini, maxi): #Check a number is within the domain
    """
    check if a number is inside a specific range
    """
    if not int(value) >= mini and int(value) <= maxi:
        print("The number", value, "does not reside between", mini, "and", maxi)
        exit(1)
    return int(value) >= mini and int(value) <= maxi
    

def syntax_check(config_data): #Check the config file contain valid data
    """
    checks the router_id is within the range[1-64000],
    and the port number is within range[1024, 64000]
    """
    
    ##CHECK FORMAT CORRECT###############################
    format_check = r"\w+-\w+(,[ ]*[0-9]+(-[0-9]+)*)+[ ]*\Z"
    entries = re.split("\n+", config_data.read())
    local_table = dict()
    
    for line in entries:

        entry = [value.strip() for value in line.split(",")]
        key, values = entry[0], entry[1:]
        local_table[key] = values
        
        if not re.match(format_check, line):

            print("invalid format:\n",line)


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
    for number in local_table["input-ports"]:
        input_ports.append(int(number))
    

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
        

    domain_check(local_table["router-id"][0], 1, 64000)
    global router_id
    router_id = int(local_table["router-id"][0])

    #####################################################

    return 1


def init_table(): #initialize the initial table given by config files
    print(output_ports)
    for item in output_ports.values():
        #print("dsafds", item)
        dest = item[1]
        via = dest
        metric = item[0]
        table[dest] = [via, metric, 0.00, "directly connected"]



def init_router(): #Initialize router, bind to input ports
    for port in input_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((HOST, port))
        listen_list.append(sock)

def show_table(): #Show table on the terminal
    #print("|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|")
    print("{:^49}".format("ROUTER_ID: " + str(router_id)))
    print("\nLoop:", loop)
    
    print("| ID   | via |metric| time  | message            ")
    print(" ------------------------------------------------>")
    for key, value in sorted(table.items()):
        print("|{:^6}|{:^5}|{:^6}|{:^7.3f}|{:^20}".format(key, value[0], value[1], value[2], value[3]))
    print("|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\n")

def update_table(pack): #Unpack packet and load entries to the table
    from_id = struct.unpack("H", pack["id"])[0]
    if from_id in table:
        table[from_id][3] = "regular update"
        table[from_id][2] = 0         
        
    else:
        details = [from_id, pack["metric"], 0, "new neighbor"]
        table[from_id] = details
        #neighbors.append(from_id)
             
        
    for dest, distance in pack["data"].items():
        new_metric = min(distance + table[from_id][1], INFINITY)
        if dest in table:
            if new_metric < INFINITY:   
                metric = table[dest][1]
                if new_metric < metric and dest not in neighbors:
                    table[dest][1] = new_metric
                    table[dest][0] = from_id
                    table[dest][3] = "metric updated"
                    table[dest][2] = 0
                elif table[dest][0] == from_id:
                    table[dest][3] = "regular update"
                    table[dest][1] = new_metric
                    table[dest][2] = 0
                        
            else:
                #if table[dest][0] == from_id:
                if table[dest][0] == from_id:
                    table[dest][2] = max(table[dest][2], TIMEOUT)
                    
                    if table[dest][1] == INFINITY and dest in neighbors:
                        table[dest][2] == GARBAGE
                    else:
                        table[dest][1] == INFINITY
                        trggered(from_id)
        else:
            if new_metric < INFINITY and dest not in neighbors:
                table[dest] = [from_id, new_metric, 0, "newly created"]
            
        
    pass

def refresh_table():  #Refresh the table, keep track of timers of each entry
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
            send_message()
            
    
    for key in to_remove:
        table.pop(key)
        #if key in neighbors:
            #neighbors.remove(key)


def recieve_msg(timeout): 
    #Recieve paccket from other connected routers
    
    def is_valid_pack(packet): #Check if packet recievedis valid
        ## the metric is not greater than 16
        for i in ["ver", "id", "data"]:
            if i not in packet:
                return False
        if packet["ver"] == 2 and len(packet["id"]) == 2\
           and type(packet["data"]) == type(dict()):
            return True
        return False

        
    readable,write,error = select.select(listen_list,[],[], timeout)
    print("received packs:\n")
    for recieved in readable:
        data, addr = recieved.recvfrom(1024)
        pack = pickle.loads(data)
        if is_valid_pack(pack):
            
            print(pack)
            update_table(pack)
    print("=================================")



def create_pack(dest_id, port, version):  #create a packet to send out, split horizon, poison reverse
    pack = {}
    pack["ver"] = 2
    pack["id"] = struct.pack("H", router_id)
    pack["metric"] = output_ports[port][0]
    pack["data"] = {}
    for dest, item in table.items():
        via = item[0]
        metric = item[1]
        if version == 1:
            if via != dest_id and dest != dest_id:
                pack["data"][dest] = item[1]
        elif version == 2:
            if dest != dest_id:
                pack["data"][dest] = item[1]
    return pack

def trggered(send_to):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = 0
    for key, value in output_ports.items():
        print(send_to, value[1])
        if value[1] == send_to:
            
            port = key
            print(port)
    if port == 0:
        print("WRONG PORT!", port,key, output_ports.items())
        exit(1)
    pack = create_pack(send_to, port, 2)
    packet = pickle.dumps(pack, protocol=2)
    sock.sendto(packet, (HOST, port))    

def send_message(): #send packet to neighbors
    
        
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for port in output_ports.keys():
        send_to = output_ports[port][1]
        pack = create_pack(send_to, port, 1)
        packet = pickle.dumps(pack, protocol=2)
        sock.sendto(packet, (HOST, port))

def exchange_info(): #Handling sending and receiving timers, regular update
    def regular_update():
        while 1:
            interval = random.uniform(UPDATE*0.8, UPDATE*0.2)
            time.sleep(interval)
            send_message()
        
    threading.Thread(target = regular_update).start()

    global loop
    while 1:
        loop += 1
        refresh_table()
        show_table()
        recieve_msg(UPDATE)
        
        
        
def main_program(file_name): #Handling the main logistics
    """the main RIPv2 program, logistics"""
    file_object=open(file_name, 'r')
    if not syntax_check(file_object):
        print("Invalid file supplied.")
        exit(1)
    init_table()
    init_router()
    exchange_info()
    
if __name__ == "__main__":
    n_args = (len(sys.argv))
    #print(sys.argv)
    if n_args == 2: main_program(sys.argv[1])
    else: print("Daemon takes exactly one configuration file.") 
