$.SyntaxHighlighter.init();

$(document).ready(function () 
{
	$('tr.component').hide();
	$('tr.success').hide();
	$('#no_differences_message').hide();

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
		
		var componentName = $(this).attr('id').split('***');	
		$('#codeModalLabel').text(componentName[0] + ' - ' + componentName[1]);

		var metadata;

		// If same file but diff
		if ( $(this).hasClass('diff') )
		{
			// Take contents of div and put into modal
			$('#codeModalBody').html($(this).parent().find('div.diff_content').html());

			// Remove nowrap attribute. This is handled better with CSS.
			$('#codeModalBody td[nowrap="nowrap"]').removeAttr('nowrap');
		}

		// Other new file or same. Do normal string replace and syntax highlighting
		else
		{
			if (componentName[0] == 'ApexClass' || componentName[0] == 'ApexTrigger' || componentName[0] == 'classes' || componentName[0] == 'triggers')
			{
				metadata = $(this).parent().find('textarea').val();
			}
			else
			{
				// Remove HTML markup
				metadata = $(this).parent().find('textarea').val()
											.replace(/</g, '&lt;')
											.replace(/>/g,'&gt;')
											.replace(/\n/g, '<br/>');
			}

			var $content = $('<pre class="highlight">' + metadata + '</pre>');
			$content.syntaxHighlight();
			$('#codeModalBody').html($content);
	        $.SyntaxHighlighter.init();

		}

		// Load modal
		$('#viewCodeModal').modal();
	});

	// Change display options
	$('#display_option').change(function()
	{
		$('tr.component').hide();
		$('tr.type').show();

		if ( $(this).val() == 'diff')
		{
			checkAnyChildVisible();
		}
		else
		{
			$('#no_differences_message').hide();
		}

	});

	$('.loading-components').hide();
	$('#compare_results').show();
	checkAnyChildVisible();

});

// Check if the parent component type (eg ApexClass), has any children. If not, ApexClass won't display at all
function checkAnyChildVisible()
{
	// Loop through type rows
	$.each($('tr.type'), function()
	{
		var childVisible = false;

		// Loop through component rows
		$.each($('tr[class*="component_' + $(this).attr('class').split('_')[1] + '"]'), function()
		{
			// It a row is visible, this is enough to know to show the parent
			if ( !$(this).hasClass('success') )
			{
				childVisible = true;
				return false;
			}
		});

		// If no children are visible, hide the parent
		if (!childVisible)
		{
			$(this).hide();
		}

	});

	// Check that anything at all is visible
	$.each($('tr.type'), function()
	{
		var rowVisible = false;
		if ($(this).is(':visible'))
		{
			rowVisible = true;
			return false;
		}

		// If no rows are visible, display message
		if (!rowVisible)
		{
			$('#no_differences_message').show();
		}
	});

}
