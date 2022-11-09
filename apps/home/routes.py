
from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from run import cur
from flask_login import (
    current_user,
    login_user,
    logout_user
)

@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')

# Format [CLIENT_ID,IP_VPN,NUMBER_OF_CLIENTS,NUMBER_OF_SERVICES]
def servers_template_handler():
    a = current_user.username
    cur.execute("select CLIENT_ID,IP_VPN,count(distinct HOST_ID) connected_devices,count(distinct SERVICIOS_ID) services from (select host.HOST_ID,HOST_IP,CLIENT_ID,IP_VPN,SERVICIOS_ID,PORT,PROTOCOL,USERNAME from host natural join clientes c  left join servicios s on host.HOST_ID = s.HOST_ID "
                f"natural join usuarios u) as t1 where t1.USERNAME='{current_user.username}' group by CLIENT_ID ")
    latest_server_host_data = cur.fetchall()
    return latest_server_host_data
# Format [NAME,HADDRS,DATETIME,STATUS]
def server_alert_template_handler(server):
    cur.execute(f"select * from logs natural join host natural join clientes where TIMESTAMP=(select max(TIMESTAMP) from logs natural join host h natural join clientes c where c.IP_VPN='{server}') and IP_VPN='{server}'"
                f"except select * from logs natural join host natural join clientes where TIMESTAMP=(select TIMESTAMP as timestamp2 from logs natural join host h2 natural join clientes where IP_VPN='{server}' order by TIMESTAMP limit 1 offset 1) and IP_VPN='{server}'")
    latest_server_alert_data = cur.fetchall()

    cur.execute( f"select * from log_servicios natural join servicios natural join clientes where TIMESTAMP=(select max(TIMESTAMP) from log_servicios natural join host h natural join clientes c where c.IP_VPN='{server}') and IP_VPN='{server}'"
        f"except select * from log_servicios natural join servicios natural join clientes where TIMESTAMP=(select TIMESTAMP as timestamp2 from log_servicios natural join host h2 natural join clientes where IP_VPN='{server}' order by TIMESTAMP limit 1 offset 1) and IP_VPN='{server}'")
    added_server_services_alert_data = cur.fetchall()
    cur.execute(f"select * from log_servicios natural join servicios natural join clientes where TIMESTAMP=(select TIMESTAMP as timestamp2 from log_servicios natural join host h2 natural join clientes where IP_VPN='{server}' order by TIMESTAMP limit 1 offset 1) and IP_VPN='{server}'"
                f"except select * from log_servicios natural join servicios natural join clientes where TIMESTAMP=(select max(TIMESTAMP) from log_servicios natural join host h natural join clientes c where c.IP_VPN='{server}') and IP_VPN='{server}'")
    removed_server_services_alert_data = cur.fetchall()


    return latest_server_alert_data,added_server_services_alert_data,removed_server_services_alert_data

# Format [NAME,DATETIME,STATUS,PORT,PROTOCOLOL,ID]
def client_services_template_handler(server,segment):
    cur.execute(f"select * from (select  NOMBRE,TIMESTAMP,STATUS,PORT,PROTOCOL,servicios.SERVICIOS_ID,row_number() over (partition by ls.SERVICIOS_ID order by  TIMESTAMP desc ) number from servicios "
                f"join host h on servicios.HOST_ID = h.HOST_ID join log_servicios ls on servicios.SERVICIOS_ID = ls.SERVICIOS_ID join clientes c on c.CLIENT_ID = h.CLIENT_ID where HOST_IP='{segment}' and IP_VPN='{server}') as t where number=1")
    client_latest_services_data= cur.fetchall()
    cur.execute(f"select  NOMBRE,TIMESTAMP,STATUS,PORT,PROTOCOL,servicios.SERVICIOS_ID from servicios "
        f"join host h on servicios.HOST_ID = h.HOST_ID join log_servicios ls on servicios.SERVICIOS_ID = ls.SERVICIOS_ID join clientes c on c.CLIENT_ID = h.CLIENT_ID where HOST_IP='{segment}' and IP_VPN='{server}'")
    client_all_services_data=cur.fetchall()
    return client_latest_services_data,client_all_services_data


# Format [HOST_IP, NUMBER_OF_LOGS,NUMBER_OF_SERVICES]
def client_template_handler(segment):
    cur.execute(f"select HOST_IP,count(distinct LOG_ID), count(distinct SERVICIOS_ID) from host natural join clientes c natural join logs l  left join servicios on host.HOST_ID = servicios.HOST_ID where IP_VPN='{segment}' group by HOST_IP")
    client_host_data = cur.fetchall()
    cur.execute(f"select HADDRS,TIMESTAMP, STATUS, HOST_IP from host natural join clientes c natural join logs l  left join servicios on host.HOST_ID = servicios.HOST_ID where IP_VPN='{segment}' group by HOST_IP")
    client_log_host_data = cur.fetchall()
    return client_host_data , client_log_host_data


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # If request is for the server tab
        if template=='servers.html':
            server_host_data = servers_template_handler()
            return render_template("home/" + template, segment=segment,server_host_data=server_host_data)


        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)


    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500

@blueprint.route('/servers/<server>')
@login_required
def server_template(server):

   try:

        segment = get_segment(request)
        client_host_data, client_log_host_data = client_template_handler(segment)
        return render_template("home/server.html", segment=segment,client_host_data=client_host_data,client_log_host_data=client_log_host_data)

   except TemplateNotFound:
        return render_template('home/page-404.html'), 404

   except:
        return render_template('home/page-500.html'), 500


@blueprint.route('/servers/<server>/<clientip>')
@login_required
def client_services_template(server,clientip):

   try:
        segment = get_segment(request)
        client_latest_services_data,client_all_services_data = client_services_template_handler(server,segment)
        return render_template("home/client_services.html",server=server, segment=segment, client_latest_services_data = client_latest_services_data, client_all_services_data = client_all_services_data)

   except TemplateNotFound:
        return render_template('home/page-404.html'), 404

   except:
        return render_template('home/page-500.html'), 500



@blueprint.route('/servers/<server>/alerts')
@login_required
def server_alerts_template(server):
    latest_server_alert_data,added_server_services_alert_data, removed_server_services_alert_data = server_alert_template_handler(server)
    return render_template('home/alerts.html',segment=server,latest_server_alert_data=latest_server_alert_data,added_server_services_alert_data=added_server_services_alert_data,removed_server_services_alert_data=removed_server_services_alert_data)

def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None



