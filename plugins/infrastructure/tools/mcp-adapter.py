#!/usr/bin/env python3
"""
mcp-adapter.py — Generic MCP stdio server wrapping an EDA tool wrapper script.

Implements MCP protocol version 2024-11-05 over stdio (JSON-RPC 2.0, newline-delimited).

Usage:
    python3 mcp-adapter.py --wrapper /path/to/wrap-TOOL.sh --tool TOOL \\
        [--description "Short description"] [--version 1.0.0]

Environment:
    TOOL_TIMEOUT_S   Kill timeout in seconds for the wrapper process (default: 300)

Each tool/call invocation runs the wrapper script with the provided arguments and
returns its compact JSON output as the MCP tool result.  All debug/status output
goes to stderr so it does not corrupt the MCP protocol stream on stdout.
"""

import sys
import json
import subprocess
import argparse
import os
import tempfile

# ---------------------------------------------------------------------------
# MCP protocol helpers
# ---------------------------------------------------------------------------

def _send(msg: dict) -> None:
    """Serialise msg as a single JSON line on stdout and flush."""
    sys.stdout.write(json.dumps(msg, separators=(',', ':')) + '\n')
    sys.stdout.flush()


def _ok(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


# ---------------------------------------------------------------------------
# Per-tool input schema and argument builder
# ---------------------------------------------------------------------------

_EXTRA_PROPERTIES: dict[str, dict] = {
    "yosys": {
        "script": {
            "type": "string",
            "description": "Inline Yosys commands passed via -p (alternative to args)"
        },
        "script_file": {
            "type": "string",
            "description": "Path to a .ys script file"
        },
    },
    "openroad": {
        "tcl_script": {
            "type": "string",
            "description": "Inline Tcl script written to a temp file and passed to OpenROAD"
        },
    },
    "opensta": {
        "tcl_script": {
            "type": "string",
            "description": "Inline Tcl script written to a temp file and passed to OpenSTA"
        },
    },
    "verilator": {
        "mode": {
            "type": "string",
            "enum": ["lint", "sim"],
            "description": "lint: verilator --lint-only; sim: run a pre-compiled sim binary"
        },
        "sim_binary": {
            "type": "string",
            "description": "Path to compiled Verilator simulation binary (required for sim mode)"
        },
    },
    "bambu": {
        "c_file": {
            "type": "string",
            "description": "Path to the C/C++ source file to synthesise"
        },
        "top_function": {
            "type": "string",
            "description": "Name of the top-level function to synthesise"
        },
    },
    "gem5": {
        "config_script": {
            "type": "string",
            "description": "Path to the gem5 Python configuration script"
        },
        "binary": {
            "type": "string",
            "description": "Workload binary to simulate (appended after config_script)"
        },
    },
    "symbiyosys": {
        "sby_file": {
            "type": "string",
            "description": "Path to the SymbiYosys .sby configuration file"
        },
        "task": {
            "type": "string",
            "description": "Optional task name within the .sby file"
        },
    },
}


def _input_schema(tool: str) -> dict:
    props: dict = {
        "args": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Raw CLI arguments passed directly to the wrapper script",
            "default": [],
        }
    }
    props.update(_EXTRA_PROPERTIES.get(tool, {}))
    return {"type": "object", "properties": props}


def _build_cli_args(tool: str, inputs: dict) -> list[str]:
    """
    Map structured tool inputs to the CLI argument list that will be passed
    to the wrapper script.  Falls back to raw args[] if no typed fields match.
    """
    raw: list[str] = inputs.get("args", [])

    if tool == "yosys":
        if "script" in inputs:
            return ["-p", inputs["script"]] + raw
        if "script_file" in inputs:
            return [inputs["script_file"]] + raw

    elif tool in ("openroad", "opensta"):
        if "tcl_script" in inputs:
            tf = tempfile.NamedTemporaryFile(
                mode="w", suffix=".tcl", delete=False, prefix="mcp_tcl_"
            )
            tf.write(inputs["tcl_script"])
            tf.flush()
            tf.close()
            print(f"[mcp-adapter] wrote Tcl script to {tf.name}", file=sys.stderr)
            return [tf.name] + raw

    elif tool == "verilator":
        mode = inputs.get("mode", "sim")
        if mode == "lint":
            return ["--lint-only"] + raw
        sim_bin = inputs.get("sim_binary", "")
        if sim_bin:
            return [sim_bin] + raw

    elif tool == "bambu":
        cli: list[str] = []
        if "top_function" in inputs:
            cli.append("--top-fname=" + inputs["top_function"])
        cli.extend(raw)
        if "c_file" in inputs:
            cli.insert(0, inputs["c_file"])
        return cli

    elif tool == "gem5":
        cli = list(raw)
        if "config_script" in inputs:
            cli.insert(0, inputs["config_script"])
        if "binary" in inputs:
            cli.append(inputs["binary"])
        return cli

    elif tool in ("symbiyosys", "symbiflow"):
        cli = list(raw)
        if "sby_file" in inputs:
            cli.insert(0, inputs["sby_file"])
        if "task" in inputs:
            cli.append(inputs["task"])
        return cli

    return raw


# ---------------------------------------------------------------------------
# Wrapper execution
# ---------------------------------------------------------------------------

def _run_wrapper(wrapper_path: str, tool: str, inputs: dict, timeout: int) -> dict:
    """
    Execute the wrapper script and return its parsed JSON output.
    Always returns a dict conforming to the wrapper JSON schema so the
    caller never has to guard against unexpected shapes.
    """
    cli_args = _build_cli_args(tool, inputs)
    cmd = [wrapper_path] + cli_args
    print(f"[mcp-adapter] running: {' '.join(cmd)}", file=sys.stderr)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = proc.stdout.strip()

        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return {
                    "tool": tool,
                    "exit_code": proc.returncode,
                    "status": "FAIL" if proc.returncode != 0 else "WARN",
                    "summary": {},
                    "errors": ["wrapper output was not valid JSON"],
                    "warnings": [],
                    "raw_output_excerpt": stdout[:500],
                }
        # Empty stdout — surface stderr as the error
        stderr_snippet = proc.stderr.strip()[:500] if proc.stderr else ""
        return {
            "tool": tool,
            "exit_code": proc.returncode,
            "status": "FAIL" if proc.returncode != 0 else "PASS",
            "summary": {},
            "errors": [stderr_snippet] if stderr_snippet else [],
            "warnings": [],
            "raw_log": "",
        }

    except subprocess.TimeoutExpired:
        return {
            "tool": tool,
            "exit_code": -1,
            "status": "FAIL",
            "summary": {},
            "errors": [
                f"process timed out after {timeout}s — raise TOOL_TIMEOUT_S env var to allow longer runs"
            ],
            "warnings": [],
            "raw_log": "",
        }

    except FileNotFoundError:
        return {
            "tool": tool,
            "exit_code": 1,
            "status": "FAIL",
            "summary": {},
            "errors": [f"wrapper script not found: {wrapper_path}"],
            "warnings": [],
            "raw_log": "",
        }


# ---------------------------------------------------------------------------
# Main server loop
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generic MCP stdio adapter for EDA tool wrapper scripts"
    )
    parser.add_argument("--wrapper", required=True, help="Absolute path to the wrapper script")
    parser.add_argument("--tool", required=True, help="Tool name (yosys, openroad, ...)")
    parser.add_argument(
        "--description",
        default="",
        help="One-line description shown in tools/list",
    )
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()

    timeout = int(os.environ.get("TOOL_TIMEOUT_S", "300"))
    tool_name = args.tool
    wrapper_path = args.wrapper
    description = args.description or (
        f"Run {tool_name} via output-filtering wrapper; returns compact JSON summary"
    )

    print(
        f"[mcp-adapter] starting {tool_name} MCP server "
        f"(wrapper={wrapper_path}, timeout={timeout}s)",
        file=sys.stderr,
    )

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        try:
            req = json.loads(raw_line)
        except json.JSONDecodeError:
            print(f"[mcp-adapter] malformed JSON ignored: {raw_line[:100]}", file=sys.stderr)
            continue

        method: str = req.get("method", "")
        req_id = req.get("id")  # None for notifications
        params: dict = req.get("params") or {}

        # Notifications have no id — no response required
        if req_id is None:
            print(f"[mcp-adapter] notification: {method}", file=sys.stderr)
            continue

        print(f"[mcp-adapter] request id={req_id} method={method}", file=sys.stderr)

        if method == "initialize":
            _send(_ok(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": f"{tool_name}-mcp", "version": args.version},
            }))

        elif method == "ping":
            _send(_ok(req_id, {}))

        elif method == "tools/list":
            _send(_ok(req_id, {
                "tools": [{
                    "name": tool_name,
                    "description": description,
                    "inputSchema": _input_schema(tool_name),
                }]
            }))

        elif method == "tools/call":
            call_name: str = params.get("name", "")
            call_inputs: dict = params.get("arguments") or {}

            if call_name != tool_name:
                _send(_err(req_id, -32602, f"Unknown tool '{call_name}'; this server exposes '{tool_name}'"))
                continue

            result = _run_wrapper(wrapper_path, tool_name, call_inputs, timeout)
            _send(_ok(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                "isError": result.get("status") == "FAIL",
            }))

        else:
            _send(_err(req_id, -32601, f"Method not found: {method}"))


if __name__ == "__main__":
    main()
