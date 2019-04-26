$(document).ready(function() {
    // submit on the weixin account info
    $('#btn_saveAccountInfo').click(function() {
        var account = $('#account_at_provider').val().trim();
        var alias = $('#account_alias').val().trim();
        if (account === "") {
            $('#div_accountInfo_error').text('请输入您的微信账号');
            return;
        } else if (alias === "") {
            $('#div_accountInfo_error').text('请输入您的昵称');
            return;
        } else {
            $('#div_accountInfo_error').text('');
        }
        $('#frm_weixin_accountInfo').submit();
    })
    $('#btn_cancel').click(function() {
        window.location.replace('/trading/accounts/accountinfo/');
    })
})