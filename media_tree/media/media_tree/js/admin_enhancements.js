django.jQuery(function($) {
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
                console.log('selected '+$(this).val());
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

});
