import logging
import os
import re
import datetime
import mariadb
from database_cursor import conn,cur


'''
  Inserts Host services to log_servicios (depreciated)

          Parameters:
                  cur_host_service_id (int): cur host service id
                  services (list): the list of services belonging to our service id

          Returns:
                  None : if there are no services
'''
def insertHostServiceLogs(cur_host_service_id, services):
    if services is None:
        return None
    for service in services:
        try:
            cur.execute(
                f"insert into log_servicios (status,nombre,SERVICIOS_ID) values ('{service[2]}','{service[3]}','{cur_host_service_id}')")
        except mariadb.IntegrityError:
            print(f'Already added {service} in the log')
        except mariadb.ProgrammingError:
            pass
    conn.commit()


# Removes file that signifies a scan has finished
def removeFinishedScan(cur_host_ip):
    os.remove(f'/home/client_rrsync/results/finished/{cur_host_ip}')

'''
  Gets Host services to information

          Parameters:
                  filecontent (int): contains the data extracted from autorecon unsanitized
                

          Returns:
                  Nothing
  '''
def getHostServicesInfo(filecontent):
    services = []

    service = ["NONE", "NONE", "NONE", "NONE"]
    portstate_patt = re.compile(r"\s(\d+/[a-z].*)")
    if portstate_patt.search(filecontent):
        for port_info in portstate_patt.findall(filecontent):
            try:
                parsing = port_info.split()
                portprotocol = parsing[0]
                service[0] = portprotocol.split('/')[0]
                service[1] = portprotocol.split('/')[1]

                status = parsing[1]
                service[2] = status

                name = parsing[2]
                service[3] = name

            except IndexError:
                pass
            finally:
                services.append(service.copy())
        return services


'''
  Inserts Host services to log_servicios 

          Parameters:
                  cur_host_service_id (int): cur host service id
                  services (list): the list of services belonging to our service id

          Returns:
                  None : if there are no services
'''
def insertHostServices(cur_host_id, services):
    if services is None:
        return None
    for service in services:
        cur.execute(f"select SERVICIOS_ID from servicios where HOST_ID ='{cur_host_id}' and port='{service[0]}'")
        cur_service_id = cur.fetchone()
        if cur_service_id is None:
            try:
                cur.execute(
                    f"insert into servicios (port,protocol,HOST_ID) values ('{service[0]}','{service[1]}','{cur_host_id}')")
                conn.commit()
            except mariadb.DataError:
                continue
        cur.execute(f"select SERVICIOS_ID from servicios where HOST_ID ='{cur_host_id}' and port='{service[0]}'")
        cur_service_id = cur.fetchone()[0]
        try:
            cur.execute(
                f"insert into log_servicios (status,nombre,SERVICIOS_ID) values ('{service[2]}','{service[3]}','{cur_service_id}')")
        except mariadb.IntegrityError:
            continue
    conn.commit()


'''
  Gets the mac address of the current machine

          Parameters:
                  filecontent (int): contains the data extracted from autorecon unsanitized
            

          Returns:
                  None : if there are no mac addresses found
                  mac_patt (String): the found pattern for the macc address
'''
def getMacAddress(filecontent):
    mac_patt = re.compile(r"MAC Address: (?:[a-fA-F0-9]{2}:)+[a-fA-F0-9]{2}")
    if mac_patt.search(filecontent):
        return mac_patt.search(filecontent)[0].split()[2]
    else:
        return None


'''
  Inserts Host logs to logs

          Parameters:
                  cur_host_id (int): cur host id
                  hardware_address (int): H-address of the current machine, None if no H-address

          Returns:
                  Nothing
'''
def insertHostLogs(cur_host_id, hardware_address):
    cur.execute(f"select * from logs where HOST_ID={cur_host_id}")
    if cur.fetchone() == None:
        print(f"Inserting host with Mac Address: {hardware_address}")
        cur.execute(f"insert into logs (HOST_ID,HADDRS,STATUS) values ('{cur_host_id}','{hardware_address}','online')")
        conn.commit()
    else:
        cur.execute(f"select * from logs where HADDRS='{hardware_address}' and HOST_ID={cur_host_id}")
        if cur.fetchone() == None:
            cur.execute(f"select * from logs where HOST_ID={cur_host_id}")
            print("!!!ALERT!!!: A Host has changed")
            print(f"Old Mac Address:{cur.fetchone()[0]} New Mac Address: {hardware_address}")
            print(f"Inserting host with Mac Address: {hardware_address}")
        cur.execute(f"insert into logs (HOST_ID,HADDRS,STATUS) values ('{cur_host_id}','{hardware_address}','online')")
        conn.commit()

