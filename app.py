import os
import webbrowser

from threading import Timer

from flask import Flask, render_template, redirect, url_for
from flask_mail import Mail

from config import Config
import db

from auth import auth_bp, login_required, current_user
from profile import profile_bp
from tools_resizer import resizer_bp
from tools_removebg import removebg_bp
from history import history_bp


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    os.makedirs(
        Config.PROFILE_PICS_FOLDER,
        exist_ok=True
    )

    os.makedirs(
        Config.RESIZER_UPLOAD_FOLDER,
        exist_ok=True
    )

    os.makedirs(
        Config.REMOVEBG_UPLOAD_FOLDER,
        exist_ok=True
    )

    db.init_db()

    mail = Mail(app)

    app.extensions["mail"] = mail

    app.register_blueprint(auth_bp)

    app.register_blueprint(profile_bp)

    app.register_blueprint(resizer_bp)

    app.register_blueprint(removebg_bp)

    app.register_blueprint(history_bp)


    @app.route("/")
    def home():

        return redirect(
            url_for("dashboard")
        )


    @app.route("/dashboard")
    @login_required
    def dashboard():

        user = current_user()

        return render_template(
            "dashboard.html",
            user=user
        )


    @app.errorhandler(413)
    def file_too_large(error):

        return render_template(
            "error.html",
            message="File is too large. Maximum size is 20 MB."
        ), 413


    @app.errorhandler(404)
    def not_found(error):

        return render_template(
            "error.html",
            message="Page not found."
        ), 404


    @app.errorhandler(500)
    def server_error(error):

        app.logger.exception("Unhandled server error")

        return render_template(
            "error.html",
            message="Something went wrong on our side. Please try again."
        ), 500


    return app


app = create_app()


if __name__ == "__main__":

    import socket

    def _lan_ip():

        try:

            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            s.connect(
                ("8.8.8.8", 80)
            )

            ip = s.getsockname()[0]

            s.close()

            return ip

        except Exception:

            return None


    lan_ip = _lan_ip()

    # -----------------------------------------------------
    # Base URL for email verification / password reset
    # -----------------------------------------------------

    if Config.APP_BASE_URL:

        base_url = Config.APP_BASE_URL

    elif lan_ip:

        base_url = f"http://{lan_ip}:5000"

    else:

        base_url = "http://127.0.0.1:5000"


    print("\n==============================================")
    print("        Smart Utility Toolkit")
    print("==============================================")

    print(
        "  On this computer:  "
        "http://127.0.0.1:5000"
    )

    if lan_ip:

        print(
            f"  On your network:   "
            f"http://{lan_ip}:5000"
        )

    print(
        f"  Email Base URL:    "
        f"{base_url}"
    )

    print("==============================================")

    print(
        "\nMobile access:"
    )

    if lan_ip:

        print(
            f"  Open this on your phone: "
            f"http://{lan_ip}:5000"
        )

    else:

        print(
            "  LAN IP could not be detected."
        )

    print(
        "\nMake sure your laptop and phone are connected"
        " to the same Wi-Fi network."
    )

    print(
        "\nEmail verification / password reset links will"
        " use the configured Email Base URL."
    )

    print(
        "==============================================\n"
    )


    # -----------------------------------------------------
    # Automatically open application on laptop
    # -----------------------------------------------------

    Timer(
        1,
        lambda: webbrowser.open(
            "http://127.0.0.1:5000"
        )
    ).start()


    # -----------------------------------------------------
    # Start Flask Server
    # -----------------------------------------------------

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )

