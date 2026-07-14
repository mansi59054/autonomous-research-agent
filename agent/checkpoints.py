# agent/checkpoints.py

def checkpoint_after_tool_call(result):
    if result is None:
        return False, "Tool returned None"
    if isinstance(result, dict) and "error" in result:
        return False, f"Tool call errored: {result['error']}"
    return True, "OK"


def checkpoint_before_final_answer(report, tool_call_count):
    if not report or len(report.strip()) < 100:
        return False, "Report is empty or suspiciously short"
    if tool_call_count == 0:
        return False, "No tools were called, report may be unsupported by real sources"
    return True, "OK"
