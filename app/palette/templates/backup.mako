<%inherit file="dialog.mako" />

<table>
 <tr>
    <th>Backup</th> <th>Backup Server</th> <th>Date and Time</th></tr>
%for entry in obj.backup_entries:
    <tr> <td>${entry.name}</td> <td>${entry.ip_address}</td> <td>${entry.creation_time}</td></tr>
%endfor
</table>
