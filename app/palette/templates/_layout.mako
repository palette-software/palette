<!DOCTYPE html>
<html>
<head>

<%block name="title">
<title>Akiri Solutions, Inc.</title>
</%block>

<%block name="favicon">
</%block>

<%block name="fullstyle">
<link href="http://fonts.googleapis.com/css?family=News+Cycle:400,700|Roboto:300,400,700" rel="stylesheet" type="text/css">
<link rel="stylesheet" type="text/css" href="/app/module/akiri.framework/css/style.css" media="screen">
<%block name="style"></%block>
</%block>
<body>

<%include file="_nav.mako" />

<div class="wrapper">
<div class="container">
${next.body()}
</div>
</div>
</body>
</html>
