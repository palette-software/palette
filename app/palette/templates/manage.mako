<%inherit file="dialog.mako" />

%for agent in obj.agents:
<p>${agent}</p>
%endfor
