from flask import Flask
import logging


def create_app(test_config=None):
    app = Flask(__name__)

    if app.debug:
        app.logger.setLevel(logging.DEBUG)

    from tasty.ext.config import init_app as init_config

    init_config(app)

    if test_config:
        app.config.update(test_config)

    from tasty.views import init_app as init_webpage

    init_webpage(app)

    return app
