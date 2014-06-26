ERROR_USAGE=1
ERROR_COMMAND_SYNTAX_ERROR=2
ERROR_NO_SUCH_COMMAND=3

ERROR_AGENT_NOT_FOUND=10
ERROR_AGENT_NOT_PRIMARY=11
ERROR_AGENT_NOT_CONNECTED=12
ERROR_AGENT_NOT_SPECIFIED=13

ERROR_BUSY=20
ERROR_WRONG_STATE=21

ERROR_INVALID_PORT=30
ERROR_NOT_FOUND=31

ERROR_SOCKET_DISCONNECTED=40

ERROR_COMMAND_FAILED=50

ERROR_INTERNAL=99

error_strings = {
    ERROR_USAGE: "Invalid usage",
    ERROR_AGENT_NOT_FOUND: "Agent not found",
    ERROR_AGENT_NOT_PRIMARY: "Agent not primary",
    ERROR_BUSY: "Busy with another user request",
    ERROR_AGENT_NOT_SPECIFIED: "No agent specified",
    ERROR_WRONG_STATE: "wrong state for command",
    ERROR_INTERNAL: "Internal error"
}