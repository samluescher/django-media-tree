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
        if ($('#add-folder-row').length) {
            $('#add-folder-row').remove();
        }
        
        var cols = [];
        var targetFolder = $('#changelist').getFirstSelectedFolder();
        
        cols[1] = $(
            '<td><form action="add_folder/" method="POST">'
                +'<span style="white-space: nowrap;"><input type="text" id="add-folder-name" name="name" value="'+gettext('New folder')+'"/>'
                +'&nbsp;<input type="submit" class="button" value="'+gettext('Save')+'" /></span>'
                +'<input type="hidden" name="csrfmiddlewaretoken" />'
                +(targetFolder ? '<input type="hidden" name="folder_id" value="' + targetFolder.id + '" />' : '')
            +'</form></td>'
        );
        
        cols[1].find('input[name=csrfmiddlewaretoken]').val($('input[name=csrfmiddlewaretoken]').val())
        
        if (targetFolder) {
            // TODO: Copy padding, but add indent
            cols[1].css('padding-left', 
                $($('td', targetFolder.row)[1]).css('padding-left'));
        }
        
        var row = $.makeChangelistRow(cols, null, targetFolder ? targetFolder.row : null);
        row.attr('id', 'add-folder-row');
        
        if (targetFolder) {
            $(targetFolder.row).after(row);
        } else {
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
                        name: $(checked[i]).closest('tr').find('.name').text(),
                        row: row[0]
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
        // Restore checked rows
        var _this = this;
        checked.each(function() {
            var tr = $('input[value='+this.value+']', _this).closest('tr');
            tr.selectChangelistRow();
        });
    }

    // TODO: Move actions() call, row coloring etc inside this function
    $('#changelist').bind('init', function(scope) {
        console.log('init');
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
        
        $(this).trigger('update', [$('tr', this)]);
    });

    $('#changelist').bind('update', function(e, updatedRows) {
        // Django calls actions() when document ready. Since the ChangeList is 
        // updated here, it needs to be called again
        django.jQuery("tr input.action-select").actions();

        $('tbody tr', this).each(function(index) {
            if ($('input.action-select:checked', this).length) {
                $(this).selectChangelistRow();
            }
            $(this).removeClass('row1 row2');
            if (index % 2) {
                $(this).addClass('row2');
            } else {
                $(this).addClass('row1');
            }
        });
        
        if (updatedRows) {
            $(updatedRows).each(function() {
                var _row = this;
                $('.metadata-icon', _row).bind('click mouseenter mouseleave', function() {
                    if ($('.displayed-metadata', _row).text() != '') {
                        $('.displayed-metadata', _row).toggle();
                    }
                });
            });
        }
    });
    
    $('#changelist').trigger('init');
    
    $('#changelist').delegate('.folder-toggle, .browse-controls a', 'click', function(event) 
    {
        var button = $(this).closest('tr').find('.folder-toggle');
        var controls = $(this).closest('tr').find('.browse-controls')
        if (button.length && button.is('.dummy.empty')) return false;
        if (!button.length || button.is('.dummy')) return;
        var folder = button.closest('.browse-controls').find('a.folder');
        var parentRow = button.closest('tr');
        //var isExpanded = parentRow.data('isExpanded');
        var isExpanded = controls.is('.expanded, .loading');
        var href = button.attr('href');
        if (!isExpanded) {
            //parentRow.data('isExpanded', true);
            controls.addClass('loading');
            $.get(href, function(data) {
                //if (!parentRow.data('isExpanded')) return;
                if (!controls.is('.loading')) return;
                controls.removeClass('loading');
                controls.addClass('expanded');
                controls.removeClass('collapsed');
                var tbody = $(data).find('#changelist tbody');
                var rows =  $('tr', tbody);
                parentRow.addExpandedChildren(rows);
                $('#changelist').trigger('update', [rows]);
            });
        } else {
            parentRow.data('isExpanded', false);
            controls.removeClass('expanded');
            controls.addClass('collapsed');
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

});
