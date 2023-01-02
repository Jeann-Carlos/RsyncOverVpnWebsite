from apps.authentication.util import fetch_to_list
from database_cursor import conn,cur
def servers_template_handler(current_user):
    """
    Retrieves data about the servers and connected devices for the current user.

    Returns:
        A list of lists containing the following information for each server:
            CLIENT_ID: The ID of the client associated with the servers of the current client.
            IP_VPN: The VPN IP address of the servers of the current client.
            connected_devices: The number of connected devices to the servers of the current client.
            services: The number of services running on the servers of the current client.
    """
    cur.execute("select CLIENT_ID,IP_VPN,count(distinct HOST_ID) connected_devices,count(distinct SERVICIOS_ID) services from (select host.HOST_ID,HOST_IP,CLIENT_ID,IP_VPN,SERVICIOS_ID,PORT,PROTOCOL,USERNAME from host natural join clientes c  left join servicios s on host.HOST_ID = s.HOST_ID "
                f"natural join usuarios u) as t1 where t1.USERNAME='{current_user.USERNAME}' group by CLIENT_ID ")
    latest_server_host_data = fetch_to_list(cur.fetchall())
    for server in latest_server_host_data:
        alerts_number = get_server_alert_count(server[1])
        server.insert(4,alerts_number)
    return latest_server_host_data


def get_server_alert_count(server):
    a,b,c = server_alert_template_handler(server)
    return len(a)+len(b)+len(c)


def server_alert_template_handler(server):
    """
     Retrieves data about the latest server alert and any added or removed services for a specific server.

     Args:
         server: The VPN IP address of the server to retrieve data for.

     Returns:
         A list of lists contaiting the following for each entry:

             latest_server_alert_data: The data for the latest server alert. Each list contains the following information:
                 NAME: The name of the server.
                 HADDRS: The hardware address of the server.
                 DATETIME: The timestamp of the server alert.
                 STATUS: The status of the server alert.
                  OST_IP: The IP of the computer that holds of the service.

             added_server_services_alert_data: The data for any services that have been added since the previous server alert. Each list contains the following information:
                 NAME: The name of the service.
                 STATUS: The status of the service.
                 TIMESTAMP: The timestamp of the service.
                 PORT: The port number used by the service.
                 PROTOCOL: The protocol used by the service.
                 IP_VPN: The VPN IP address of the server.
                 HOST_IP: The IP of the computer that holds of the service.

             removed_server_services_alert_data: The data for any services that have been removed since the previous server alert. Each list contains the following information:
                 NAME: The name of the service.
                 STATUS: The status of the service.
                 TIMESTAMP: The timestamp of the service.
                 PORT: The port number used by the service.
                 PROTOCOL: The protocol used by the service.
                 IP_VPN: The VPN IP address of the server.
                 HOST_IP: The IP of the computer that holds of the service.
     """

    cur.execute(f"select  distinct t.HADDRS,(SELECT MAX(TIMESTAMP) FROM logs WHERE ls.HADDRS=t.HADDRS AND t.STATUS=ls.STATUS AND ls.HOST_ID = t.HOST_ID) as TIMESTAMP,t.STATUS,HOST_IP from (select HADDRS,STATUS,HOST_IP ,HOST_ID from logs natural join host natural join clientes where TIMESTAMP=(select max(TIMESTAMP) from logs natural join host h natural join clientes c where c.IP_VPN='{server}') and IP_VPN='{server}'"
                f"except select HADDRS,STATUS,HOST_IP,HOST_ID from logs natural join host natural join clientes where TIMESTAMP=(select distinct TIMESTAMP as timestamp2 from logs natural join host h2 natural join clientes where IP_VPN='{server}' order by TIMESTAMP desc limit 1 offset 1) and IP_VPN='{server}') t JOIN logs ls ON  t.HOST_ID=ls.HOST_ID")
    latest_server_alert_data =  fetch_to_list(cur.fetchall())
    cur.execute(f"select distinct  ls.NOMBRE,ls.STATUS,(SELECT MAX(TIMESTAMP) FROM log_servicios WHERE NOMBRE=ls.NOMBRE AND STATUS=ls.STATUS AND ls.SERVICIOS_ID = t.SERVICIOS_ID)  AS TIMESTAMP,PORT,PROTOCOL,IP_VPN,t.HOST_IP from( select NOMBRE,STATUS,PORT,PROTOCOL,IP_VPN,SERVICIOS_ID,HOST_IP from log_servicios natural join  servicios  natural join host natural join clientes where TIMESTAMP=(select max(TIMESTAMP) from log_servicios naural natural join servicios natural join host h natural join clientes c where c.IP_VPN='{server}') and IP_VPN='{server}' "
       f"except select  NOMBRE,STATUS,PORT,PROTOCOL,IP_VPN,SERVICIOS_ID,HOST_IP from log_servicios natural join servicios  natural join host natural join clientes where TIMESTAMP=(select distinct TIMESTAMP as timestamp2 from log_servicios natural join servicios natural join host h2 natural join clientes where IP_VPN='{server}' order by TIMESTAMP desc limit 1 offset 1) and IP_VPN='{server}') t JOIN log_servicios ls ON t.NOMBRE=ls.NOMBRE AND t.STATUS=ls.STATUS AND t.SERVICIOS_ID=ls.SERVICIOS_ID")
    added_server_services_alert_data =fetch_to_list(cur.fetchall())
    cur.execute(f"select distinct ls.NOMBRE,ls.STATUS,(SELECT MAX(TIMESTAMP) FROM log_servicios WHERE NOMBRE=ls.NOMBRE AND STATUS=ls.STATUS AND ls.SERVICIOS_ID = t.SERVICIOS_ID)  AS TIMESTAMP,PORT,PROTOCOL,IP_VPN,HOST_IP,t.HOST_IP from(  select  NOMBRE,STATUS,PORT,PROTOCOL,IP_VPN,SERVICIOS_ID,HOST_IP from log_servicios natural join servicios  natural join host natural join clientes where TIMESTAMP=(select distinct TIMESTAMP as timestamp2 from log_servicios natural join servicios natural join  host h2 natural join clientes where IP_VPN='{server}' order by TIMESTAMP desc limit 1 offset 1) and IP_VPN='{server}'"
F"except select NOMBRE,STATUS,PORT,PROTOCOL,IP_VPN,SERVICIOS_ID,HOST_IP from log_servicios natural join servicios  natural join host natural join clientes where TIMESTAMP=(select max(TIMESTAMP) from log_servicios naural join servicios natural join host h natural join clientes c where c.IP_VPN='{server}' ) and IP_VPN='{server}' ) t JOIN log_servicios ls ON t.NOMBRE=ls.NOMBRE AND t.STATUS=ls.STATUS AND t.SERVICIOS_ID=ls.SERVICIOS_ID")
    removed_server_services_alert_data = fetch_to_list(cur.fetchall())
    return latest_server_alert_data,added_server_services_alert_data,removed_server_services_alert_data


