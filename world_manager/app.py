from typing import Optional

from celery import Celery, Task
from flask import Flask

from world_manager.extensions import db, debug_toolbar, jsglue

from world_manager.blueprints.page.views import page


ACTIVE_EXTENSIONS = [db, debug_toolbar, jsglue]
ACTIVE_BLUEPRINTS = [page]
CELERY_TASK_LIST = []


def create_celery_app(app: Optional[Flask]=None) -> Celery:
    """
    Create a new Celery app and tie the app's config together with celery's.
    Wrap all tasks in the context of the application.

    :param app: The flask app
    :return: celery app
    """

    app = app or create_app()

    class ContextTask(Task):

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(self, *args, **kwargs)

        def run(self, *args, **kwargs):
            """The body of the task executed by workers."""
            raise NotImplementedError('Tasks must define the run method.')

    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'],
                    include=CELERY_TASK_LIST)

    celery.conf.update(app.config)
    # noinspection PyPropertyAccess
    celery.Task = ContextTask

    return celery


def create_app(settings_override: Optional[dict]=None) -> Flask:
    """
    Create a Flask app

    :param settings_override: any settings to override
    :return: flask app
    """

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config.settings')
    app.config.from_pyfile('settings.py', silent=True)

    if settings_override:
        app.config.update(settings_override)
    configure_logging(app)

    initialize_extensions(app)
    db.app = app
    register_blueprints(app)

    load_models()

    return app


def initialize_extensions(app: Flask) -> None:
    """
    Initialize extensions

    :param app: The flask app
    """
    for extension in ACTIVE_EXTENSIONS:
        extension.init_app(app)


def register_blueprints(app: Flask) -> None:
    """
    Register blueprints

    :param app: the flask app
    """
    for blueprint in ACTIVE_BLUEPRINTS:
        app.register_blueprint(blueprint)


def configure_logging(app: Flask) -> None:
    pass


# noinspection PyUnresolvedReferences
def load_models():
    # Ensure that all database models get loaded properly
    import world_manager.model.account
    import world_manager.model.stat
