import os

from webob.dec import wsgify
from webob.exc import HTTPNotFound
import morepath

from conduit import App, ProductionApp, TestApp
from conduit.database import db


def setup_db(app):
    db_params = app.settings.database.__dict__.copy()
    db.bind(**db_params)
    db.generate_mapping(create_tables=True)


def wsgi_factory():  # pragma: no cover
    morepath.autoscan()

    if os.getenv("RUN_ENV") == "production":
        ProductionApp.commit()
        app = ProductionApp()
    elif os.getenv("RUN_ENV") == "test":
        TestApp.commit()
        app = TestApp()
    else:
        App.commit()
        app = App()

    setup_db(app)

    @wsgify
    def run_morepath(request):
        popped = request.path_info_pop()
        if popped == "api":
            return request.get_response(app)
        else:
            raise HTTPNotFound

    return run_morepath


application = wsgi_factory()  # pragma: no cover
