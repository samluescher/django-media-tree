django.jQuery(function($) {
    $('.FileNodeForeignKeyRawIdWidget').delegate('.preview, .name', 'click', function() {
        $(this).closest('.FileNodeForeignKeyRawIdWidget').find('.related-lookup').trigger('click');
    });
});
