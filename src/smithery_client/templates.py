TEMPLATES = {}

def create_template(template_name: str, tool_id: str, default_params: dict) -> dict:
    TEMPLATES[template_name] = {"tool_id": tool_id, "params": default_params}
    return TEMPLATES[template_name]

def get_template(template_name: str) -> dict:
    return TEMPLATES.get(template_name, {"error": "Template not found."})

def list_templates() -> list:
    return list(TEMPLATES.keys())