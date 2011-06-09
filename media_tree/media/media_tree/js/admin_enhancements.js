jQuery(function($) {

    $.makeChangelistRow = function(cols, row)
    {
        if ($('#changelist table').length == 0) {
            var table = $('<table cellspacing="0"><thead><th>&nbsp;</th><th>'+gettext('Name')+'</th><th>'+gettext('Size')+'</th></table>')
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
        $('#changelist').delegate('input[name=_selected_action]', 'change', function() {
            $('.popup-select-button')[0].disabled = 
                $('#changelist input[name=_selected_action]:checked').length == 0;
        });
        $('.popup-select-button').click(function() {
            var selectedId = $('#changelist input[name=_selected_action]:checked').val();
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

    /**
    Adds child rows after a row (which are actually just indented rows sitting
    underneath it), and adds keeps track of them for later removal.
    */
    $.fn.addExpandedChildren = function(rows, appendAfter) {
        if (appendAfter == null || appendAfter) {
            $(this).after(rows);
        }
        var expandedChildren = $(this).data('expandedChildren');
        if (!expandedChildren) {
            expandedChildren = [];
        }
        for (var i = 0; i < rows.length; i++) {
            expandedChildren.push(rows[i]);
        }
        $(this).data('expandedChildren', expandedChildren);
    };

    /**
    Recursively removes all of a row's expanded child rows (which are actually
    just indented rows sitting underneath it).
    */
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

    $.fn.selectChangelistRow = function() {
        $('input[name=_selected_action]', this)[0].checked = true;
        $(this).addClass('selected');
    };

    $.fn.getFirstSelectedFolder = function() 
    {
        var checked = $('#changelist input[name=_selected_action]:checked');
        if (checked) {
            for (var i = 0; i < checked.length; i++) {
                var row = $(checked[i]).closest('tr');
                if (row.find('.folder').length) {
                    return {
                        id: checked.val(),
                        name: $(checked[i]).closest('tr').find('.name').text()
                    };
                }
            }
        }
    }    
    
    $.fn.updateChangelist = function(html) {
        // Store checked rows
        var checked = $('input[name=_selected_action]:checked', this);
        // Update list
        $(this).html(html);
        $(this).trigger('init');
        // Django calls actions() when document ready. Since the ChangeList is 
        // updated here, it needs to be called again
        django.jQuery("tr input.action-select").actions();
        // Restore checked rows
        var _this = this;
        checked.each(function() {
            $('input[value='+this.value+']', _this).closest('tr').selectChangelistRow();
        });
    }
        

    // TODO: Move actions() call, row coloring etc inside this function
    $('#changelist').bind('init', function(scope) {
        var rows = [];
        $('tr', this).each(function() {
            var id = $(this).find('input[name=_selected_action]').val();
            rows[parseInt(id)] = $(this);
        });
        
        $('a[rel^=parent]', this).each(function() {
            var rel = $(this).attr('rel').split(':');
            if (rel.length == 2) {
                var parentRow = rows[parseInt(rel[1])];
                var row = $(this).closest('tr')[0];
                if (parentRow) {
                    parentRow.addExpandedChildren([row], false);
                }
            }
        });
        
        $(this).trigger('update');
    });

    $('#changelist').bind('update', function() {
        $('tbody tr', this).each(function(index) {
            $(this).removeClass('row1 row2');
            if (index % 2) {
                $(this).addClass('row2');
            } else {
                $(this).addClass('row1');
            }
        });
    });
    
    $('#changelist').trigger('init');
    
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
                parentRow.addExpandedChildren(rows);
                $('#changelist').trigger('update');
            });
        } else {
            parentRow.data('isExpanded', false);
            button.removeClass('loading expanded');
            button.addClass('collapsed');
            folder.removeClass('expanded');
            folder.addClass('collapsed');
            parentRow.closeExpandedChildren();
            $('#changelist').trigger('update');
            
            var closedFolderId = parseInt(href.split('=')[1]);
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
                $.cookie('expanded_folders_pk', newCookie, {path: '/', raw: true});
            }
        }
        return false;
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
