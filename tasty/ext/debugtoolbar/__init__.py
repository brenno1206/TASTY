from flask_debugtoolbar import DebugToolbarExtension

toolbar = DebugToolbarExtension()

def init_app(app):
    """Inicializa a extensão Flask-DebugToolbar com o aplicativo Flask."""
    app.logger.info("Inicializando Flask-DebugToolbar...")
    toolbar.init_app(app)