jQuery(function($) {

    var ROW_SELECTOR = '#changelist tbody tr',
        DRAG_HANDLE_SELECTOR = '.drag-handler',
        DRAG_DROP_SCOPE = 'media_tree',
        EXPAND_COLLAPSE_SELECTOR = '.collapse';

    var isFolder = function(row) {
        return $('.meta', row).attr('type') === 'folder';
    };

    var pendingRequests = [];

    var initChangeListResults = function(rows) {
        $(rows).each(function() {
            var $this = $(this);

            // TODO: initially, we remove the expanded attribute from all nodes with
            // the following hack, and replace it with the collapsed attribute. This
            // is necessary since treebeard's `admin_tree` template tags will assume
            // that the tree is fully expanded, but media_tree's MediaTreeChangeList
            // actually returns collapsed results. This hack should be replaced with
            // proper solution that is contributed back to the treebeard project.
            $this.find('a.collapse.expanded').each(function() {
                $(this).removeClass('expanded').addClass('collapsed');
            });

            // Init draggable
            $this.draggable({
                distance: $(this).outerHeight() / 2,
                stop: function(event, ui) {
                    if ($(this).data('deselectAfterDrop')) {
                        $(this).data('deselectAfterDrop', false);
                        $(rowSelectInputSel, this).trigger('click');
                    }
                },
                helper: function(event, ui) {
                    var $helper = $(
                        '<div class="drag-helper">'
                        + '<table><tr><th></th></tr></table>'
                        + '</div>');
                    $('th', $helper).append($('.field-node_preview_and_name a', this).clone());
                    return $helper;
                },
                scope: DRAG_DROP_SCOPE,
                handle: DRAG_HANDLE_SELECTOR,
                appendTo: 'body',
                distance: 1,
                delay: 50
            });

            $this.droppable({
                drop: function(event, ui) {
                    var droppedId = $(ui.draggable.context).attr('node'),
                        targetId = $(this).attr('node'),
                        targetIsFolder = isFolder(this),
                        $expandCollapse = $(EXPAND_COLLAPSE_SELECTOR, this);

                    $expandCollapse.addClass('loading');
                    pendingRequests.push($.ajax({
                        url: window.MOVE_NODE_ENDPOINT,
                        type: 'post',
                        data: {
                            node_id: droppedId,
                            sibling_id: targetId,
                            as_child: targetIsFolder ? 1 : 0
                        },
                        beforeSend: function(xhr) {
                            xhr.setRequestHeader("X-CSRFToken", $('input[name=csrfmiddlewaretoken]').val());
                        },
                        complete: function(xhr, textStatus) {
                            pendingRequests.splice(pendingRequests.indexOf(xhr), 1);
                            if (!pendingRequests.length) {
                                window.location.reload();
                            } else {
                                $expandCollapse.removeClass('loading');
                            }
                        }
                    }));
                },
                scope: DRAG_DROP_SCOPE,
                hoverClass: function() {
                    return isFolder(this) ? 'drop-parent' : 'drop-sibling';
                },
                greedy: true,
                accept: function(draggable) {
                    return true
                }
            });

            // Disable selection and dragging of thumbnail
            $this.disableSelection().find('img').css({'pointer-events': 'none'})

            // Display drag handle
            $this.find(DRAG_HANDLE_SELECTOR).addClass('active');
        });
    };

    var changeListUpdated = function() {
        // Count rows and update the displayed number of rows in paginator
        var rows = $(ROW_SELECTOR);
        $('#changelist .paginator, #changelist-search .small.quiet').contents().each(function() {
            if (this.nodeType == 3 && this.nodeValue.match('[0-9]')) {
                pat = /([^\s()]+\s*)*[0-9]+(\s*[^\s()]+)*/
                this.nodeValue = this.nodeValue.replace(pat, ngettext('%i media object',
                    '%i media objects', rows.length).replace('%i', rows.length));
            }
        });
    };

    var collapseRecursively = function(parentId) {
        var $childTrs = $(ROW_SELECTOR + '[parent=' + parentId + ']');
        $childTrs.each(function() {
            var $tr = $(this),
                nodeId = $tr.attr('node');
            collapseRecursively(nodeId);
            $tr.remove();
        });
    };

    initChangeListResults(ROW_SELECTOR);

    $('#changelist').delegate('a.collapse.collapsed', 'click', function(event) {
        event.preventDefault();
        var $toggle = $(this),
            $tr = $toggle.closest('tr'),
            nodeId = $tr.attr('node');

        $toggle.addClass('loading');
        $.ajax({
            url: '?parent=' + nodeId,
            success: function(result, textStatus, xhr) {
                $toggle.removeClass('collapsed').addClass('expanded');
                var $newTrs = $(result).find(ROW_SELECTOR);
                initChangeListResults($newTrs);
                var inserted = $newTrs.insertAfter($tr);
                changeListUpdated();
            },
            complete: function(xhr, textStatus) {
                $toggle.removeClass('loading');
            }
        });
    });

    $('#changelist').delegate('a.collapse.expanded', 'click', function(event) {
        var $toggle = $(this),
            $tr = $toggle.closest('tr'),
            nodeId = $tr.attr('node');
        collapseRecursively(nodeId);
        $toggle.removeClass('expanded').addClass('collapsed');
    });

    $('a[onclick*=dismissRelatedLookupPopup]').each(function() {
        var _onclick = this.onclick,
            $trigger = $(this);
        this.onclick = null;
        $trigger.click(function(evt) {
            evt.preventDefault();
            var d = opener.document,
                fieldName = windowname_to_id(window.name).substring('id_'.length),
                $input = $('#' + windowname_to_id(window.name), d),
                $widgetContainer = $input.closest('.FileNodeForeignKeyRawIdWidget');
            if ($widgetContainer.length) {
                var $preview = $trigger.find('.preview:visible').clone(),
                    $name = $trigger.find('.name').clone(),
                    $targetPreview = $widgetContainer.find('.preview'),
                    $targetName = $widgetContainer.find('.name');
                $targetPreview.replaceWith($preview);
                $targetName.replaceWith($name);
            }

            window.selectedMeta = $trigger.find('link.meta')[0];
            _onclick();
        });
    });

    $.makeChangelistRow = function(cols, row)
    {
        if ($('#changelist table').length == 0) {
            var table = $('<table cellspacing="0"><thead><th>&nbsp;</th><th>'+gettext('Media object')+'</th><th>'+gettext('Size')+'</th></table>')
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

    // Prebuffer background images
    var bufferBackgroundElements = $('<div class="loading"><div class="folder-toggle" /></div>');
    bufferBackgroundElements.hide();
    $('body').append(bufferBackgroundElements);
    $('*', bufferBackgroundElements).each(function() {
        var matchUrl = $(this).css('background-image').match(/url\((.*)\)/);
        if (matchUrl) {
            var img = new Image();
            img.src = matchUrl[1];
        }
    });
    bufferBackgroundElements.remove();
});
