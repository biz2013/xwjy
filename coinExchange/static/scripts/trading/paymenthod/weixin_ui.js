$(document).ready(function() {
    // submit on the weixin account info
    $('#btn_saveAccountInfo').click(function() {
        var account = $('#account_at_provider').val().trim();
        var alias = $('#account_alias').val().trim();
        if (account === "" && alias === "") {
            $('#div_accountInfo_error').text('请您的微信账号或昵称，两者不可都为空');
            return;
        } else {
            $('#div_accountInfo_error').text('');
        }
        $('#frm_weixin_accountInfo').submit();
    })
})