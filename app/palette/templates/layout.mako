# -*- coding: utf-8 -*-
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">

<%include file="favicon.mako" />
<link rel="stylesheet" type="text/css" href="/fonts/fonts.css">
<link rel="stylesheet" type="text/css" href="/css/style.css" media="screen">

<%block name="title">
<title>Palette</title>
</%block>

<script>
  var require = {
    paths: {
      'jquery': '/js/vendor/jquery.min',
      'underscore': '/js/vendor/underscore',
      'topic': '/js/vendor/pubsub.min',
      'template': '/js/vendor/mustache.min',
      'react': '/js/vendor/react.min',
      'react-dom': '/js/vendor/react-dom.min',

      'bootstrap': '/js/vendor/bootstrap.min',
      'lightbox': '//www.helpdocsonline.com/v2/lightbox'
    },
    shim: {
      'bootstrap': {
         deps: ['jquery']
      },
      'lightbox': {
         deps: ['jquery']
      }
    }
  };
</script>
</head>

${next.body()}
