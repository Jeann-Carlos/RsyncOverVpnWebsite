
from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from run import cur

@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')

# Format [CLIENT_ID,IP_VPN,NUMBER_OF_CLIENTS,NUMBER_OF_SERVICES]
def servers_template_handler():
    cur.execute("select CLIENT_ID,IP_VPN,count(distinct HOST_ID) connected_devices,count(distinct SERVICIOS_ID) services from (select host.HOST_ID,HOST_IP,CLIENT_ID,IP_VPN,SERVICIOS_ID,PORT,PROTOCOL from host natural join clientes c  left join servicios s on host.HOST_ID = s.HOST_ID) as t1 group by CLIENT_ID")
    server_host_data = cur.fetchall()
    return server_host_data


# Format [NAME,DATETIME,STATUS,PORT,PROTOCOLOL,ID]
def client_services_template_handler(segment):
    cur.execute(f"select  NOMBRE,TIMESTAMP,STATUS,PORT, PROTOCOL,servicios.SERVICIOS_ID from servicios join host h on servicios.HOST_ID "
                f"= h.HOST_ID join log_servicios ls on servicios.SERVICIOS_ID = ls.SERVICIOS_ID join clientes c on c.CLIENT_ID = h.CLIENT_ID where HOST_IP='192.0.0.1' and IP_VPN='10.0.0.1' group by ls.SERVICIOS_ID")
    client_services_data= cur.fetchall()
    return client_services_data


# Format [HOST_IP, NUMBER_OF_LOGS,NUMBER_OF_SERVICES]
def client_template_handler(segment):
    cur.execute(f"select HOST_IP,count(distinct LOG_ID), count(SERVICIOS_ID) from host natural join clientes c natural join logs l  left join servicios on host.HOST_ID = servicios.HOST_ID where IP_VPN='{segment}' group by HOST_IP")
    server_host_data = cur.fetchall()
    return server_host_data


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
        client_host_data = client_template_handler(segment)
        return render_template("home/server.html", segment=segment,client_host_data=client_host_data)

   except TemplateNotFound:
        return render_template('home/page-404.html'), 404

   except:
        return render_template('home/page-500.html'), 500


@blueprint.route('/servers/<server>/<clientip>')
@login_required
def client_services_template(server,clientip):

   try:
        segment = get_segment(request)
        client_services_data = client_services_template_handler(segment)
        return render_template("home/client_services.html",server=server, segment=segment, client_services_data= client_services_data)

   except TemplateNotFound:
        return render_template('home/page-404.html'), 404

   except:
        return render_template('home/page-500.html'), 500

# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None



