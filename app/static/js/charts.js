$('document').ready(function() {
    'use strict';

    function chartInit() {
        $('.charts > .chart').each(function() {
            var $header = $(this).find('.chart-header'),
                $content = $(this).find('.chart-content');
            $header.click(function() {
                if ($content.is(':visible')) {
                    $content.hide();
                } else {
                    $content.show();
                }
            });
        });
    }

    function init() {
        chartInit();
    }

    init();
});