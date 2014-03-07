<%inherit file="_dialog.mako" />

<table class="dialog">
  <tr>
    <th>Agent</th> <th>Type</th> <th>Connection Time</th> <th>Disconnection Time</th> <th>Connected</th>
  </tr>
%for agent in obj.agents:
  <tr>
    <td>${agent.displayname}</td>
    <td>${agent.agent_type}</td>
    <td class="creation-time">${agent.last_connection_time_str}</td>
    <td class="creation-time">${agent.last_disconnect_time_str}</td>
    <td>${str(agent.connected())}</td>
  </tr>
%endfor
</table>
