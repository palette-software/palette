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

<script src="/app/module/palette/js/vendor/modernizr.js"></script>

<style type="text/css">
.main-side-bar ul.actions li.active-home a {
  background-color:rgba(0,0,0,0.1);
  box-shadow:0 -2px rgba(0,0,0,0.1);
}
.main-side-bar ul.actions li.active-home a:after {
  content: "";
  position: absolute;
  right: 0;
  top: 50%;
  margin-top: -12px;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 12px 12px 12px 0;
  border-color: transparent #555A60 transparent transparent;
  display: block;
}
.main-side-bar.collapsed .actions li.active-home a {
  background-color: #ececec;
}
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

<script>
require({
  packages: [
    { name: "palette", location: "/app/module/palette/js" }
  ]
}, [ "palette/monitor", "palette/backup", "palette/manage" ]);
</script>

<%include file="commonjs.mako" />