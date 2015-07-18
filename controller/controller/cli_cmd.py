import time
import json
import httplib

from sqlalchemy import Column, String, BigInteger, DateTime, func

import akiri.framework.sqlalchemy as meta

from event_control import EventControl
from util import safecmd

class XIDEntry(meta.Base):
    #pylint: disable=no-init
    __tablename__ = 'xid'

    xid = Column(BigInteger, unique=True, nullable=False, \
                 autoincrement=True, primary_key=True)
    # FIXME: Enumerate valid state values.
    state = Column(String, default='started')
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
                               server_onupdate=func.current_timestamp())

class Request(object):
    """Represents a request.
       Creates a body and adds:
        command: <command>
        xid: <xid>
        body: <body>
    """

    def __init__(self, action, send_body_dict=None, xid=None):
        self.action = action

        session = meta.Session()
        entry = None
        if xid:
            entry = session.query(XIDEntry).\
                filter(XIDEntry.xid == xid).\
                one()
        else:
            entry = XIDEntry()
            session.add(entry)
            session.commit()
        self.xid = entry.xid

        if send_body_dict is None:
            send_body_dict = {}
        send_body_dict["action"] = action
        send_body_dict["xid"] = self.xid
        self.send_body = json.dumps(send_body_dict)

        if send_body_dict["action"] == 'cleanup':
            entry.state = "finished"
            session.commit()

    def __repr__(self):
        return "<action: %s, body_dict: %s, xid: %d>" % \
            (self.action, self.send_body, self.xid)

class CliStartRequest(Request):
    def __init__(self, cli_command, env=None, immediate=False):
        d = {"cli": cli_command}
        if env:
            d["env"] = env
        if immediate:
            d["immediate"] = immediate
        super(CliStartRequest, self).__init__("start", d)

class CleanupRequest(Request):
    def __init__(self, xid):
        super(CleanupRequest, self).__init__("cleanup", xid=xid)

