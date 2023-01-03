import threading
from flask import render_template, url_for, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from werkzeug.utils import redirect
from flask_login import current_user
import serverprocess
from apps.home import blueprint
from apps.home.queries import servers_template_handler, client_template_handler, client_services_template_handler, \
    server_alert_template_handler


@blueprint.route('/servers')
@login_required
def index():
    """
    Displays the servers page for the logged-in user. Also reloads server scans if needed

    Returns:
        A rendered template for the servers page.
    """

    def serverprocess_thread():
        serverprocess.main()

    # To reload server scans
    thread = threading.Thread(target=serverprocess_thread)
    thread.start()

    # Display server data
    server_host_data = servers_template_handler(current_user)
    segment = get_segment(request)
    return render_template("home/servers.html", segment=segment, server_host_data=server_host_data)


@blueprint.route('login.html')
def login_redirection():
    """
    Redirects the user to the login page.

    Returns:
        A redirect to the login page.
    """
    return redirect(url_for('authentication_blueprint.login'))


@blueprint.route('register.html')
def register_redirection():
    """
    Redirects the user to the registration page.

    Returns:
        A redirect to the registration page.
    """
    return redirect(url_for('authentication_blueprint.register'))


@blueprint.route('/servers/<server>')
@login_required
def server_template(server):
    """
    Displays the server page for the logged-in user.

    Args:
        server: The VPN IP address of the server.

    Returns:
        A rendered template for the server page.
    """
    try:
        segment = get_segment(request)
        client_host_data, client_log_host_data = client_template_handler(segment)
        return render_template("home/server.html", segment=segment, client_host_data=client_host_data,
                               client_log_host_data=client_log_host_data)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


@blueprint.route('/servers/<server>/<clientip>')
@login_required
def client_services_template(server, clientip):
    """
    Displays the client services page for the logged-in user.

    Args:
        server: The VPN IP address of the server.
        clientip: The IP address of the client.

    Returns:
        A rendered template for the client services page.
    """
    try:
        segment = get_segment(request)
        client_latest_services_data, client_all_services_data = client_services_template_handler(server, segment)
        return render_template("home/client_services.html", server=server, segment=segment,
                               client_latest_services_data=client_latest_services_data,
                               client_all_services_data=client_all_services_data)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


@blueprint.route('/servers/<server>/alerts')
@login_required
def server_alerts_template(server):
    """
    Displays the alerts page for the logged-in user.

    Args:
        server: The VPN IP address of the server.

    Returns:
        A rendered template for the alerts page.
    """

    latest_server_alert_data, added_server_services_alert_data, removed_server_services_alert_data = server_alert_template_handler(server)
    return render_template('home/alerts.html', segment=server, latest_server_alert_data=latest_server_alert_data,
                           added_server_services_alert_data=added_server_services_alert_data,
                           removed_server_services_alert_data=removed_server_services_alert_data)


def get_segment(request):
    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'servers'

        return segment

    except:
        return None
