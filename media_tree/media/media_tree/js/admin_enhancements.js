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
    
    $.getSelectedFolder = function() 
    {
        var checked = $('#changelist input[name=_selected_action]:checked');
        if (checked) {
            var row = $(checked[0]).closest('tr');
            if (row.find('.folder').length) {
                return {
                    id: checked.val(),
                    name: $(checked[0]).closest('tr').find('.name').text()
                };
            }
        }
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
                $(expandedChildren).closeExpandedChildren();
                $(expandedChildren).remove();
                $(this).data('expandedChildren', null);
            }
        }); 
    };

    $.fn.addExpandedChildren = function(rows) {
        var expandedChildren = $(this).data('expandedChildren');
        if (!expandedChildren) {
            expandedChildren = [];
        }
        for (var i = 0; i < rows.length; i++) {
            expandedChildren.push(rows[i]);
        }
        $(this).data('expandedChildren', expandedChildren);
    };

    // TODO: Move actions() call, row coloring etc inside this function
    $.initChangelistFolders = function(scope)
    {
        var rows = [];
        $('#changelist tr', scope).each(function() {
            var id = $(this).find('input[name=_selected_action]').val();
            rows[parseInt(id)] = $(this);
        });

        $('#changelist', scope).find('a[rel^=parent]').each(function() {
            var rel = $(this).attr('rel').split(':');
            if (rel.length == 2) {
                var parentRow = rows[parseInt(rel[1])];
                var row = $(this).closest('tr')[0];
                if (parentRow) {
                    parentRow.addExpandedChildren([row]);
                }
            }
        });
    }
    
    $.initChangelistFolders();
    
    $('#changelist').delegate('.folder-toggle, .browse-controls a', 'click', function(event) {
        var button = $(this).closest('tr').find('.folder-toggle');
        if (button.length && button.is('.dummy.empty')) return false;
        if (!button.length || button.is('.dummy')) return;
        var folder = button.closest('.browse-controls').find('a.folder');
        var parentRow = button.closest('tr');
        //var isExpanded = parentRow.data('isExpanded');
        var isExpanded = button.is('.expanded, .loading');
        var href = button.attr('href');
        if (!isExpanded) {
            //parentRow.data('isExpanded', true);
            button.removeClass('collapsed');
            button.addClass('loading');
            $.get(href, function(data) {
                //if (!parentRow.data('isExpanded')) return;
                if (!button.is('.loading')) return;
                button.removeClass('loading collapsed');
                button.addClass('expanded');
                folder.removeClass('collapsed');
                folder.addClass('expanded');
                var tbody = $(data).find('#changelist tbody');
                // TODO: yellow selection is enabled, but elements are not POSTed when executing action
                django.jQuery("tr input.action-select", django.jQuery(tbody)).actions();
                var rows =  $('tr', tbody);
                parentRow.after(rows);
                parentRow.addExpandedChildren(rows);
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
            folder.removeClass('expanded');
            folder.addClass('collapsed');
            parentRow.closeExpandedChildren();
            
            var closedFolderId = parseInt(href.split('=')[1]);
            console.log('closed = '+closedFolderId);
            var cookie = $.cookie('expanded_folders_pk');
            var newCookie = '';
            if (cookie) {
                var split = cookie.split('|');
                for (var i = 0; i < split.length; i++) {
                    if (parseInt(split[i]) != closedFolderId) {
                        if (newCookie != '') {
                            newCookie += '|';
                        }
                        newCookie += split[i];
                    }
                }
                console.log('old cookie = '+cookie);
                console.log('new cookie = '+newCookie);
                $.cookie('expanded_folders_pk', newCookie, {path: '/', raw: true});
                console.log($.cookie('expanded_folders_pk'));
            }
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
