# run_test.py

from smithery_client.client import SmitheryClient
from smithery_client.workflows import execute_workflow
from smithery_client.templates import create_template, get_template, list_templates

def run():
    client = SmitheryClient()
    
    # Search tools
    tools = client.search_tools("genome")
    print("\nTool Search Result:\n", tools)

    # Get tool details
    tool_info = client.get_tool_details("tool-001")
    print("\nTool Details:\n", tool_info)

    # Execute workflow
    result = execute_workflow("tool-001", {"input_file": "data.fasta", "threshold": 0.95})
    print("\nWorkflow Execution Result:\n", result)

    # Template operations
    create_template("genomic-analysis", "tool-001", {"threshold": 0.8})
    print("\nTemplate Retrieved:\n", get_template("genomic-analysis"))
    print("\nAll Templates:\n", list_templates())

if __name__ == "__main__":
    run()