class CliCmd(object):
    def __init__(self, server):
        self.server = server
        self.log = server.log

    def cli_cmd(self, command, agent, env=None, immediate=False,
                timeout=60*60*2):
        """ 1) Sends the command (a string)
            2) Waits for status/completion.  Saves the body from the status.
            3) Sends cleanup.
            4) Returns body from the status.

            "timeout" is the maximum amount of time the command is allowed
            to run before it is considered failed.
        """
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-arguments

        body = self._send_cli(command, agent, env=env, immediate=immediate)

        if body.has_key('error'):
            return body

        if not body.has_key('run-status'):
            return self.server.error(
                              "_send_cli (%s) missing 'run-status': %s" % \
                              (safecmd(command), str(body)))

        # It is possible for the command to finish immediately.
        if body['run-status'] == 'finished':
            return body

        cli_body = self._get_cli_status(body['xid'], agent, command, timeout)

        if not 'stdout' in cli_body:
            self.log.error(
                "check status of cli xid %d failed - missing 'stdout' in " + \
                "reply for command '%s': %s", body['xid'], command, cli_body)
            if not 'error' in cli_body:
                cli_body['error'] = \
                    ("Missing 'stdout' in agent reply for xid %d, " + \
                    "command '%s': %s") % \
                    (safecmd(command), body['xid'], cli_body)

        cleanup_body = self._send_cleanup(body['xid'], agent, command)

        if cli_body.has_key("error"):
            return cli_body

        if cleanup_body.has_key('error'):
            return cleanup_body

        return cli_body

    def _send_cli(self, cli_command, agent, env=None, immediate=False):
        """Send a "cli" command to an Agent.
            Returns a body with the results.
            Called without the connection lock."""
        # pylint: disable=too-many-return-statements

        self.log.debug("_send_cli")

        aconn = agent.connection
        aconn.lock()

        req = CliStartRequest(cli_command, env=env, immediate=immediate)

        headers = {"Content-Type": "application/json"}
        uri = self.server.CLI_URI

        displayname = agent.displayname and agent.displayname or agent.uuid
        self.log.debug(
            "about to send the cli command to '%s', conn_id %d, " + \
            "type '%s' xid: %d, command: %s",
            displayname, aconn.conn_id, agent.agent_type,
            req.xid, safecmd(cli_command))
        try:
            aconn.httpconn.request('POST', '/cli', req.send_body, headers)
            self.log.debug('sent cli command.')

            res = aconn.httpconn.getresponse()

            self.log.debug('_send_cli: command: cli: ' + \
                           str(res.status) + ' ' + str(res.reason))
            # print "headers:", res.getheaders()
            self.log.debug("_send_cli reading...")
            body_json = res.read()

            if res.status != httplib.OK:
                self.log.error("_send_cli: command: '%s', %d %s : %s",
                               safecmd(cli_command), res.status,
                               res.reason, body_json)
                reason = "Command sent to agent failed. Error: " + res.reason
                self.server.remove_agent(agent, reason)
                return self.server.httperror(res, method="POST",
                                      displayname=agent.displayname,
                                      uri=uri, body=body_json)

        except (httplib.HTTPException, EnvironmentError) as ex:
            self.log.error(
                "_send_cli: command '%s' failed with httplib.HTTPException: %s",
                           safecmd(cli_command), str(ex))
            # bad agent
            self.server.remove_agent(agent, "Command to agent failed. " + \
                                     "Error: " + str(ex))
            return self.server.error("_send_cli: '%s' command failed with: %s" %
                              (safecmd(cli_command), str(ex)))
        finally:
            aconn.unlock()

        self.log.debug("_send_cli done reading, body_json: " + body_json)
        body = json.loads(body_json)
        if body == None:
            return self.server.error("POST /cli response had a null body")
        self.log.debug("_send_cli body:" + str(body))
        if not body.has_key('xid'):
            return self.server.error(
                                "POST /cli response was missing the xid", body)
        if req.xid != body['xid']:
            return self.server.error("POST /cli xid expected: %d but was %d" % \
                              (req.xid, body['xid']), body)

        if not body.has_key('run-status'):
            return self.server.error(
                                "POST /cli response missing 'run-status'", body)
        if body['run-status'] != 'running' and body['run-status'] != 'finished':
            # FIXME: could possibly be finished.
            return self.server.error(
                "POST /cli response for 'run-status' was not 'running'", body)

        return body

    def _send_cleanup(self, xid, agent, orig_cli_command):
        """Send a "cleanup" command to an Agent.
            On success, returns the body of the reply.
            On failure, throws an exception.

            orig_cli_command is used only for debugging/printing.

            Called without the connection lock."""

        self.log.debug("_send_cleanup")
        aconn = agent.connection
        aconn.lock()
        self.log.debug("_send_cleanup got lock")

        req = CleanupRequest(xid)
        headers = {"Content-Type": "application/json"}
        uri = self.server.CLI_URI

        self.log.debug('about to send the cleanup command, xid %d', xid)
        try:
            aconn.httpconn.request('POST', uri, req.send_body, headers)
            self.log.debug('sent cleanup command')
            res = aconn.httpconn.getresponse()
            self.log.debug('command: cleanup: ' + \
                               str(res.status) + ' ' + str(res.reason))
            body_json = res.read()
            if res.status != httplib.OK:
                self.log.error("_send_cleanup: POST %s for cmd '%s' failed,"
                               "%d %s : %s", uri, orig_cli_command,
                               res.status, res.reason, body_json)
                alert = "Agent command failed with status: " + str(res.status)
                self.server.remove_agent(agent, alert)
                return self.server.httperror(res, method="POST",
                                      displayname=agent.displayname,
                                      uri=uri, body=body_json)

            self.log.debug("headers: " + str(res.getheaders()))
            self.log.debug("_send_cleanup reading...")

        except (httplib.HTTPException, EnvironmentError) as ex:
            # bad agent
            self.log.error("_send_cleanup: POST %s for '%s' failed with: %s",
                           uri, orig_cli_command, str(ex))
            self.server.remove_agent(agent, "Command to agent failed. " \
                                  + "Error: " + str(ex))
            return self.server.error("'%s' failed for command '%s' with: %s" % \
                                  (uri, orig_cli_command, str(ex)), {})
        finally:
            # Must call aconn.unlock() even after self.server.remove_agent(),
            # since another thread may waiting on the lock.
            aconn.unlock()
            self.log.debug("_send_cleanup unlocked")

        self.log.debug("done reading.")
        body = json.loads(body_json)
        if body == None:
            return self.server.error(
                              "POST /%s getresponse returned null body" % uri,
                              return_dict={})
        return body

    def _get_cli_status(self, xid, agent, orig_cli_command, timeout):
        """Gets status on the command and xid.  The timeout is the
           maximum amount of time the command is allowed to take before
           we consider it failed:

           Returns:

            Body in json with status/results.

            orig_cli_command is used only for debugging/printing.

            Note: Do not call this with the agent lock since
            we keep requesting status until the command is
            finished and that could be a long time.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

#        debug for testing agent disconnects
#        print "sleeping"
#        time.sleep(5)
#        print "awake"

        uri = self.server.CLI_URI + "?xid=" + str(xid)
        headers = {"Content-Type": "application/json"}

        aconn = agent.connection
        start_time = time.time()
        while True:
            now = time.time()
            if now - start_time > timeout:
                self.log.info("timeout for command '%s', xid %s, " + \
                              "conn_id %d, timeout %d, " + \
                              "elapsed %d, start_time %d, now %d",
                              safecmd(orig_cli_command), xid, aconn.conn_id,
                              timeout, now - start_time, start_time, now)
                kill_body = self.server.kill_cmd(xid, agent)
                return self.server.error(
                                   ("Command timed out after %d seconds: " + \
                                   "'%s', agent '%s', xid %d, conn_id %d " + \
                                   "kill results: %s") \
                                   % (timeout, safecmd(orig_cli_command),
                                   agent.displayname, xid, aconn.conn_id,
                                   str(kill_body)))

            self.log.debug("about to get status of cli command '%s', " + \
                           "xid %d, conn_id %d, timeout %d",
                           safecmd(orig_cli_command), xid, aconn.conn_id,
                           timeout)

            # If the agent is initializing, then "agent_connected"
            # will not know about it yet.
            if not aconn.initting and \
                    not self.server.agentmanager.agent_connected(aconn):
                self.log.warning(
                    "Agent '%s' (type: '%s', uuid %s, conn_id %d) " + \
                    "disconnected before finishing: %s",
                     agent.displayname, agent.agent_type, agent.uuid,
                     aconn.conn_id, uri)
                return self.server.error(
                    ("Agent '%s' (type: '%s', uuid %s, " + \
                    "conn_id %d), disconnected before finishing: %s") %
                    (agent.displayname, agent.agent_type, agent.uuid,
                    aconn.conn_id, uri))

            aconn.lock()
            self.log.debug("Sending GET " + uri)

            try:
                aconn.httpconn.request("GET", uri, None, headers)

                self.log.debug("Getting response from GET " +  uri)
                res = aconn.httpconn.getresponse()
                self.log.debug("status: " + str(res.status) + ' ' + \
                                                            str(res.reason))
                if res.status != httplib.OK:
                    self.server.remove_agent(agent,
                                 EventControl.AGENT_RETURNED_INVALID_STATUS)
                    return self.server.httperror(res,
                                          displayname=agent.displayname,
                                          uri=uri)

#                debug for testing agent disconnects
#                print "sleeping"
#                time.sleep(5)
#                print "awake"

                self.log.debug("_get_status reading.")
                body_json = res.read()
                body = json.loads(body_json)
                if body == None:
                    return self.server.error(
                            "Get /%s getresponse returned a null body" % uri)

                self.log.debug("body = " + str(body))

            except httplib.HTTPException, ex:
                self.server.remove_agent(agent,
                            "HTTP communication failure with agent: " + str(ex))
                return self.server.error(
                                  "GET %s failed with HTTPException: %s" % \
                                  (uri, str(ex)))
            except EnvironmentError, ex:
                self.server.remove_agent(agent,
                                  "Communication failure with " + \
                                  "agent. Unexpected error: " + str(ex))
                return self.server.error("GET %s failed with: %s" % \
                                         (uri, str(ex)))
            finally:
                aconn.unlock()

            if not 'run-status' in body:
                self.server.remove_agent(agent,
                                     EventControl.AGENT_RETURNED_INVALID_STATUS)
                return self.server.error(
                        ("GET %s command reply was missing 'run-status'!  " + \
                        "Will not retry: %s") % (uri, str(body)))

            if body['run-status'] == 'finished':
                # Make sure if the command failed, that the 'error'
                # key is set.
                if not 'exit-status' in body:
                    self.server.remove_agent(agent,
                                     EventControl.AGENT_RETURNED_INVALID_STATUS)
                    return self.server.error(
                        ("GET %s command reply returned 'finished' but was " + \
                         "missing 'exit-status'!  " + \
                        "Will not retry: %s") % (uri, str(body)))

                if body['exit-status'] != 0:
                    if body.has_key('stderr') and body['stderr']:
                        body['error'] = body['stderr']
                    else:
                        body['error'] = u"Failed with exit status: %d" % \
                                                        body['exit-status']
                return body
            elif body['run-status'] == 'running':
                time.sleep(self.server.cli_get_status_interval)
                continue
            else:
                self.server.remove_agent(agent,
                    "Communication failure with agent:  " + \
                    "Unknown run-status returned from agent: %s" % \
                                        body['run-status'])    # bad agent
                return self.server.error(
                                        "Unknown run-status: %s.  Will not " + \
                                        "retry." % body['run-status'], body)
