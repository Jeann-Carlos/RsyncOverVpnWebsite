
from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from run import cur

@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')

# Format [HOST_ID,HOST_IP,NUMBER_OF_CLIENTS,NUMBER_OF_SERVICES]
def servers_template_handler():
    cur.execute("SELECT HOST_ID,HOST_IP FROM host")
    server_host_data = cur.fetchall()
    for i,host_data in enumerate(server_host_data):
        host_data = list(host_data)
        cur.execute(f"SELECT count(HOST_ID) from host where HOST_ID={host_data[0]}")
        host_data.append(cur.fetchall()[0][0])
        cur.execute(f"SELECT COUNT(SERVICIOS_ID) from servicios where HOST_ID={host_data[0]}")
        host_data.append(cur.fetchall()[0][0])
        server_host_data[i] = host_data
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
        return render_template("home/index.html", segment=segment)

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



