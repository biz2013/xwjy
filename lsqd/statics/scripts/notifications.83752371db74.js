/**
 * Simple cross-window/cross-tab message and notification handler with AJAX poller.
 *
 *
 */
(function($) {

    "use strict";

    /** The notification data hold for this tab */
    var currentNotificationData = null;

    /** Timer handle we are using to flash the message bar. */
    var blinker = null;

    /** setTimeout() handle for polling new events. */
    var poller = null;

    /** Should we stop polling the server */
    var finished = false;

    /* Icons we use in the attention seeking */
    var favicon = $("#favicon");
    var faviconBlink = $("#favicon-blink");

    /** Default notification poller settings */
    var config = {

        /** How often we poll for new notifications */
        interval: 15000,

        /** Randomize notification loads so that all windows don't try to load simultaneously */
        variance : 3000,

        /**
         * fetcher(callback) - function to be called to trigger loading of new notifications.
         * Usually something which does AJAX poll and then calls fetcher in the end.
         *
         * Callback is a function reference to onFetchData().
         *
         */
        fetcher: null,

        /**
         * updater(data, source, action) will update the page to reflect notification status changes.
         *
         * source is either "localStorage" or "fetcher"
         *
         * action is either "notification-received" or "notification-noticed    "
         */
        updater: null,

        /**
         * Callback to determine if notification data has changed since the last fetch.
         * Data is passed as is from the fetcher.
         *
         * @type {Function} hasChanged(oldData, newData)
         */
        hasChanged: null,

        /**
         * Callback to show external notifications outside browser window.
         */
        showExternalNotifications: null,

        /**
         * Under which key store our data in localStroage
         */
        localStorageKey: "notifications",


        /**
         * localStorage key determining should audio events be played or not.
         *
         * "on" or "off", default "on" behavior
         */
        audioStateKey: "notifications-audio",

        /**
         * Output console messages
         * @type {Boolean}
         */
        debug: false

    };

    // Log output wrapper
    function log() {
        if(window.console && config.debug) {
            var args = Array.prototype.slice.call(arguments, 0);
            window.console.log.apply(console, args);
        }
    }

    /**
     * Post a notification event to other windows/tabs.
     *
     * @param {String} action "notification-fetch-started", "notification-noticed", "notification-received"
     *
     * @param {Object} data directly passed to config callbacks or null.
     *
     * @param {Boolean} local Send event to this page itself too
     *
     * @param {Boolean} silent This notification should not trigger any visual or audible events
     */
    function sendNotificationEvent(action, data, local, silent) {

        var evt = {
            action: action,
            data: data,
            silent: silent,
            timestamp: new Date()
        };

        window.localStorage[config.localStorageKey] = JSON.stringify(evt);

        if(local) {
            onNotificationEvent(evt, "local");
        }
    }

    /**
     * Update the window content with new notifications.
     *
     *
     * This handler can be be triggered through
     *
     * - The page sends "notification-noticed" event to other tabs on page load (localStorage)
     *
     * - Poller fetch() returns new data and the tab who did the polling
     *   delegates it across tabs (localStorage)
     *
     * - Poller fetch() returns new data and updates the page itself (fetcher)
     *
     * - Page becomes visible, signals other windows to stop flashing (localStorage)
     *
     * @param  {Object} notificationPayload {action, data, timestamp} - see sendNotificationEvent()
     *
     * @param {String} source either "localStorage" or "local"
     */
    function onNotificationEvent(notificationPayload, source) {

        // Other tab has started fetching new data,
        // reset us
        if(notificationPayload.action == "notification-fetch-started") {
            resetPoller();
            return;
        }

        // Some other tab has been opened, clear attention needed flag
        if(notificationPayload.action == "notification-noticed") {
            seekAttention(false);
            return;
        }

        // Check if we need to update the DOM, or did we already updated it before
        // (race conditions, etc...)
        if(!notificationPayload.data) {
            return;
        }

        // Check if the notification data has chagned
        if(currentNotificationData) {
            // currentNotificationData is null on the virgin payload
            // so let us pass always through this check,
            // so that the page load can fire "notification-received"
            // to populate initial notification data.
            if(!config.hasChanged(currentNotificationData, notificationPayload.data)) {
                log("Notification contents still the same");
                return;
            } else {
                log("Updating notification list on the page");
            }
        }

        // Tell our customer app that here comes the payload
        config.updater(notificationPayload.data, source, notificationPayload.action);

        currentNotificationData = notificationPayload.data;

        // Turn on the blinker
        if(document.hidden && !notificationPayload.silent) {
            seekAttention(true);
        } else {
            // We are visible. Override the previous event (notification-received)
            // and inform other tabs that they should stop blinking.
            noticeNotifications();
        }

    }

    /**
     * Start/restart the notification data fetcher polling
     */
    function resetPoller() {

        var timeout = config.interval + Math.random() * config.variance;
        log("Restarting notification poller, timeout is ", timeout);

        function poll() {
            log("Notification fetch start");
            sendNotificationEvent("notification-fetch-started");
            var result = config.fetcher(onFetchedData);
            resetPoller();
        }

        if(poller) {
            window.clearTimeout(poller);
            poller = null;
        }

        // Add some variance, so that all tabs don't start fetcher at the same moment
        if(!finished) {
            poller = window.setTimeout(poll, timeout);
        } else {
            log("End polling has been requested by the server.")
        }
    }

    /**
     * Reflect the fetched notification data across all tabs.
     *
     * @param {Object} data The currently stored notification data
     * @param {Boolean} silent Set to true if you want to avoid notification alarm (e.g. no new notifications, but all notifications cleared)
     * @param {Boolean} silent Set to true if you want to stop the polling (server responded the session has timed out).
     */
    function onFetchedData(data, silent, stop) {

        if(stop) {
            log("Polling stop requested");
            finished = true;
            return;
        }

        // Check if the current notification data is already up-to-date
        if(!config.hasChanged(currentNotificationData, data)) {
            // Already up-to-date
            return;
        }

        if (config.showExternalNotifications) {
            config.showExternalNotifications(currentNotificationData, data);
        }

        // Inform other tabs we have new data
        sendNotificationEvent("notification-received", data, true, silent);

        if(!silent) {
            ping();
        }
    }

    /**
     * Signal all tab/windows that the user has now focus and knows there are notifications.
     *
     * Post on all tabs one was actually visible.
     */
    function noticeNotifications() {
        sendNotificationEvent("notification-noticed", null);
    }

    /**
     * Start blinking the page favicon if we are inactive.
     *
     * NOTE: Chrome does not seem to dynamic updating of favicons with .ico format only.
     *
     * https://developer.mozilla.org/en-US/docs/Web/Guide/User_experience/Using_the_Page_Visibility_API
     *
     * @param {Boolean} state Turn blinking on or off
     */
    function seekAttention(state) {

        // Start interval timer switching between
        // two favicons
        var blinkOn = false;
        var head = $("head");

        // Do this only if both icons are present
        if(!favicon.length || !faviconBlink.length) {
            return;
        }

        // On every state change reset interval
        if(blinker) {
            window.clearInterval(blinker);
            blinker = null;
        }

        // We have turned off the linker
        if(!state) {
            // Restore favicon state
            log("Turning off blinker");
            head.find("link[rel=icon]").remove();
            head.append(favicon);
            window.clearInterval(blinker);
            return;
        }

        // The page is not visible or visibility API is not supported
        if(!document.hidden) {
            // Start attention seeking only on hidden windows / tabs
            return;
        }

        log("Turning on blinker");

        // Alternate between two favicons
        function blink() {

            head.find("link[rel=icon]").remove();
            faviconBlink.attr("rel", "icon");

            if(blinkOn) {
                head.append(favicon);
                blinkOn = false;
            } else {
                head.append(faviconBlink);
                blinkOn = true;
            }
        }

        blinker = window.setInterval(blink, 230);
    }

    /**
     * Cause an audible feedback for the user to know they should return to their browser.
     */
    function ping() {

        // Audio notifications are off by users
        if(window.localStorage[config.audioStateKey] == "off") {
            return;
        }

        var audio = document.getElementById("notification-tone");

        // audio.play not provided by old IEs
        if(audio && audio.play) {
            // Cannot reliable replay HTML5 audio element without reloading it,
            // so make sure your static assets are cached properly
            // http://stackoverflow.com/a/7005562/31516
            audio.load();
            audio.play();
        }
    }

    /**
     * Event handlers on each tab needed for interaction.
     */
    function installEventHandlers() {

        // *Other* windows post storage event when localStorage is modified
        $(window).on("storage", function(evt) {

            if(evt.originalEvent.key != config.localStorageKey) {
                // Somebody else is modifying localStorage, not us
                return;
            }
            // Parse the payload we use to communite cross-window
            var payload = JSON.parse(evt.originalEvent.newValue);
            onNotificationEvent(payload, "localStorage");
        });

        // Check that if we need to clear attention seeking when
        // the user switchs back to this window/tab
        $(document).on("visibilitychange", function() {
            if(blinker) {
                noticeNotifications();
                seekAttention(false);
            }
        });
    }

    /**
     * Exports
     */
    window.notifications = {

        /**
         * Start notification system. Call on window onload.
         */
        init: function(_config) {

            // Old IE
            if(!window.localStorage) {
                return;
            }

            config = $.extend({}, config, _config);
            installEventHandlers();

            if(!config.interval || !config.variance) {
                throw new Error("Notification poller interval and variance must be configured");
            }

            resetPoller();
        },

        /**
         * Send notification event.
         *
         * You can use this e.g. on the page load to tell other tabs to stop blinking.
         */
        trigger: function(action, data, local) {
            sendNotificationEvent(action, data, local);
        },

        /**
         * Control audio feedback (the user might want to mute).
         *
         * @param {[type]} state [description]
         */
        setAudible: function(state) {
            window.localStorage[config.audioStateKey] = state ? "on" : "off";
        },

        getAudible: function() {
            return window.localStorage[config.audioStateKey] != "off";
        }
    };


})(jQuery);