def client_services_template_handler(server,segment):
    """
        Retrieves data about the services for a specific client on a specific server.

        Args:
            server: The VPN IP address of the server.
            segment: The IP address of the client.

        Returns:
             A list of lists contaiting the following for each entry:
                client_latest_services_data: The data for the latest status of each service for the client. Each list contains the following information:
                    NAME: The name of the service.
                    TIMESTAMP: The timestamp of the service status.
                    STATUS: The status of the service.
                    PORT: The port number used by the service.
                    PROTOCOL: The protocol used by the service.
                    SERVICIOS_ID: The ID of the service.

                client_all_services_data: The data for all the services for the client. Each lists contains the following information:
                    NAME: The name of the service.
                    TIMESTAMP: The timestamp of the service status.
                    STATUS: The status of the service.
                    PORT: The port number used by the service.
                    PROTOCOL: The protocol used by the service.
                    SERVICIOS_ID: The ID of the service.
        """
    cur.execute(f"select * from (select  NOMBRE,TIMESTAMP,STATUS,PORT,PROTOCOL,servicios.SERVICIOS_ID,row_number() over (partition by ls.SERVICIOS_ID order by  TIMESTAMP desc ) number from servicios "
                f"join host h on servicios.HOST_ID = h.HOST_ID join log_servicios ls on servicios.SERVICIOS_ID = ls.SERVICIOS_ID join clientes c on c.CLIENT_ID = h.CLIENT_ID where HOST_IP='{segment}' and IP_VPN='{server}') as t where number=1")
    client_latest_services_data= fetch_to_list(cur.fetchall())
    cur.execute(f"select  NOMBRE,TIMESTAMP,STATUS,PORT,PROTOCOL,servicios.SERVICIOS_ID from servicios "
        f"join host h on servicios.HOST_ID = h.HOST_ID join log_servicios ls on servicios.SERVICIOS_ID = ls.SERVICIOS_ID join clientes c on c.CLIENT_ID = h.CLIENT_ID where HOST_IP='{segment}' and IP_VPN='{server}'")
    client_all_services_data=fetch_to_list(cur.fetchall())
    return client_latest_services_data,client_all_services_data


def client_template_handler(server):
    """
        Retrieves data about the hosts and logs for a specific client on a specific server.

        Args:
            server: The IP address of the server.

        Returns:
            A tuple containing two elements:
                client_host_data: A list of lists containing data about the hosts for the client. Each list contains the following information:
                    HOST_IP: The IP address of the host.
                    NUMBER_OF_LOGS: The number of logs for the host.
                    NUMBER_OF_SERVICES: The number of services for the host.

                client_log_host_data: A list of lists containing data about the logs for the hosts for the client. Each list contains the following information:
                    HADDRS: The hardware address of the host.
                    TIMESTAMP: The timestamp of the log entry.
                    STATUS: The status of the host.
                    HOST_IP: The IP address of the host.
    """
    cur.execute(f"select HOST_IP,count(distinct LOG_ID), count(distinct SERVICIOS_ID) from host natural join clientes c natural join logs l  left join servicios on host.HOST_ID = servicios.HOST_ID where IP_VPN='{server}' group by HOST_IP")
    client_host_data = fetch_to_list(cur.fetchall())
    cur.execute(f"select HADDRS,TIMESTAMP, STATUS, HOST_IP from host natural join clientes c natural join logs l  left join servicios on host.HOST_ID = servicios.HOST_ID where IP_VPN='{server}' group by HOST_IP")
    client_log_host_data = fetch_to_list(cur.fetchall())
    return client_host_data , client_log_host_data
