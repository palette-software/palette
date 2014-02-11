<%inherit file="_dialog.mako" />

<table class="dialog">
  <tr>
    <th>Agent</th> <th>Type</th> <th>Creation Time</th> <th>Connected</th>
  </tr>
%for agent in obj.agents:
  <tr>
    <td>${agent.hostname}</td>
    <td>${agent.agent_type}</td>
    <td class="creation-time">${agent.creation_time}</td>
    <td>${str(agent.connected())}</td>
  </tr>
%endfor
</table>
