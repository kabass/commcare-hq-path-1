hqDefine("domain/js/manage_alerts",[
    'jquery',
    'hqwebapp/js/initial_page_data',
], function ($, initialPageData) {
    $(function () {
        $('#ko-alert-container').koApplyBindings({
            'alerts': initialPageData.get('alerts'),
        });
    });
});
