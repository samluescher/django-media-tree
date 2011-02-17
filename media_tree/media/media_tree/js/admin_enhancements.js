jQuery(function($) {
    $.makeChangelistRow = function(cols, row)
    {
        if ($('#changelist table').length == 0) {
            var table = $('<table cellspacing="0"><thead><th>&nbsp;</th><th>&nbsp;</th><th>'+gettext('Name')+'</th><th>'+gettext('Size')+'</th></table>')
            var tbody = $('<tbody></tbody>');
            table.append(tbody);
            $('#changelist').append(table);
        }
        
        var colCount = $('#changelist table').find('thead').find('th').length;
        if (row == null) {
            row = $('<tr class="row1"></tr>');
        }

        for (var i = 0; i < colCount; i++) {
            if (i < cols.length && cols[i] != null) {
                row.append(cols[i]);
            } else {
                row.append($('<td>&nbsp;</td>'));
            }
        }

        return row;
    }

    $('#object-tool-add-folder').click(function(event) {
        event.preventDefault();
        if ($('#add-folder-name').length == 0) {
            var cols = []
            cols[2] = $('<td><form action="add_folder/" method="POST">'
                +'<span style="white-space: nowrap;"><input type="text" id="add-folder-name" name="name" value="'+gettext('New folder')+'"/>'
                +'&nbsp;<input type="submit" class="button" value="'+gettext('Save')+'" /></span>'
                +'<input type="hidden" name="csrfmiddlewaretoken" />'
                +'</form></td>');
            cols[2].find('input[name=csrfmiddlewaretoken]').val($('input[name=csrfmiddlewaretoken]').val())
            var row = $.makeChangelistRow(cols);
            $('#changelist table tbody').prepend(row);
        }
        $('#add-folder-name').select().focus();
    });
    
    if (document.location.href.indexOf('pop=1') != -1) {
        $('#changelist input[type=checkbox]').change(function() {
            if (this.checked) {
                //console.log('selected '+$(this).val());
            }
        });
        $('#popup-button-select').click(function() {
            var selectedId = $('#changelist input[type=checkbox]:checked').val();
            if (selectedId) {
                opener.dismissRelatedLookupPopup(window, selectedId); 
            }
            return false;
        });
        $('a[onclick^=opener]').each(function() {
            this.onclick = false;
            $(this).click(function() {
                var href = $(this).attr('href');
                var querySplit = document.location.href.split('?');
                querySplit[0] = href;
                window.location.href = querySplit.join('?');
                return false;
            });
        });
    }

    // Removes all expanded "child" rows of a row, recursively
    $.fn.closeExpandedChildren = function() {
        $(this).each(function() {
            var expandedChildren = $(this).data('expandedChildren');
            if (expandedChildren) {
                expandedChildren.closeExpandedChildren();
                expandedChildren.remove();
                $(this).data('expandedChildren', null);
            }
        }); 
    }

    $('#changelist').delegate('.folder-toggle, a', 'click', function(event) {
        var button = $(this).closest('tr').find('.folder-toggle');
        if (!button.length || button.is('.dummy')) return;
        var parentRow = button.closest('tr');
        var isExpanded = parentRow.data('isExpanded');
        if (!isExpanded) {
            parentRow.data('isExpanded', true);
            button.removeClass('collapsed');
            button.addClass('loading');
            $.get(button.attr('href'), function(data) {
                if (!parentRow.data('isExpanded')) return;
                button.removeClass('loading collapsed');
                button.addClass('expanded');
                var tbody = $(data).find('#changelist tbody');
                // TODO: yellow selection is enabled, but elements are not POSTed when executing action
                django.jQuery("tr input.action-select", django.jQuery(tbody)).actions();
                var rows =  $('tr', tbody);
                parentRow.after(rows);
                parentRow.data('expandedChildren', rows);
                $('#changelist tbody tr').each(function(index) {
                    $(this).removeClass('row1 row2');
                    if (index % 2) {
                        $(this).addClass('row2');
                    } else {
                        $(this).addClass('row1');
                    }
                });
            });
        } else {
            parentRow.data('isExpanded', false);
            button.removeClass('loading expanded');
            button.addClass('collapsed');
            parentRow.closeExpandedChildren();
        }
        return false;
    });
    
    $('#changelist tbody tr').draggable({
        //revert: true
        opacity: .5
        //,placeholder: "ui-state-highlight"
    });


    
    
    // TODO: Move to media extender
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
            var x = inputX.val();
            var y = inputY.val();
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
        
        /*focalPoint.hide();
        container.mouseenter(function() { 
            focalPoint.show();
        });
        container.mouseleave(function() { 
            focalPoint.hide();
        });*/
    }

});
