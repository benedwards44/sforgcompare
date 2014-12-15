$.SyntaxHighlighter.init();

$(document).ready(function () 
{
	$('tr.component').hide();
	$('tr.success').hide();

	checkAnyChildVisible();

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


		var metadata;
		if (componentName[0] == 'ApexClass' || componentName[0] == 'ApexTrigger')
		{
			metadata = $(this).parent().find('textarea').val();
		}
		// VisualForce markup requires HTML escaping
		else
		{
			metadata = $(this).parent().find('textarea').val()
											.replace(/</g, '&lt;')
											.replace(/>/g,'&gt;')
											.replace(/\n/g, '<br/>');
		}

		// Display the Python diff results
		if ( $(this).hasClass('diff') )
		{
			$('#codeModalBody').html(metadata);
		}
		// Show the code in a nice modal with syntax highlighting
		else
		{
			var $content;
			if ( $(this).hasClass('both_same') )
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
		}
		$('td.diff_next').hide();
		console.log($('table.diff').width());
		$('#scrollbar').width($('table.diff').width());
		$('#viewCodeModal').modal();
		console.log($('table.diff').width());
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

	});

	/* Add top scroll bar for code comparison */
	$("#top_scrollbar").scroll(function()
    {
        $("#codeModalBody").scrollLeft($("#top_scrollbar").scrollLeft());
    });

    $("#codeModalBody").scroll(function()
    {
        $("#top_scrollbar").scrollLeft($("#codeModalBody").scrollLeft());
    });

});

// Check if the parent component type (eg ApexClass), has any children. If not, ApexClass won't display at all
function checkAnyChildVisible()
{
	// Loop through type rows
	$.each($('tr.type'), function(typeKey, typeValue)
	{
		var childVisible = false;

		// Loop through component rows
		$.each($('tr[class*="' + $(this).attr('class').split('_')[1] + '"]'), function(componentKey, componentValue)
		{
			// It a row is visible, this is enough to know to show the parent
			if ($(this).is(':visible'))
			{
				childVisible = true;
				return;
			}
		});

		// If no children are visible, hide the parent
		if (!childVisible)
		{
			$(this).hide();
		}

	});
}
