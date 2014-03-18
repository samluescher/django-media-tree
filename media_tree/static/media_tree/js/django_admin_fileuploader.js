jQuery(function($) {

    $.fn.djangoAdminFileUploader = function(opts) {
        var uploader = $(this).fineUploader(opts),
            originalDocumentTitle = document.title,

            _updateStatusText = function(id, message, messageClass) {
                var row = _getItemByFileId(id);
                $(row).find('.queue-status').each(function() {
                    if (messageClass != null) {
                        $(this).addClass(messageClass);
                    }
                    $(this).text(message);
                });
            },

            _updateProgressBar = function(id, text, percent, cls) {
                var row = _getItemByFileId(id);

                $(row).find('.upload-progress-bar-container').css('display', 'inline-block');
                var bar = $(row).find('.upload-progress-bar');
                
                if (percent != undefined) {
                    bar.css('width', percent+'%');
                }
                if (text) {
                    bar.text(text);
                }
                if (cls) {
                    bar.addClass(cls);
                }
            },

            _addToList = function(id, fileName) {
                var c = {};

                cols = [];
                cols[1] = $(
                    '<td class="nowrap"><span style="display: none;" class="upload-progress-bar-container">'
                    + '<span class="upload-progress-bar"></span></span><span class="queue-status">' 
                    + gettext('queued') + '</span>' 
                    + '&nbsp;<a href="#" class="name">' + fileName + '</a>'
                    + '&nbsp;<a href="#" class="cancel">'+gettext('cancel')+'</a>'
                    + '</td>');
                cols[2] = $('<td class="filesize"><span class="size"></span></td>');

                var row = $.makeChangelistRow(cols, _getItemByFileId(id))[0];
                row.qqFileId = id;

                $('.cancel', row).on('click', function() {
                    console.log('cancel', id);
                    uploader.fineUploader('cancel', id);
                });

                var queuedRows = $('tr.queue');

                if (queuedRows.length > 0) {
                    $(queuedRows[queuedRows.length - 1]).after(row);
                } else {
                    $('#changelist table tbody').prepend(row);
                }

                var sortCol = $('#changelist table').find('th.sorted');
                sortCol.removeClass('sorted ascending descending');
            },

            _getItemByFileId = function(id) {
                var item = $('#queue-'+id);
                if (item.length) {
                    return item[0];
                } else {
                    return $('<tr id="queue-'+id+'" class="queue"></tr>');
                }
            },

            _setQueueMessage = function() {
                var filesInProgress = uploader.fineUploader('getInProgress');
                if (filesInProgress > 0) {
                    document.title = gettext('uploading… (%i in progress)').replace('%i', filesInProgress)+' – '+originalDocumentTitle;
                } else {
                    document.title = originalDocumentTitle;
                }
                var message = ngettext('%i file in progress.', '%i files in progress.', filesInProgress).replace('%i', filesInProgress);
                $.addUserMessage(message, 'upload-queue-message');
            };

        uploader.on('error', function (event, id, name, reason) {
            _updateStatusText(id, reason, 'upload-error');
            _updateProgressBar(id, 'failed', 0, 'complete');
            _setQueueMessage();
        }).on('submit', function (event, id, name) {
            _addToList(id, name);
            _setQueueMessage();
        }).on('progress', function (event, id, name, uploadedBytes, totalBytes) {
            var row = _getItemByFileId(id);
            var percent = Math.round(uploadedBytes / totalBytes * 100);

            _updateStatusText(id, '');
            _setQueueMessage();
            if (percent == 100) {
                $('.cancel', row).remove();
                _updateProgressBar(id, 'waiting', 100);
            } else {
                _updateProgressBar(id, percent+'%', percent);
            }
        }).on('complete', function (event, id, name, responseJSON) {
            var row = _getItemByFileId(id);
            $('.cancel', row).remove();
            if (responseJSON.success) {
                _updateProgressBar(id, 'complete', 100, 'complete');
            }
        }).on('cancel', function(event, id, name) {
            var row = _getItemByFileId(id);
            $('.cancel', row).remove();
            _updateStatusText(id, 'canceled', 'upload-error');
            _updateProgressBar(id, '', 0, 'complete');
        }).on('allComplete', function(event, succeeded, failed) {
            _setQueueMessage();
            var successfulUploads = succeeded.length,
                uploadsInProgress = false,
                uploadErrors = failed.length;

            if (uploadErrors == 0) {
                /*window.location.reload();*/
                // instead, replace change list only:
                var message = gettext('loading…');
                $.addUserMessage(message, 'upload-queue-message');

                $('#changelist').addClass('loading');
                $('#changelist').setUpdateReq($.ajax({
                    url: window.location.href, 
                    success: function(data, textStatus) {
                        if (!uploadsInProgress) {
                            // reload changelist contents
                            $('#changelist').updateChangelist($(data).find('#changelist').html());
                            // insert success message
                            message = ngettext('Successfully added %i file.', 'Successfully added %i files.', successfulUploads).replace('%i', successfulUploads);
                            $.addUserMessage(message, 'upload-queue-message');
                            // reset stats
                        }
                    },
                    complete: function(jqXHR, textStatus) {
                        $('#changelist').removeClass('loading');
                    }
                }));
            } else {
                var message = gettext('There were errors during upload.');
                $.addUserMessage(message, 'upload-queue-message');
            }
        });

        return uploader;
    };

});