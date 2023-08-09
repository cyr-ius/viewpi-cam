from wtforms.widgets import html_params


class ButtonWidget(object):
    input_type = "submit"

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", self.input_type)
        kwargs.setdefault("name", field.name)
        return f"<button {html_params(**kwargs)}>{field.label.text}</button>"
