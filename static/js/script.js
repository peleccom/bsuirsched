GROUP_COOKIE_NAME = "default_group"
function SetDefaultGroup(group){
    $.cookie(GROUP_COOKIE_NAME, group, {expires: 160});
    $("#SetDefaultButton").hide();
    $("#DeleteDefaultButton").show();

}

function DeleteDefaultGroup(){
    $.removeCookie(GROUP_COOKIE_NAME);
    $("#DeleteDefaultButton").hide();
    $("#SetDefaultButton").show();
}