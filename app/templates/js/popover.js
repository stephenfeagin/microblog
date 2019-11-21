// app/templates/js/popover.js
$(function() {
    $(".user_popup").hover(
        function(event) {
            // mouse in event handler
            var elem = $(event.currentTarget);
        },
        function(event) {
            // mouse out event handler
            var elem = $(event.currentTarget);
        }
    )
});

$(function() {
    // hover delay
    var timer = null;
    var xhr = null;
    $(".user_popup").hover(
        function(event) {
            // mouse in event handler
            var elem = $(event.currentTarget);
            timer = setTimeout(function() {
                timer = null;
                // popup logic
                xhr = $.ajax(
                        "/user/" + elem.first().text().trim() + "/popup"
                    ).done(function(data) {
                        xhr = null;
                        // create and display popup
                        elem.popover({
                            trigger: "manual",
                            html: true,
                            animation: false,
                            container: elem,
                            content: data
                        }).popover("show");
                        flask_moment_render_all();
                });
            }, 500);
        },
        function(event) {
            var elem = $(event.currentTarget);
            if (timer) {
                clearTimeout(timer);
                timer = null;
            } else if (xhr) {
                xhr.abort();
                xhr = null;
            } else {
                // destroy popup
                elem.popover("destroy");
            }
        }
    )
});