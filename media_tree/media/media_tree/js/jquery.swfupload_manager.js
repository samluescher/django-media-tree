jQuery(function($) {
    $.SWFUploadManager = function(opts)  
    {
        // Since the event methods in the manager object will be bound to
        // `this` being the SWFUpload object, all methods below use 
        // `manager` instead of `this` when referring to self.
        var manager = 
        {
            originalDocumentTitle: document.title

            ,init: function(opts)
            {
                manager.markFirstChangelistRow();
                defaults = {
                    upload_url: '[required]'
                    ,flash_url: '[required]' 
                    ,button_placeholder_id: "[required]" 
                    ,file_post_name : "[required]" 
                    ,button_width: "[required]"
                    ,button_height: "[required]"
                    ,button_cursor: SWFUpload.CURSOR.HAND 
                    ,button_window_mode: SWFUpload.WINDOW_MODE.TRANSPARENT 
                    ,file_types : "*.*"
                    ,file_size_limit : "1000000000B"
                    // Events:
                    ,file_queued_handler : manager.fileQueued
                    ,file_queue_error_handler : manager.fileQueueError
                    ,file_dialog_complete_handler : manager.fileDialogComplete
                    ,upload_start_handler : manager.uploadStart
                    ,upload_progress_handler : manager.uploadProgress
                    ,upload_error_handler : manager.uploadError
                    ,upload_success_handler : manager.uploadSuccess
                    ,upload_complete_handler : manager.uploadComplete
                    ,queue_complete_handler : manager.queueComplete // Queue plugin event
                };
                new SWFUpload($.extend(defaults, opts)); 
            }

            ,markFirstChangelistRow: function()
            {
                var row = $('#changelist tbody tr');
                if (row.length) {
                    $(row[0]).addClass('changelist-first-row');
                }

            }

            ,fileQueued: function(file) 
            {
                cols = [];
                cols[1] = $('<td class="nowrap"><span style="display: none;" class="upload-progress-bar-container">'
                    + '<span class="upload-progress-bar"></span></span><span class="queue-status">' 
                    + gettext('queued') + '</span>' 
                    + '&nbsp;<a href="javascript:void(0)">'+file.name+'</a></td>');
                cols[2] = $('<td class="filesize">'+Math.round(file.size / 1024, 1) + ' KiB'+'</td>');

                var row = $.makeChangelistRow(cols, manager.getQueueItem(file, 'row1'));
                var firstRow = $('.changelist-first-row');
                if (firstRow.length > 0) {
                    firstRow.before (row);
                } else {
                    $('#changelist table tbody').append(row);
                }

                var sortCol = $('#changelist table').find('th.sorted');
                sortCol.removeClass('sorted ascending descending');
            }

            ,fileQueueError: function(file, errorCode, message) {
            }

            ,fileDialogComplete: function(numFilesSelected, numFilesQueued) {
                if (manager.targetFolder) {
                    this.addPostParam('folder_id', manager.targetFolder.id);
                } else {
                    this.removePostParam('folder_id');
                }
                this.startUpload();
            }

            ,uploadQueueMessage: function(stats)
            {
            	gettext('queued') // For some mysterious reason, the gettext() in fileQueued() is not picked up by django-admin.py makemessages
                document.title = gettext('uploading... (%i in queue)').replace('%i', stats.files_queued)+' – '+manager.originalDocumentTitle;
                var message = ngettext('%i file in queue.', '%i files in queue.', stats.files_queued).replace('%i', stats.files_queued);
                var waitMessage = gettext('Please do not close this window until upload is complete.');
                manager.addUserMessage(message+' '+waitMessage, 'swfupload-queue-message');
            }

            ,uploadStart: function(file) {
                manager.uploadQueueMessage(this.getStats());
            }

            ,uploadProgress: function(file, bytesLoaded, bytesTotal) {
                manager.updateStatusBar(file, Math.ceil((bytesLoaded / bytesTotal) * 100));
            }

            ,updateStatusBar: function(file, percent)
            {
                row = manager.getQueueItem(file);
                $(row).find('.queue-status').text('');
                $(row).find('.upload-progress-bar-container').each(function() {
                    $(this).css('display', 'inline-block');
                });
                $(row).find('.upload-progress-bar').each(function() {
                    $(this).css('width', percent+'%');
                    $(this).text(percent+'%');
                    if (percent == 100) {
                        $(this).addClass('complete');
                    }
                });
            }

            ,uploadSuccess: function(file, serverData) {
                manager.uploadQueueMessage(this.getStats());
                if (serverData.indexOf('ok') != 0) {
                    this.__uploadError = true;
                    manager.errorMessage(file, gettext('Upload error'));
                } else {
                    manager.updateStatusBar(file, 100);
                    //updateStatusText(file, gettext('done'), 'upload-success');
                }
            }

            ,removeStatusBar: function(file)
            {
                row = manager.getQueueItem(file);
                $(row).find('.upload-progress-bar').remove();
            }

            ,updateStatusText: function(file, message, messageClass)
            {
                row = manager.getQueueItem(file);
                $(row).find('.queue-status').each(function() {
                    if (messageClass != null) {
                        $(this).addClass(messageClass);
                    }
                    $(this).text(message);
                });
            }

            ,errorMessage: function(file, message)
            {
                manager.removeStatusBar(file);
                manager.updateStatusText(file, message, 'upload-error');
            }

            ,uploadError: function(file, errorCode, message) 
            {
                switch (errorCode) {
                    case SWFUpload.UPLOAD_ERROR.HTTP_ERROR:
                        message = "Upload Error: " + message;
                        this.debug("Error Code: HTTP Error, File name: " + file.name + ", Message: " + message);
                        break;
                    case SWFUpload.UPLOAD_ERROR.UPLOAD_FAILED:
                        message = "Upload Failed.";
                        this.debug("Error Code: Upload Failed, File name: " + file.name + ", File size: " + file.size + ", Message: " + message);
                        break;
                    case SWFUpload.UPLOAD_ERROR.IO_ERROR:
                        message = "Server (IO) Error";
                        this.debug("Error Code: IO Error, File name: " + file.name + ", Message: " + message);
                        break;
                    case SWFUpload.UPLOAD_ERROR.SECURITY_ERROR:
                        message = "Security Error";
                        this.debug("Error Code: Security Error, File name: " + file.name + ", Message: " + message);
                        break;
                    case SWFUpload.UPLOAD_ERROR.UPLOAD_LIMIT_EXCEEDED:
                        message = "Upload limit exceeded.";
                        this.debug("Error Code: Upload Limit Exceeded, File name: " + file.name + ", File size: " + file.size + ", Message: " + message);
                        break;
                    case SWFUpload.UPLOAD_ERROR.FILE_VALIDATION_FAILED:
                        message = "Failed Validation.  Upload skipped.";
                        this.debug("Error Code: File Validation Failed, File name: " + file.name + ", File size: " + file.size + ", Message: " + message);
                        break;
                    case SWFUpload.UPLOAD_ERROR.FILE_CANCELLED:
                        message = "Cancelled";
                        break;
                    case SWFUpload.UPLOAD_ERROR.UPLOAD_STOPPED:
                        message = "Stopped";
                        break;
                    default:
                        message = "Unhandled Error: " + errorCode;
                        this.debug("Error Code: " + errorCode + ", File name: " + file.name + ", File size: " + file.size + ", Message: " + message);
                        break;
                }

                manager.errorMessage(file, message);
            }

            ,uploadComplete: function(file) {
            }

            ,getQueueItem: function(file, rowClass) {
                var item = $('#queue-'+file.id);
                if (item.length) {
                    return item[0];
                } else {
                    return $('<tr id="queue-'+file.id+'" class="'+rowClass+'"></tr>');
                }
            }

            ,addUserMessage: function(messageText, messageId) 
            {
                var message = $('<li id="'+messageId+'">'+messageText+'</li>')
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

            ,queueComplete: function(numFilesUploaded) {
                document.title = manager.originalDocumentTitle;
                var stats = this.getStats();
                var _this = this;
                if (stats.upload_errors == 0 && !this.__uploadError) {
                    /*window.location.reload();*/
                    // instead, replace change list only:
                    var message = gettext('loading...');
                    manager.addUserMessage(message, 'swfupload-queue-message');

                    $.get(window.location.href, null, function(data, textStatus) {
                        stats = _this.getStats();
                        if (stats.files_queued == 0) {
                            // reload changelist contents
                            $('#changelist').updateChangelist($(data).find('#changelist').html());
                            manager.markFirstChangelistRow();
                            // insert success message
                            message = ngettext('Successfully added %i file.', 'Successfully added %i files.', stats.successful_uploads).replace('%i', stats.successful_uploads);
                            manager.addUserMessage(message, 'swfupload-queue-message');
                            // reset stats
                            stats.successful_uploads = 0;
                            _this.setStats(stats);
                        }
                    });
                } else {
                    var message = gettext('There were errors during upload.');
                    manager.addUserMessage(message, 'swfupload-queue-message');
                }
            }
        };

        manager.init(opts);
        return manager;
    }
});