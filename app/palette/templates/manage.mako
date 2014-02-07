<%inherit file="dialog.mako" />

%for agent in obj.agents:
<p>agent name: ${agent.hostname}, type: ${agent.agent_type}, connected at ${agent.creation_time}</p>
%endfor
