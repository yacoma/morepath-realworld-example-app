from more.cerberus.error import ValidationError

from .app import App


@App.json(model=ValidationError)
def validation_error(self, request):
    @request.after
    def set_status(response):
        response.status = 422

    errors = list(self.errors.values())[0][0]

    return {"errors": errors}
