<script src="/app/module/palette/js/vendor/jquery.js"></script>
<script src="/app/module/palette/js/foundation.min.js"></script>
<script>
  var $rows = $(".dashboard .row");
  $(document).foundation();
</script>
<script type="text/javascript">
    var viewport = $(window).width();

    if (viewport >= 1200) {
        $('#mainNav ul.nav li.more').bind('mouseenter', function() {
        $(this).find('ul').addClass('visible');
        });
        $('#mainNav ul.nav li.more').bind('mouseleave', function() {
            $(this).find('ul').removeClass('visible');
        });     
    } 
    else {
        

        $('li.more > a').bind('click', function() {
            event.preventDefault();
        });

        $('#mainNav ul.nav > li.more').bind('click', function() {
          $(this).find('ul').toggleClass('visible');
        });

        $('#toggle-main-menu').bind('click', function() {
            $('#mainNav ul.nav').toggleClass('visible');
            $(this).toggleClass('visible');
        });
    }
    
</script>