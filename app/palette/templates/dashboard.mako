# -*- coding: utf-8 -*- 
<%inherit file="_layout.mako" />

<%block name="title">
<title>Palette - Activities </title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>
<%block name="fullstyle">
<meta charset="utf-8">
<meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width">
<link href='http://fonts.googleapis.com/css?family=Roboto:300,500' rel='stylesheet' type='text/css'>
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/font-awesome.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">

<script src="/app/module/palette/js/vendor/require.js"
        data-main="/app/module/palette/js/dashboard.js" >
</script>

<script src="/app/module/palette/js/vendor/modernizr.js"></script>

<style type="text/css">
</style>

</%block>
<%include file="side-bar.mako" />
<section class="secondary-side-bar">
  <h5>Production</h5>
  <ul class="server-list">
    <li>
      <a href="#">
        <img src="/app/module/palette/images/server-icons-green.png">
        <h5>Tableau Server Worker</h5>
        <p>123.123.1.2</p>
      </a>
    </li>
    <li>
      <a href="#">
        <img src="/app/module/palette/images/server-icons-green.png">
        <h5>Tableau Server Worker</h5>
        <p>123.123.1.2</p>
      </a>
    </li>
    <li>
      <a href="#">
        <img src="/app/module/palette/images/server-icons-green.png">
        <h5>Tableau Server Worker</h5>
        <p>123.123.1.2</p>
      </a>
    </li>
  </ul>
</section>
<%include file="events.mako" />

<%include file="commonjs.mako" />
