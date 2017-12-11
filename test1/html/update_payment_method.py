<!DOCTYPE html>
<html lang="en-us">

<head>
  <!-- Latest compiled and minified CSS -->
  <!--<link rel="stylesheet" href="/static/css/bootstrap.3.3.7.min.css">-->
  <link rel='stylesheet' href='/static/css/bootstrap.min.css'>

  <!-- jQuery library -->
  <script src="/static/scripts/jquery.3.2.1.min.js"></script>

  <!-- Latest compiled JavaScript -->
  <script src="/static/scripts/bootstrap.3.3.7.min.js"></script>
  <script>
    function bs_input_file() {
	$(".input-file").before(
		function() {
			if ( ! $(this).prev().hasClass('input-ghost') ) {
				var element = $("<input type='file' class='input-ghost' style='visibility:hidden; height:0'>");
				element.attr("name",$(this).attr("name"));
				element.change(function(){
					element.next(element).find('input').val((element.val()).split('\\').pop());
				});
				$(this).find("button.btn-choose").click(function(){
					element.click();
				});
				$(this).find("button.btn-reset").click(function(){
					element.val(null);
					$(this).parents(".input-file").find('input').val('');
				});
				$(this).find('input').css("cursor","pointer");
				$(this).find('input').mousedown(function() {
					$(this).parents('.input-file').prev().click();
					return false;
				});
				return element;
			}
		}
	);
}
$(function() {
	bs_input_file();
});

  </script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>美基金朋友圈交易站</title>
</head>

<body>
  <div class="container">
    <nav class="navbar navbar-inverse">
      <div class="container-fluid">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#myNavbar">
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
          <a class="navbar-brand" href="#">交易站商标图案</a>
        </div>
        <div class="collapse navbar-collapse" id="myNavbar">
          <ul class="nav navbar-nav">
            <li><a href="#">卖美基金</a></li>
            <li class="active"><a href="#">买美基金</a></li>
            <li><a href="#">公布交易</a></li>
          </ul>
          <ul class="nav navbar-nav navbar-right">
            <li><a href="account.html"><span class="glyphicon glyphicon-user"></span>我的账户</a></li>
            <li><a href="logout.html"><span class="glyphicon glyphicon-log-in"></span> 退出</a></li>
          </ul>
        </div>
      </div>
    </nav>
  </div>
  <div class="container">
    <h6>美基金余额：2302.35 状态：锁定</h6>
    <div class="well">
      <div class="row">
          <h4>添加,修改付款方式</h4>
          <form method="POST" action="#" enctype="multipart/form-data">
          <input type='hidden' name='csrfmiddlewaretoken' value='cuyRJ1AJO9ZFz7Kr4JOenRslxTnE9x3T' />
          <div id="div_id_username" class="form-group"> <label for="id_username" class="control-label  requiredField">支付方式<span class="asteriskField">*</span> </label>
            <div class="controls ">
              <select class="form-control" id="sel_id_payment_provider">
                {% if payment_providers %}
                   {% for provider in payment_providers %}
                   <option value="{{ payment_provider.name }}">{{ payment_provider.alias }}</option>
                   {% endfor %}
                {% endif %}
              </select>
            </div>
          </div>
          <div id="div_id_password1" class="form-group"> <label for="id_password1" class="control-label  requiredField">账号<span class="asteriskField">*</span> </label>
            <div class="controls "> <input class="textinput textInput form-control" id="id_password1" name="password1" type="password" /> </div>
          </div>
          <div id="div_id_password2" class="form-group"> <label for="id_password2" class="control-label  requiredField">支付账户二维码<span class="asteriskField">*</span> </label></div>
            <!-- COMPONENT START -->
            <div class="form-group">
              <div class="input-group input-file" name="Fichier1">
                <input type="text" class="form-control" placeholder='选择二维码图像文件...' />
                <span class="input-group-btn">
              		<button class="btn btn-default btn-choose" type="button">选择</button>
                    <button type="reset" class="btn btn-danger">清除</button>
            	</span>
              </div>
            </div>
            <!-- COMPONENT END -->
            <div class="form-group">
              <button type="submit" class="btn btn-success pull-right" disabled>确认</button>
              <button type="submit" class="btn btn-default pull-left" disabled>取消</button>
            </div>
        </form>
      </div>
    </div>
  </div>

  <footer class="container">
    <div class="row" style="text-align: center;">
      美基金团队版权所有2017&copy
    </div>
  </footer>
</body>

</html>