'''
  Inserts client ip to clientes

          Parameters:
                  client (int): current client ip address
                  

          Returns:
                  client_id (int): the id generated for the current client
'''
def insertClientIP(client):
    try:
        cur.execute(f"insert into clientes (IP_VPN) values ('{client}')")
        conn.commit()
    except mariadb.IntegrityError:
        print(f'Already added {client} as a client ip skipping insertion...')
    finally:
        cur.execute(f"select CLIENT_ID from clientes where IP_VPN ='{client}'")
        for CLIENT_ID in cur:
            client_id = CLIENT_ID[0]
        return client_id


'''
  Creates the relation betewen client and host

          Parameters:
                 cur_host_ip (int): contains current host ip address
                 cur_client_id (int): contains current client id
                cur_client_ip (int): contains current client ip address


          Returns:
                  host_id (int): the id generated from the relation
'''
def insertHostIP(cur_host_ip, cur_client_id, cur_client_ip):
    try:
        cur.execute(f"insert into host (HOST_IP,CLIENT_ID) values ('{cur_host_ip}','{cur_client_id}')")
        conn.commit()
    except mariadb.IntegrityError:
        print(f'This host: {cur_host_ip} already has a relation with client: {cur_client_ip}. Skipping insertion.')
    finally:
        cur.execute(f"select HOST_ID from host where HOST_IP='{cur_host_ip}' and CLIENT_ID='{cur_client_id}'")
        for HOST_ID in cur:
            host_id = HOST_ID[0]
        return host_id


def process_directory(directory):
    # Process all the files in the given directory
    for cur_client_ip in os.listdir(directory):
        client_path = os.path.join(directory, cur_client_ip)
        if os.path.isdir(client_path):
            for cur_host_ip in os.listdir(os.path.join(client_path, 'results')):
                host_path = os.path.join(client_path, 'results', cur_host_ip)
                if os.path.isdir(host_path):
                    scan_path = os.path.join(host_path, 'scans', '_full_tcp_nmap.txt')
                    if os.path.exists(scan_path):
                        with open(scan_path, 'r') as f:
                            file_content = f.read()
                            cur_client_id = insertClientIP(cur_client_ip)
                            cur_host_id = insertHostIP(cur_host_ip, cur_client_id, cur_client_ip)
                            services = getHostServicesInfo(file_content)
                            cur_host_service_id = insertHostServices(cur_host_id, services)
                            hardware_address = getMacAddress(file_content)
                            insertHostLogs(cur_host_id, hardware_address)
                    else:
                        logging.warning(f"Scan file not found at {scan_path}")
                else:
                    logging.warning(f"Invalid host directory: {host_path}")
        else:
            logging.warning(f"Invalid client directory: {client_path}")

def main():
    logging.basicConfig(level=logging.INFO)
    finished_directory = '/home/client_rrsync/results/finished/'
    if not os.listdir(finished_directory):
        logging.info("Nothing to insert")
        return 0
    logging.info(f"Starting insertion at {datetime.datetime.now()}")
    process_directory(finished_directory)
    for cur_client_ip in os.listdir(finished_directory):
        pass
        #removeFinishedScan(cur_client_ip)




# def main():
#     hosts = os.listdir("/home/client_rrsync/results/finished/")
#     print(f"Starting insertion at {datetime.datetime.now()}")
#     if not hosts:
#         print('Nothing to insert')
#         return 0
#     for cur_client_ip in hosts:
#         try:
#             for cur_host_ip in os.listdir('/home/client_rrsync/results/' + cur_client_ip + '/results/'):
#                 try:
#                     current_file = open(
#                         '/home/client_rrsync/results/' + cur_client_ip + '/results/' + cur_host_ip + '/scans/_full_tcp_nmap.txt')
#                     filecontent = current_file.read()
#                     cur_client_id = insertClientIP(cur_client_ip)
#                     cur_host_id = insertHostIP(cur_host_ip, cur_client_id, cur_client_ip)
#                     services = getHostServicesInfo(filecontent)
#                     cur_host_service_id = insertHostServices(cur_host_id, services)
#                     hardware_address = getMacAddress(filecontent)
#                     insertHostLogs(cur_host_id, hardware_address)
#                     current_file.close()
#                 except FileNotFoundError as err:
#                     print(f"current directory: {cur_host_ip} doesn't have the scan folder...skipping.")
#                     current_file.close()
#                     pass
#         except FileNotFoundError as err:
#             print(f"Current folder: {cur_client_ip} doesn't have a valid directory ignoring...")
#             current_file.close()
#             pass
#         removeFinishedScan(cur_client_ip)



