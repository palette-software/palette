<%inherit file="dialog.mako" />
Status:
%if obj.main_status == 'RUNNING':
    <font color='green'>
%else:
    <font color='red'>
%endif
${obj.main_status}
</font>
at ${obj.status_time}</br>
<br></br>

<table border='1'>
 <tr>
    <th>Component</th> <th>PID</th> <th>Status</th></tr>
%for entry in obj.status_entries:
    %if entry.name != 'Status':
        <tr> <td>${entry.name}</td> <td>${entry.pid}</td> <td>${entry.status}</td></tr>
    %endif
%endfor
</table>
