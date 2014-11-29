$(document).ready(function ()
{
	$('#orgOneButton').click(function()
	{
		var loginUrl = 'https://';
		if ( $('#org_one_env').val() == 'Production' )
		{
			loginUrl += 'login'
		}
		else
		{
			loginUrl += 'test'
		}
		loginUrl += '.salesforce.com/services/oauth2/authorize?response_type=code&client_id={{client_id}}&redirect_uri={{redirect_uri}}&scope=api&state=' + $('#org_one_env').val() + 'org1';
		popupwindow(loginUrl);
	});

	$('#orgTwoButton').click(function()
	{
		var loginUrl = 'https://';
		if ( $('#org_two_env').val() == 'Production' )
		{
			loginUrl += 'login'
		}
		else
		{
			loginUrl += 'test'
		}
		loginUrl += '.salesforce.com/services/oauth2/authorize?response_type=code&client_id={{client_id}}&redirect_uri={{redirect_uri}}&scope=api&state=' + $('#org_one_env').val() + 'org2';
		popupwindow(loginUrl);
	});

});

function popupwindow(url) 
{
	var w = 800;
	var h = 500;
  	var left = (screen.width/2)-(w/2);
  	var top = (screen.height/2)-(h/2);
  	return window.open(url, 'SalesforceLogin', 'toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width='+w+', height='+h+', top='+top+', left='+left);
} 

function updateOrgDetails(org, username, org_name)
{
	if (org == 'one')
	{
		$('#orgOneLogin').hide();
		$('#orgOneDisplay').show();
		$('#orgOneUsername').text(username);
		$('#orgOneOrg').show(org_name);
	}
	else
	{
		$('#orgTwoLogin').hide();
		$('#orgTwoDisplay').show();
		$('#orgTwoUsername').text(username);
		$('#orgTwoOrg').show(org_name);
	}

	// Both elements are visible, show the GO button
	if ( $('orgOneDisplay').is(":visible") && $('orgTwoDisplay').is(":visible") )
	{
		$('#compareOrgs').show();
	}
}