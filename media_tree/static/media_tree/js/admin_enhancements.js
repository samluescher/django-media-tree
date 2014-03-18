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

    var makeForm = function(action, hiddenFields) {
        if (!hiddenFields) {
            hiddenFields = {};
        }
        hiddenFields['csrfmiddlewaretoken'] = $('input[name=csrfmiddlewaretoken]').val();
        hiddenHtml = '';
        for (key in hiddenFields) {
            hiddenHtml += '<input type="hidden" name="' + key + '" value="' + hiddenFields[key] + '" />';
        }
        return $( 
            '<form action="' + action + '" method="POST">'
                +'<div style="display: none">' + hiddenHtml + '</div>'
            +'</form>');
    };
    
    $('#object-tool-add-folder').click(function(event) {
        event.preventDefault();
        if ($('#add-folder-row').length) {
            $('#add-folder-row').remove();
        }
        
        var cols = [];
        var targetFolder = $('#changelist').data('targetFolder');
        
        cols[1] = $(
            '<td></td>'
        );

        var form = makeForm($('#object-tool-add-folder').attr('href'));
        form.attr('class', 'add-folder');
        form.append(
            '<a class="folder-toggle dummy" rel="%s">&nbsp;</a><span style="white-space: nowrap;"><input type="text" id="add-folder-name" name="name" value="'+gettext('New folder')+'"/>'
            +'&nbsp;<input type="submit" class="button default" value="'+gettext('Save')+'" />'
            +'&nbsp;<input type="submit" class="button cancel" value="'+gettext('Cancel')+'" /></span>'
            +'<input type="hidden" name="parent" value="' + (targetFolder ? targetFolder.id : '') + '" />'
            +(targetFolder ? '<input type="hidden" name="folder_id" value="' + targetFolder.id + '" />' : '')
        );

        cols[1].append(form);
        
        if (targetFolder && targetFolder.row) {
            // TODO: Copy padding, but add indent
            cols[1].css('padding-left', 
                $($('td', targetFolder.row)[1]).css('padding-left'));
        }
        
        var row = $.makeChangelistRow(cols, null, targetFolder ? targetFolder.row : null);
        row.attr('id', 'add-folder-row');
        
        if (targetFolder && targetFolder.row) {
            $(targetFolder.row).after(row);
        } else {
            $('#changelist table tbody').prepend(row);
        }

        $('#add-folder-name').select().focus();
        $('.button.cancel', form).on('click', function() {
            row.remove();
            return false;
        });
        $(form).on('keyup', function(evt) {
            if (evt.keyCode == 27) {
                row.remove();
                return false;
            }
        });
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
    underneath it), and keeps track of them for later removal.
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
                $(this).data('expandedChildren', null);
                $(expandedChildren).closeExpandedChildren();
                $(expandedChildren).remove();

                /*$(expandedChildren).fadeOut('fast', function() {
                    $(this).remove();
                });*/
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

    var dragHelper, draggedItem;
    
    $.fn.updateChangelist = function(html, restoreSelected) {
        if (draggedItem) {
            // TODO: This does not work. If the user is dragging while changelist is replaced,
            // there will be JS errors.
            $(draggedItem).draggable('destroy');
        }
        if (dragHelper) {
            $(dragHelper).remove();
            dragHelper = null;
        }

        // Store checked rows
        var checked = $('input[name=_selected_action]:checked', this);
        // Update list
        $(this).html(html);
        $(this).trigger('init');
        // Restore checked rows
        var _this = this;
        if (restoreSelected == null || restoreSelected) {
            checked.each(function() {
                var tr = $('input[value='+this.value+']', _this).closest('tr');
                tr.selectChangelistRow();
            });
        }
    }

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
        
        $(this).trigger('update', [$('tr', this), true]);
    });

    $.fn.setUpdateReq = function(req) {
        $(this).abortUpdateReq();
        $(this).data('updateReq', req);
    };

    $.fn.abortUpdateReq = function(req) {
        var req = $(this).data('updateReq');
        if (req) {
            req.abort();
        }
    };

    $.addUserMessage = function(messageText, messageId, messageClass) {
        if (!messageClass) {
            messageClass = 'info';
        }
        var defaultMessageId = 'default-message';
        if (!messageId) {
            messageId = defaultMessageId;
        }
        $('#' + defaultMessageId).remove();
        var message = $('<li id="'+messageId+'" class="' + messageClass + '">'+messageText+'</li>')
        var currentMessage = $('#'+messageId);
        if (currentMessage.length > 0) {
            currentMessage.replaceWith(message);
        } else {
            var messageList = $('ul.messagelist');
            if (messageList.length == 0) {
                $('#content').before('<ul class="messagelist"></ul>');
                var messageList = $('ul.messagelist');
            }
            messageList.append(message);
        }
    }

    $('#changelist').bind('update', function(e, updatedRows, isInitial) {
        var _changelist = this;

        // Django calls actions() when document ready. Since the ChangeList  
        // was updated, actions() needs to be called again:
        django.jQuery("tr input.action-select").actions();

        var rows = $('tbody tr', this);
        rows.each(function(index) {
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

        // Set up drag & drop

        var rowSelectInputName = '_selected_action';
        var rowSelectInputSel = 'input[name=' + rowSelectInputName + ']';
        var rowSel = '#changelist tbody tr';
        var tableSel = '#changelist table';
        var rootDroppable;
        var dragDropScope = 'drag-filenode';

        var getDropTargetId = function(droppable) {
            if (droppable != rootDroppable) {
                var node = $('.node', droppable);
                if (node.is('.folder')) {
                    // drop on folder
                    return $(rowSelectInputSel, droppable).val();
                } else {
                    // drop next to sibling
                    return node.attr('data-parentid');
                }
            } else {
                // drop on root
                return '';
            }
        };

        var getSelectedCheckboxes = function() {
            return $(rowSelectInputSel + ':checked', _changelist);
        };

        var initDroppable = function(target, loaderTarget) {
            return $(target).droppable({
                drop: function(event, ui) {
                    dragHelper = null;
                    draggedItem = null;
                    var targetId = getDropTargetId(this);

                    var action = $(ui.draggable).data('copyDrag') ? 'copy_selected' : 'move_selected';
                    var fields = {
                        action: action,
                        target_node: targetId,
                        execute: 1
                    };

                    var form = makeForm('', fields);
                    var selected = getSelectedCheckboxes();
                    form.append(selected.clone()); 
                    
                    //form.submit();
                    
                    //return;
                    // instead:
                    if (!loaderTarget) {
                        loaderTarget = $('#node-'+targetId).closest('tr');
                    }
                    loaderTarget.addClass('loading');

                    $(_changelist).setUpdateReq($.ajax({
                        type: 'post',
                        data: form.serialize(),  
                        success: function(data) {
                            loaderTarget.removeClass('loading');
                            var newChangelist = $(data).find('#changelist');
                            if (newChangelist.length) {
                                // update table
                                $(_changelist).updateChangelist(newChangelist.html(), false);
                                // display messages
                                $('.messagelist li', data).each(function() {
                                    $.addUserMessage($(this).text(), null, this.className);
                                });
                            } else {
                                // if the result is no changelist, the form did not validate.
                                // display error messages:
                                $('fieldset .errorlist li', data).each(function() {
                                    $.addUserMessage($(this).text(), null, 'error');
                                });
                            }
                        }, 
                        error: function() {
                            loaderTarget.removeClass('loading');
                        }  
                    }));
                    
                    return false;      
                },
                scope: dragDropScope,
                hoverClass: function() {
                    return $('.node', this).is('.folder') ?
                        'drop-parent' : 'drop-sibling';
                },
                greedy: true,
                accept: function(draggable) {
                    // TODO: currently when trying to drop on self the item will be
                    // moved to root. This is only partially solved by setting the
                    // draggables distance to half its height.
                    var result = true,
                        targetId = getDropTargetId(this);
                    getSelectedCheckboxes().each(function(index, input) {
                        var nodeId = $(input).val(),
                            parentId = $('#node-' + nodeId).attr('data-parentid');
                        if (parentId == targetId) {
                            result = false;
                        }
                    });
                    return result;
                }
            });
        };

        // Init dropping on root.
        // TODO: We can not use the table itself as droppable, since that would 
        // accept a dragged row even when that row is dropped on itself (or actually
        // the table, since jQuery prevents dropping on self and then propagates the
        // event up the the table if the table is a droppable).
        // Solution for now: The thead is the root droppable.
        rootDroppable = initDroppable($('table', _changelist), $(_changelist))[0];

        $(rowSel).each(function() {
            $(this).draggable({
                distance: $(this).outerHeight() / 2,
                stop: function(event, ui) {
                    if ($(this).data('deselectAfterDrop')) {
                        $(this).data('deselectAfterDrop', false);
                        $(rowSelectInputSel, this).trigger('click');
                    }
                },
                helper: function(event, ui) {
                    // select dragged item
                    if (!$(rowSelectInputSel, this).is(':checked')) {
                        $(this).data('deselectAfterDrop', true);
                        $(rowSelectInputSel, this).trigger('click');
                    }
                    var selected = $(rowSelectInputSel + ':checked', _changelist);
                    var selectedCount = selected.length;

                    var copyDrag = event.altKey;
                    $(this).data('copyDrag', copyDrag);
                    var helper = $(
                        '<div class="drag-helper-wrapper"><div class="drag-helper collapsed' + (copyDrag ? ' copy' : '') + '">'
                        + '<table><tr><td></td></tr></table>'
                        + '</div></div>');
                    var nodeLink = $(this).closest('tr').find('.node-link');
                    $('td', helper).append(nodeLink.clone());

                    
                    if (selectedCount > 1) {
                        var counter = '<span class="drag-counter">' + selectedCount
                            + '</span>';
                        $('td', helper).prepend(counter);
                    }
                    

                    var handleOffset = nodeLink.position().left+'px';
                    $(helper).css('padding-left', handleOffset);
                    $(helper).css('padding-right', handleOffset);

                    dragHelper = helper;
                    draggedItem = this;

                    return helper;
                },
                scope: dragDropScope,
                opacity: .9,
                handle: '.node-link',
                appendTo: 'body',
                delay: 200
            }).disableSelection();

            initDroppable(this);
        });

        if (!isInitial) {
            /*$('#changelist .paginator').text(ngettext('%i media object',
                '%i media objects', rows.length).replace('%i', rows.length));*/
            // Look for text node containing numbers displaying current number of rows, and update with current number.
            $('#changelist .paginator, #changelist-search .small.quiet').contents().each(function() {
                if (this.nodeType == 3 && this.nodeValue.match('[0-9]')) {
                    pat = /([^\s()]+\s*)*[0-9]+(\s*[^\s()]+)*/
                    this.nodeValue = this.nodeValue.replace(pat, ngettext('%i media object',
                        '%i media objects', rows.length).replace('%i', rows.length));
                }
            });
        }

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
            $.ajax({
                url: href, 
                success: function(data) {
                    //if (!parentRow.data('isExpanded')) return;
                    if (!controls.is('.loading')) return;
                    controls.removeClass('loading');
                    controls.addClass('expanded');
                    controls.removeClass('collapsed');
                    var tbody = $(data).find('#changelist tbody');
                    var rows =  $('tr', tbody);
                    if (rows.length > 0) {
                        button.removeClass('empty');
                    } else {
                        button.addClass('empty');
                    }
                    parentRow.addExpandedChildren(rows);
                    $('#changelist').trigger('update', [rows]);
                },
                error: function() {
                    controls.removeClass('loading');
                }
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

    // Prebuffer background images
    var bufferBackgroundElements = $('<div class="loading"><div class="folder-toggle" /></div>');
    bufferBackgroundElements.hide();
    $('body').append(bufferBackgroundElements);
    $('*', bufferBackgroundElements).each(function() {
        var matchUrl = $(this).css('background-image').match(/url\((.*)\)/);
        var img = new Image();
        img.src = matchUrl[1];
    });
    bufferBackgroundElements.remove();

});
