$.SyntaxHighlighter.init();

$(document).ready(function () 
{
	$('tr.component').hide();
	$('tr.success').hide();

	// Toggle file show and hide
	$('tr.type td').click(function() 
	{
		var componentType = $(this).parent().attr('class').split('_')[1];
		$('.component_' + componentType).toggle();
		
		if ( $('#display_option').val() == 'diff')
		{
			$('tr.success').hide();
		}

	});

	// Open code view modal
	$('tr.component td').click(function() 
	{
		var componentName = $(this).attr('id').split('.');	
		$('#codeModalLabel').text(componentName[0] + ' - ' + componentName[1]);

		var metadata = $(this).find('textarea').val()
										.replace(/</g, '&lt;')
										.replace(/>/g,'&gt;')
										.replace(/\n/g, '<br/>');
		var $content;
		if ( $(this).hasClass('both') )
		{
			$content = $('<div style="float:left;width:49%;"><pre class="highlight" >' + metadata + '</pre></div><div style="float:left;width:49%;margin-left:2%;"><pre class="highlight">' + metadata + '</pre></div><div class="clear:both;></div>');
		}
		else
		{
			$content = $('<pre class="highlight">' + metadata + '</pre>');
		}

		$content.syntaxHighlight();
		$('#codeModalBody').html($content);
        $.SyntaxHighlighter.init();
		$('#viewCodeModal').modal();
	});

	// Change display options
	$('#display_option').change(function()
	{
		$('tr.component').hide();
	});

});
