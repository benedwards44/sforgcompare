$(document).ready(function() {

	$('.loading').hide();

	$('.logging_out').hide();

	/* Scroll to top logic */
	var offset = 220;
    var duration = 500;
    $(window).scroll(function() {
        if (jQuery(this).scrollTop() > offset) {
            jQuery('.back-to-top').fadeIn(duration);
        } else {
            jQuery('.back-to-top').fadeOut(duration);
        }
    });
    
    $('.back-to-top').click(function(event) {
        event.preventDefault();
        jQuery('html, body').animate({scrollTop: 0}, duration);
        return false;
    });
	
});

function hideTable(){
	$('.login_table').hide();
	$('#select_components').hide();
	$('.messages').hide();
	$('.loading').show();
}
function showTable(){
	$('.login_table').show();
	$('#select_components').show();
	$('.messages').show();
	$('.loading').hide();
}

function showLogout(){
	$('.login_table').hide();
	$('#select_components').hide();
	$('.messages').hide();
	$('.logging_out').show();
}

function hideLogout(){
	$('.login_table').show();
	$('#select_components').show();
	$('.messages').show();
	$('.logging_out').hide();
}