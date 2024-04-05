import json

class DSSSelectorChoices(object):
    def __init__(self):
        self.choices = []

    def append(self, label, value):
        if isinstance(value, dict):
            self.choices.append(
                {
                    "label": label,
                    "value": "{}".format(json.dumps(value))
                }
            )
        else:
            self.choices.append(
                {
                    "label": label,
                    "value": value
                }
            )

    def append_manual_select(self):
        self.choices.append(
            {
                "label": "✍️ Enter manually",
                "value": "dku_manual_select"
            }
        )

    def append_default_manual_select(self):
        self.choices.append(
            {
                "label": "✍️ Enter manually",
                "value": None
            }
        )

    def _build_select_choices(self, choices=None):
        if not choices:
            return {"choices": []}
        if isinstance(choices, str):
            return {"choices": [{"label": "{}".format(choices)}]}
        if isinstance(choices, list):
            return {"choices": choices}
        if isinstance(choices, dict):
            returned_choices = []
            for choice_key in choices:
                returned_choices.append({
                    "label": choice_key,
                    "value": choices.get(choice_key)
                })
            return {"choices": returned_choices}

    def text_message(self, text_message):
        return self._build_select_choices(text_message)

    def to_dss(self):
        return self._build_select_choices(self.choices)