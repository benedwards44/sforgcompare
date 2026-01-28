$(document).ready(function ()
{	
	var urlPrefix =  'https://';
	var urlSuffix = '.salesforce.com/services/oauth2/authorize?response_type=code&client_id=' + $('#client_id').val() + '&redirect_uri=' + $('#redirect_uri').val() + '&scope=api&state=';

	$('#orgOneButton').click(function()
	{
		var loginUrl = urlPrefix;
		if ( $('#org_one_env').val() == 'Production' )
		{
			loginUrl += 'login'
		}
		else
		{
			loginUrl += 'test'
		}
		loginUrl += urlSuffix + $('#org_one_env').val() + 'org1';
		window.location = loginUrl;
	});

	$('#orgTwoButton').click(function()
	{
		var loginUrl = urlPrefix;
		if ( $('#org_two_env').val() == 'Production' )
		{
			loginUrl += 'login'
		}
		else
		{
			loginUrl += 'test'
		}
		loginUrl += urlSuffix + $('#org_two_env').val() + 'org2';
		window.location = loginUrl;
	});

	$('#id_email_choice').change(function() 
	{
		if ( $(this).val() == 'yes' )
		{
			$('#id_email').show();
		}
		else
		{
			$('#id_email').hide();
		}
	});

	$('[data-toggle="popover"]').popover();

});