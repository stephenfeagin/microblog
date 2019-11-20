function translate(sourceElem, destElem, sourceLang, destLang) {
    $(destElem).html("<img src='{{ url_for("static", filename="img/loading.gif") }}'>");

    $.post("/translate", {
        text: $(sourceElem).text(),
        source_language: sourceLang,
        dest_language: destLang
    }).done(function(response) {
        $(destElem).html("<em>" + response["text"] + "</em>");
    }).fail(function() {
        $(destElem).text("{{ _('Error: Could not contact server') }}");
    });
}