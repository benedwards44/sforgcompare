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
		$('#codeModalBody').html('<img src="/static/images/loading.gif" alt="Loading" title="Loading" width="30" height="30" />');

		// Component type of the cell clicked
		var componentType = $(this).parent().attr('class').split('_')[1].trim();
		var componentName = $(this).text().trim();

		// Set label of the modal
		$('#codeModalLabel').text(componentType + '/' + componentName);

		// If diff file - query for diff HTML that Python generated
		if ( $(this).hasClass('diff') )
		{
			$.ajax(
			{
			    url: '/get_diffhtml/' + $(this).attr('id'),
			    type: 'get',
			    success: function(resp) 
			    {
		    		$('#codeModalBody').html(resp);
			        // Remove nowrap attribute. This is handled better with CSS.
					$('#codeModalBody td[nowrap="nowrap"]').removeAttr('nowrap');
			    },
			    failure: function(resp) 
			    { 
			        $('#codeModalBody').html('<div class="alert alert-danger" role="alert"><p>There was an error getting the metadata:</p><br/><p>' + resp + '</p>>/div>');
			    }
			});
		}
		// Otherwise obtain metadata for display
		else
		{
			$.ajax(
			{
			    url: '/get_metadata/' + $(this).attr('id'),
			    type: 'get',
			    success: function(resp) 
			    {
			    	var metadata;
			    	if (componentType == 'ApexClass' || componentType == 'ApexTrigger' || componentType == 'classes' || componentType == 'triggers')
			    	{
			    		if (componentName.indexOf('meta.xml') != -1) 
			    		{
		    				metadata = resp.replace(/</g, '&lt;')
									.replace(/>/g,'&gt;')
									.replace(/\n/g, '<br/>');
	    				}
	    				else 
	    				{
	    					metadata = resp;
	    				}
			    	}
			    	else
			    	{
			    		metadata = resp.replace(/</g, '&lt;')
										.replace(/>/g,'&gt;')
										.replace(/\n/g, '<br/>');
			    	}

			    	var $content = $('<pre class="highlight">' + metadata + '</pre>');
					$content.syntaxHighlight();
					$('#codeModalBody').html($content);
			        $.SyntaxHighlighter.init();
			    },
			    failure: function(resp) 
			    { 
			        $('#codeModalBody').html('<div class="alert alert-danger" role="alert"><p>There was an error getting the metadata:</p><br/><p>' + resp + '</p>>/div>');
			    }
			});
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

function startDownloadJob(file_url, job_id) {

	if (file_url != '' && file_url != null) {

		updateModal(
			'File Ready For Download',
			'<div class="alert alert-success" role="alert" style="margin-bottom:10px;">Your file has been successfully generated.</div><div class="text-right"><a class="btn btn-success" href="' + file_url + '">Download File</a></div>',
			true
		);

		$('#downloadOfflineModal').modal();
	}
	else {

		updateModal(
			'Generating Offline File',
			'Your download file is being generated, this can take a few minutes...' +
			'<div class="progress">' +
				'<div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div>' +
			'</div>',
			false
		);

		$('#downloadOfflineModal').modal();

		$.ajax(
		{
		    url: '/compare_result/' + job_id + '/build_file/',
		    type: 'get',
		    dataType: 'json',
		    success: function(resp) {
		    	
		    	// There was an error running the job
		    	if (resp.status == 'Error') {

		    		updateModal(
			    		'Error Generating File',
			    		'<div class="alert alert-danger" role="alert">There was an error building your file: ' + resp.error + '</div>',
			    		true
			    	);

		    	}
		    	// Job has successfully started. Start looping for progress
		    	else {

		    		check_status(job_id);
		    	}
		    },
		    failure: function(resp) { 
		        
		        // Error starting job
		    	updateModal(
		    		'Error Generating File',
		    		'<div class="alert alert-danger" role="alert">There was an error building your file: ' + resp + '</div>',
		    		true
		    	);
		    }
		});
	}
}

function reRun(job_id) {

	var reRunJob = confirm('This will clear this current job and re-download metadata and compare the results.');

	if (reRunJob) {

		window.location = '/re-run-job/' + job_id;
	}
	else {

		return false;
	}
}

function updateModal(header, body, allow_close)
{
	if (allow_close)
	{
		$('#downloadOfflineModal .modal-header').html('<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button><h4 class="modal-title">' + header + '</h4>');
		$('#downloadOfflineModal .modal-footer').html('<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>');
	}
	else
	{
		$('#downloadOfflineModal .modal-header').html('<h4 class="modal-title">' + header + '</h4>');
		$('#downloadOfflineModal .modal-footer').html('');
	}

	$('#downloadOfflineModal .modal-body').html(body);
}



function check_status(job_id)
{
	var refreshIntervalId = window.setInterval(function () 
	{
   		$.ajax({
		    url: '/check_file_status/' + job_id + '/',
		    type: 'get',
		    dataType: 'json',
		    success: function(resp) 
		    {
		        if (resp.status == 'Finished')
		        {
		        	updateModal(
						'File Ready For Download',
						'<div class="alert alert-success" role="alert" style="margin-bottom:10px;">Your file has been successfully generated.</div><div class="text-right"><a class="btn btn-success" href="' + resp.url + '">Download File</a></div>',
						true
					);

					clearInterval(refreshIntervalId);
		        } 
		        else if (resp.status == 'Error')
		        {

					updateModal(
						'Error',
						'<div class="alert alert-danger" role="alert">There was an error building your file: ' + resp.error + '</div>',
						true
					);

					clearInterval(refreshIntervalId);
		        }
		        // Else job is still running, this will re-run shortly.
		    },
		    failure: function(resp) 
		    { 
				updateModal(
		    		'Error Generating File',
		    		'<div class="alert alert-danger" role="alert">There was an error building your file: ' + resp + '</div>',
		    		true
		    	);

				clearInterval(refreshIntervalId);
		    }
		});
	}, 1000);
}