django.jQuery(function($) {
    $('.FileNodeForeignKeyRawIdWidget').delegate('.preview, .name', 'click', function() {
        $(this).closest('.FileNodeForeignKeyRawIdWidget').find('.related-lookup').trigger('click');
    });
    $('.FileNodeForeignKeyRawIdWidget').delegate('.clear-widget', 'click', function() {
        var $widget = $(this).closest('.FileNodeForeignKeyRawIdWidget');
        $widget.find('input').val('');
        $widget.find('.preview').empty();
        $widget.find('.name').empty();
        $(this).hide();
    });
});
