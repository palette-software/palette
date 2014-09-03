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
<meta name="viewport" content="width=980,minimal-ui">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/font-awesome.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/fonts/fonts.css">
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

<script id="server-list-template" type="x-tmpl-mustache">
  {{#environments}}
  <h1>{{name}}</h1>
  <ul class="server-list">
    {{#agents}}
    <li>
      <a>
        <i class="fa fa-fw fa-laptop {{color}}"></i>
	    <div>
          <h5>{{displayname}}</h5>
          <span class="hostname">{{hostname}}</span>
          <span class="address">{{ip_address}}</span>
	    </div>
        <i class="fa fa-fw fa-angle-down down-arrow"></i>
      </a>
      <ul class="processes">
	{{#volumes}}
	<li>
	  <i class="fa fa-fw fa-circle {{color}}"></i>
	  Storage: {{name}} {{value}}
	</li>
	{{/volumes}}
	{{#license}}
	<li>
	  <i class="fa fa-fw fa-circle {{color}}"></i>
	  License: Tableau
	</li>
	{{/license}}
	{{#in_ports}}
	<li>
	   <i class="fa fa-fw fa-circle {{color}}"></i>
	   In: {{name}} ({{num}})
	</li>
	{{/in_ports}}
	{{#out_ports}}
	<li>
	   <i class="fa fa-fw fa-circle {{color}}"></i>
	   Out: {{name}} ({{num}})
	</li>
	{{/out_ports}}
	{{#details}}
	<li>
	  <i class="fa fa-fw fa-circle {{color}}"></i>
	  {{name}} ({{pid}})
	</li>
	{{/details}}
	{{#warnings}}
	<li>
	  <i class="fa fa-fw fa-circle {{color}}"></i>
	  {{message}}
	</li>
	{{/warnings}}
      </ul>
    </li>
    {{/agents}}
  </ul>
  {{/environments}}
</script>

<script id="editbox-view" type="x-tmpl-mustache">
  <span>{{value}}</span>
  <i class="fa fa-fw fa-pencil"></i>
</script>

<script id="editbox-edit" type="x-tmpl-mustache">
  <input type="text" value="{{value}}" />
  <i class="fa fa-fw fa-check ok"></i>
  <i class="fa fa-fw fa-times cancel"></i>
</script>

<script id="onoffswitch" type="x-tmpl-mustache">
  <input type="checkbox" class="onoffswitch-checkbox" {{checked}}>
    <label class="onoffswitch-label">
      <span class="onoffswitch-inner"></span>
      <span class="onoffswitch-switch"></span>
    </label>
</script>

</head>
<body>

<%include file="_nav.mako" />

<div class="wrapper">
<div class="container">

<%include file="side-bar.mako" />

<section class="secondary-side-bar servers">
  <div id="server-list"></div>
</section>

${next.body()}
</div>
</div>

</body>
</html>
