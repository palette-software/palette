<!DOCTYPE html>
<html>
<head>

<%block name="title">
<title>Palette</title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>

<%block name="fullstyle">
<meta charset="utf-8">
<meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width">
<link href='//fonts.googleapis.com/css?family=Roboto:300,500' rel='stylesheet' type='text/css'>
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/font-awesome.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">
</%block>

<script>
  var require = {
    paths: {
      'jquery': '/app/module/palette/js/vendor/jquery',
      'topic': '/app/module/palette/js/vendor/pubsub',
      'template' : '/app/module/palette/js/vendor/mustache',
      'domReady': '/app/module/palette/js/vendor/domReady',

      'bootstrap': '/app/module/palette/js/vendor/bootstrap'
    },
    shim: {
      'bootstrap': {
         deps: ['jquery']
      }
    }
  };
</script>

</head>
<body>

<%include file="_nav.mako" />

<div class="wrapper">
<div class="container">

<%include file="side-bar.mako" />

${next.body()}
</div>
</div>

</body>
</html>
