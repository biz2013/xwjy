function create_purchase_order(sell_order_id, sell_order_owner_userid,
   locked_in_unit_price, available_units_for_purchase) {
    $("#reference_order_id").val(sell_order_id);
    $("#owner_user_id").val(sell_order_owner_userid);
    $("#locked_in_unit_price").val(locked_in_unit_price);
    $("#available_units_for_purchase").val(available_units_for_purchase);

    $("#form_create_purchase_order").submit();
}

function show_total_cost(units, price) {
  alert("show_total_cost " + units + " " + price)
  if (!isNaN(units)) {
    $("#total_cost").text("总额: " + (units * price));
  }
}
