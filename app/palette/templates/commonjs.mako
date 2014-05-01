<script src="/app/module/palette/js/vendor/jquery.js"></script>
<script type="text/javascript">

	$(function(){
		$('#toggle-side-menu').bind('click', function() {
			$('.main-side-bar').toggleClass('collapsed');
		});

		$('#mainNav .container > i').bind('click', function() {
			$('.main-side-bar').toggleClass('open');
			$(this).toggleClass('open');
		});
		
	});

	function clearmenu() {
		$('.main-side-bar').removeClass('open');
		$('.main-side-bar').removeClass('collapsed');
		$('#mainNav .container > i').removeClass('open');
	}

	$(function(){
		$('#toggle-events').bind('click', function() {
			clearmenu();
			$('.secondary-side-bar').toggleClass('closed');
		});	
	});

	var viewport = $(window).width();

    $('#mainNav ul.nav li.more').bind('mouseenter', function() {
        if (viewport >= 960) {
        	$('#mainNav ul.nav li.more ul').removeClass('visible');
            $(this).find('ul').addClass('visible');
        }
    });
    $('#mainNav ul.nav li.more').bind('mouseleave', function() {
        if (viewport >= 960) {
            $(this).find('ul').removeClass('visible');
        }
    });     
    
    $('#mainNav ul.nav li.more a').bind('click', function() {
        if (viewport <= 960) {
        	$('#mainNav ul.nav li.more ul').removeClass('visible');
            event.preventDefault();
        }

    });

    $('#mainNav ul.nav li.more').bind('click', function() {
        if (viewport <= 960) {
            $(this).find('ul').toggleClass('visible');
        } 
    });
	
</script>
