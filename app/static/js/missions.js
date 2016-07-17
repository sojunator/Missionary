$('document').ready(function() {
    $('.mission-collapse').click(function() {
        $content = $(this).parent().parent().next();
        if ($content.is(":visible")) {
            $content.hide();
        } else {
            $content.show();
        }
    });
});