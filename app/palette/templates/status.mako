<%inherit file="dialog.mako" />

<p>
Status:
%if obj.main_status == 'RUNNING':
    <span class="running">
%else:
    <span class="stopped">
%endif
${obj.main_status}
</span>
at ${obj.status_time}
</p>

<table>
 <tr>
    <th>Component</th> <th>PID</th> <th>Status</th></tr>
%for entry in obj.status_entries:
    %if entry.name != 'Status':
        <tr> <td>${entry.name}</td> <td>${entry.pid}</td> <td>${entry.status}</td></tr>
    %endif
%endfor
</table>
