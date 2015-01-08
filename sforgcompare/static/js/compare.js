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

function getContent(componentId)
{
	$.ajax(
	{
	    url: '/get_metadata/' + componentId,
	    type: 'get',
	    success: function(resp) 
	    {
	        return resp;
	    },
	    failure: function(resp) 
	    { 
	        return false;
	    }
	});
}

function getDiffHtml(componentId)
{
	$.ajax(
	{
	    url: '/get_diffhtml/' + componentId,
	    type: 'get',
	    success: function(resp) 
	    {
	        return resp;
	    },
	    failure: function(resp) 
	    { 
	        return false;
	    }
	});
}
