jQuery(function($) {
    var thumb = $('.form-row.file .thumbnail');
    if (thumb.length) {

        var focalPoint = $('<span class="focal-point" />');
        var img = $('img', thumb);
        var imgW = img.attr('width');
        var imgH = img.attr('height');
        var container = $('<span class="focal-point-container" />');
        container.append(focalPoint);
        thumb.append(container);

        var focalPointW = focalPoint.outerWidth();
        var focalPointH = focalPoint.outerHeight();
        var inputX = $('#id_focal_x');
        var inputY = $('#id_focal_y');
        var defaultX = .5;
        var defaultY = .5;
        container.width(imgW + focalPointW);
        container.height(imgH + focalPointH);
        container.css('left', -focalPointW / 2);
        container.css('top', -focalPointH / 2);

        focalPoint.setPosition = function(x, y) {
            $(this).css('left', x * imgW);
            $(this).css('top', y * imgH);
        }

        focalPoint.getPosition = function(decimals) {
            var x = focalPoint.position().left / imgW;
            var y = focalPoint.position().top / imgH;
            x = Math.min(1, Math.max(0, x));
            y = Math.min(1, Math.max(0, y));
            if (decimals) {
                var r = Math.pow(10, decimals);
                x = Math.round(x * r) / r;
                y = Math.round(y * r) / r;
            }
            return {x: x, y: y};
        }

        focalPoint.setPositionToInput = function() {
            var x = inputX.val().replace(/[^0-9\.]/g, '');
            var y = inputY.val().replace(/[^0-9\.]/g, '');
            var emptyX = x == '';
            var emptyY = y == '';
            if (emptyX) x = defaultX; else x = parseFloat(x);
            if (emptyY) y = defaultY; else y = parseFloat(y);
            x = Math.min(1, Math.max(0, x));
            y = Math.min(1, Math.max(0, y));
            if (!emptyX) inputX.val(x);
            if (!emptyY) inputY.val(y);
            focalPoint.setPosition(x, y);
        }
        
        focalPoint.draggable({
            containment: 'parent'
            ,drag: function() {
                pos = focalPoint.getPosition(3);
                inputX.val(pos.x);
                inputY.val(pos.y);
            }
        });
        
        inputX.change(focalPoint.setPositionToInput);
        inputY.change(focalPoint.setPositionToInput);
        
        focalPoint.setPositionToInput();

        var fieldset = inputX.closest('fieldset');
        if (fieldset.hasClass('collapsed')) {
            focalPoint.hide();
        }

        fieldset.find('.collapse-toggle').click(function() {
            focalPoint.toggle();
        });
    }

});
