<%inherit file="_dialog.mako" />

<table class="dialog">
 <tr>
    <th>Backup</th> <th>Backup Server</th> <th>Date and Time</th>
 </tr>
%for data in obj.backup_entries:
    <tr>
      <td>${data['name']}</td>
      <td>${data['ip-address']}</td>
      <td class="creation-time">${data['creation-time']}</td>
    </tr>
%endfor
</table>
