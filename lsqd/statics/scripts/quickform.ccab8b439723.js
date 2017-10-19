/**
 * Quick order form logic.
 *
 */

/* global jQuery, google */

(function($) {

    "use strict";

    var spinner = $("<span class='online-provider-spinner'><i class='fa fa-spinner fa-spin'></i></span>");

    function setFieldVisible(form, field_name, visible) {
        var field = form.find('[name=' + field_name + ']');
        var form_group_div = field.parent().parent();
        if (visible) {
            form_group_div.css('display', 'inline-block');
        } else {
            form_group_div.css('display', 'none');
        }
    }

    /**
     * @return {String} "buy" or "sell";
     */
    function getTradeType(form) {
        return form.find("input[name='action']").val();
    }

    function getPaymentMethodName(id) {
        var pm = window.quickForm.paymentMethodData[id];
        if(pm) {
            return pm.name;
        } else {
            return id;
        }
    }

    /**
     * Get the payment method currently selected.
     */
    function getSelectedPaymentMethod(form) {
        return form.find("[name='online_provider']").val();
    }

    /**
     * Rebuild payment method options <select>
     */
    function refreshPaymentMethodChoices(form, data) {

        var s = $('<select class="form-control" id="id_online_provider" name="online_provider"/>');

        $(data).each(function() {

            var optgroup = $("<optgroup />").attr("label", this.name);
            $(this.methods).each(function() {
                var key = this;
                optgroup.append($("<option/>").attr("value", key).text(getPaymentMethodName(key)));
            });

            s.append(optgroup);
        });

        form.find('[name="online_provider"]').replaceWith(s);
        form.find(".online-provider-spinner").replaceWith(s);

        setupOnlineProviderEventListeners();
    }


    /**
     * Update the form with country specific payment method list from the server.
     *
     * @param  {String} tradeType   "buy" or "sell"
     * @param  {String} countryCode "FI"
     */
    function loadPaymentMethodList(form, tradeType, countryCode) {

        // Preserve the selected choice
        var paymentMethod = form.find('[name="online_provider"]').val();

        form.find('[name="online_provider"]').replaceWith(spinner);

        var params = {
            "country": countryCode,
            "type": tradeType
        };

        $.getJSON(window.quickForm.paymentMethodAjaxUrl, params, function(data) {
            refreshPaymentMethodChoices(form, data);
            var online_provider_select = form.find('[name="online_provider"]');
            if (online_provider_select.find('option[value="' + paymentMethod + '"]').length > 0) {
                online_provider_select.val(paymentMethod);
            }
            selectCurrencyBasedOnOnlineProvider(form);
        });
    }

    /**
     * Chooce currency by active country.
     */
    function chooseCurrency(form, cc) {
        if(!cc) {
            return;
        }
        cc = cc.toUpperCase();
        var cur = window.quickForm.currencyData[cc];
        if(!cur) {
            cur = "USD";
        }
        form.find('[name="currency"]').val(cur);
    }


    /**
     * User changes the place fallback.
     *
     * @param location {Object} Google Places location preprocessed for the consumption
     */
    function onPlace(form, location) {
        var countryCode = location.countryCode;
        var tradeType = getTradeType(form);
        loadPaymentMethodList(form, tradeType, countryCode);
        chooseCurrency(form, countryCode);
    }

    /**
     * User changes the place dropdown fallback.
     */
    function onPlaceCountry(form) {
        var select = form.find("select[name='place_country']")[0];
        var country_code = select.value;
        var country_name = select.options[select.selectedIndex].innerText;
        var tradeType = getTradeType(form);
        loadPaymentMethodList(form, tradeType, country_code);
        chooseCurrency(form, country_code);

        form.find('[name="lat"]').val(0.0);
        form.find('[name="lon"]').val(0.0);
        form.find('[name="location_string"]').val(country_name);
        form.find('[name="country_code"]').val(country_code);

        // Also set new value for Google Places input
        form.find('[name="place"]').val(country_name);
    }

    /**
     * Set up the location widget magic
     */
    function makeGooglePlaces(form) {
        var input = form.find('[name="place"]');

        if(!input.length) {
            throw new Error("Place widget missing");
        }
        var autocomplete = window.createPlaceAutocompleteSelectFirst(input[0]);
        // When user selects an entry in the list kick in the magic
        google.maps.event.addListener(autocomplete, "place_changed", function() {

            var place = autocomplete.getPlace();
            if (!place.geometry) {
                return;
            }

            var location = window.splitLocation(place);

            // Update payment listing for new location, etc.
            onPlace(form, location);

            form.find('[name="lat"]').val(place.geometry.location.lat());
            form.find('[name="lon"]').val(place.geometry.location.lng());
            form.find('[name="location_string"]').val(location.locationString);
            form.find('[name="country_code"]').val(location.countryCode);

            // Also set new value for country dropdown
            form.find('[name="place_country"]').val(location.countryCode);
        });
    }


    /**
     * Calls selectCorrectPlaceInput() for both forms
     */
    function selectCorrectPlaceInputs() {
        var forms = $(".search-form");
        forms.each(function() {
            var form = $(this);
            selectCorrectPlaceInput(form);
        });
    }


    /**
     * Depending offer type, select either basic dropdown or advanced Google place widget.
     */
    function selectCorrectPlaceInput(form) {
        var method = getSelectedPaymentMethod(form);

        if (method == 'CASH') {
            // If Google Places is not yet initialized, then do it now
            if (!form.google_places_initialized) {
                makeGooglePlaces(form);
                form.google_places_initialized = true;
            }
            setFieldVisible(form, 'place_country', false);
            setFieldVisible(form, 'place', true);
        } else {
            setFieldVisible(form, 'place_country', true);
            setFieldVisible(form, 'place', false);
        }
    }

    /**
     * Some online providers might want to change currency.
     */
    function selectCurrencyBasedOnOnlineProvider(form) {
        var method = getSelectedPaymentMethod(form);
        if (method) {
            var method_data = window.quickForm.paymentMethodData[method];
            var allowed_currencies = method_data['currencies'];
            var selected_currency = form.find('[name="currency"]').val();
            // If only certain currencies are allowed and
            // currency currency is not in them, then change currency.
            if (allowed_currencies && allowed_currencies.indexOf(selected_currency) < 0) {
                form.find('[name="currency"]').val(allowed_currencies[0]);
            }
        }
    }

    /**
     * When the form is opened for the first time, preload payment method list
     */
    function preloadPaymentMethods() {
        var forms = $(".search-form");
        forms.each(function() {
            var form = $(this);
            var paymentMethod = form.find('[name="online_provider"]').val();
            if (getTradeType(form) === 'buy') {
                refreshPaymentMethodChoices(form, window.quickForm.paymentMethodChoicesBuy);
            } else {
                refreshPaymentMethodChoices(form, window.quickForm.paymentMethodChoicesSell);
            }
            form.find('[name="online_provider"]').val(paymentMethod);
        });
    }

    /**
     * Prevent form submission on enter
     */
    function preventEnter() {
        $(".search-form input, .search-form select").keypress(function(event) { return event.keyCode != 13; });
    }

    /** On mobile, scroll the results visible */
    function jumpToResults() {
        if(window.quickForm.searched && window.hasTouch) {
            window.location.hash = "results";
        }
    }

    /**
     * For ONLINE_SELL, ONLINE_BUY we do HTTP GET instead of HTTP POST
     *
     * - Makes Back button links, work correctly
     *
     * - We can't do this form cash: HTTP GET query with location_string considered harmful, please see quick_form()
     *
     * - If JavaScript is not working, always falls back to HTTP POST
     *
     * TODO: Long term solution: better location database, all locations correctly
     * resolved on the server side.
     */
    function makeLinkableSubmission() {
        var forms = $(".search-form");
        forms.each(function() {
            var form = $(this);
            form.find("[name='find-offers']").click(function() {
                if(getSelectedPaymentMethod($(this).parents(".search-form")) != "CASH") {
                    form.attr("method", "GET");
                    // Disable unnecessary fields, so they don't pollute the URL
                    form.find("input[name='lat']").attr("disabled", "disabled");
                    form.find("input[name='lon']").attr("disabled", "disabled");
                    form.find("input[name='location_string']").attr("disabled", "disabled");
                    form.find("input[name='place']").attr("disabled", "disabled");
                    form.find("input[name='csrfmiddlewaretoken']").attr("disabled", "disabled");
                } else {
                    form.attr("method", "POST");
                    // Location sensitive search
                    form.find("input[name='lat']").removeAttr("disabled");
                    form.find("input[name='lon]").removeAttr("disabled");
                    form.find("input[name='location_string']").removeAttr("disabled");
                    form.find("input[name='place']").removeAttr("disabled");
                    form.find("input[name='csrfmiddlewaretoken']").removeAttr("disabled");
                }
            });
        });
    }

    function setupOnlineProviderEventListeners() {
        var forms = $(".search-form");
        forms.each(function() {
            var form = $(this);
            form.find("select[name='online_provider']").change(function() {
                selectCorrectPlaceInput(form);
                selectCurrencyBasedOnOnlineProvider(form);
            });
        });
    }

    function setupPlaceCountryEventListeners() {
        var forms = $(".search-form");
        forms.each(function() {
            var form = $(this);
            form.find("select[name='place_country']").change(function() {
                onPlaceCountry(form)
            });
        });
    }

    /**
     * Use hidden inputs to choose good default for country dropdown.
     */
    function selectPlaceCountryDefaults() {
        var forms = $(".search-form");
        forms.each(function() {
            var form = $(this);
            var country_code = form.find("input[name='country_code']").val();
            if (!country_code) {
                country_code = 'US';
            }
            form.find("select[name='place_country']").val(country_code);
        });
    }

    $(window).ready(function() {

        // Quick form not on the page
        if($(".search-form").length === 0) {
            return;
        }
        selectCorrectPlaceInputs();
        preventEnter();
        // jumpToResults();
        makeLinkableSubmission();
        preloadPaymentMethods();
        setupOnlineProviderEventListeners();
        setupPlaceCountryEventListeners();
        selectPlaceCountryDefaults();
    });

})(jQuery);
