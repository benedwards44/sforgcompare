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
		// Set loading gif while metadata loads
		$('#codeModalBody').html('<img src="staticfiles/images/loading.gif" alt="Loading" title="Loading" width="30" height="30" />');

		// Component type of the cell clicked
		var componentType = $(this).parent().attr('class').split('_')[1].trim();
		var componentName = $(this).text().trim();

		// Set label of the modal
		$('#codeModalLabel').text(componentType + '/' + componentName);

		// If diff file - query for diff HTML that Python generated
		if ( $(this).hasClass('diff') )
		{
			var metadata = component_data['diff-' + $(this).attr('id')];

    		$('#codeModalBody').html(metadata);

	        // Remove nowrap attribute. This is handled better with CSS.
			$('#codeModalBody td[nowrap="nowrap"]').removeAttr('nowrap');
		}
		// Otherwise obtain metadata for display
		else
		{

			console.log(componentName);

	    	var metadata = component_data['component-' + $(this).attr('id')];
	    	
	    	if (componentType == 'ApexClass' || componentType == 'ApexTrigger' || componentType == 'classes' || componentType == 'triggers')
	    	{
	    		if (componentName.indexOf('meta.xml') != -1) {

	    			metadata = metadata.replace(/</g, '&lt;')
								.replace(/>/g,'&gt;')
								.replace(/\n/g, '<br/>');
	    		}
	    	}
	    	else
	    	{
	    		metadata = metadata.replace(/</g, '&lt;')
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

	$('.loading-display').hide();
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
				return;
			}
		});

		// If no children are visible, hide the parent
		if (!childVisible)
		{
			$(this).hide();
		}

	});

	var rowVisible = false;

	// Check that anything at all is visible
	$.each($('tr.type'), function()
	{
		if ($(this).is(':visible'))
		{
			rowVisible = true;
			return;
		}
	});

	// If no rows are visible, display message
	if (!rowVisible)
	{
		$('#no_differences_message').show();
	}

}