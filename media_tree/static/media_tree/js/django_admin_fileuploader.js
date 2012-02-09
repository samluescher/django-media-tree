jQuery(function($) {
    DjangoAdminFileUploader = function(o){
        // call parent constructor
        qq.FileUploader.apply(this, arguments);
        this._options.showMessage = function(message) { };
    }

    qq.extend(DjangoAdminFileUploader.prototype, qq.FileUploader.prototype);

    qq.extend(DjangoAdminFileUploader.prototype, {


        /**
         * Gets one of the elements listed in this._options.classes
         **/
        _find: function(parent, type){                                
            var element = qq.getByClass(parent, this._options.classes[type])[0];        
            if (!element){
                throw new Error('element not found ' + type);
            }
            
            return element;
        },
        _setupDragDrop: function(){
            var self = this,
                dropArea = this._find(this._element, 'drop');                        

            var dz = new qq.UploadDropZone({
                element: dropArea,
                onEnter: function(e){
                    qq.addClass(dropArea, self._classes.dropActive);
                    e.stopPropagation();
                },
                onLeave: function(e){
                    e.stopPropagation();
                },
                onLeaveNotDescendants: function(e){
                    qq.removeClass(dropArea, self._classes.dropActive);  
                },
                onDrop: function(e){
                    dropArea.style.display = 'none';
                    qq.removeClass(dropArea, self._classes.dropActive);
                    self._uploadFileList(e.dataTransfer.files);    
                }
            });
                    
            dropArea.style.display = 'none';

            qq.attach(document, 'dragenter', function(e){     
                if (!dz._isValidFileDrag(e)) return; 
                
                dropArea.style.display = 'block';            
            });                 
            qq.attach(document, 'dragleave', function(e){
                if (!dz._isValidFileDrag(e)) return;            
                
                var relatedTarget = document.elementFromPoint(e.clientX, e.clientY);
                // only fire when leaving document out
                if ( ! relatedTarget || relatedTarget.nodeName == "HTML"){               
                    dropArea.style.display = 'none';                                            
                }
            });                
        },



        _onComplete: function(id, fileName, result){
            qq.FileUploaderBasic.prototype._onComplete.apply(this, arguments);

            // mark completed
            var item = this._getItemByFileId(id);                
            qq.remove(this._find(item, 'cancel'));
            
            if (result.success){
                qq.addClass(item, this._classes.success);    
            } else {
                qq.addClass(item, this._classes.fail);
            }         

            if (result.error){
                this._updateStatusText(id, result.error, 'upload-error');
                $(item).find('.upload-progress-bar').text(gettext('failed'));
            }             
        },

        _updateStatusText: function(id, message, messageClass)
        {
            var row = this._getItemByFileId(id);
            $(row).find('.queue-status').each(function() {
                if (messageClass != null) {
                    $(this).addClass(messageClass);
                }
                $(this).text(message);
            });
        },




        _onProgress: function(id, fileName, loaded, total){
            qq.FileUploaderBasic.prototype._onProgress.apply(this, arguments);

            var row = this._getItemByFileId(id);
            var percent = Math.round(loaded / total * 100);

            $(row).find('.queue-status').text('');
            $(row).find('.upload-progress-bar-container').css('display', 'inline-block');
            var bar = $(row).find('.upload-progress-bar');
            bar.css('width', percent+'%');
            bar.text(percent+'%');
            if (percent == 100) {
                bar.addClass('complete');
            }

        },

        _formatSize: function(size) {
            return size > 1000000 ? 
                Math.round(size / 1000000, 1) + ' MB'
                : (size > 1000 ? 
                    Math.round(size / 1000, 1) + ' KB'
                    : size + ' bytes'); 
        },

        _addToList: function(id, fileName){

            var file = {
                name: fileName,
                size: 0,
                id: id
            };
            
            var c = this._options.classes;

            cols = [];
            cols[1] = $(
                '<td class="nowrap"><span style="display: none;" class="upload-progress-bar-container">'
                + '<span class="upload-progress-bar"></span></span><span class="queue-status">' 
                + gettext('queued') + '</span>' 
                + '&nbsp;<a href="#">' + file.name + '</a>'
                + '&nbsp;<a href="#" class="' + c['cancel'] + '">'+gettext('cancel')+'</a>'
                + '</td>');
            cols[2] = $('<td class="filesize"><span class="' + c['size'] + '"></span></td>');

            var row = $.makeChangelistRow(cols, this._getItemByFileId(id));
            row.qqFileId = id;

            var queuedRows = $('tr.queue');

            if (queuedRows.length > 0) {
                $(queuedRows[queuedRows.length - 1]).after(row);
            } else {
                $('#changelist table tbody').prepend(row);
            }

            var sortCol = $('#changelist table').find('th.sorted');
            sortCol.removeClass('sorted ascending descending');
        },

        _getItemByFileId: function(id){
            var item = $('#queue-'+id);
            if (item.length) {
                return item[0];
            } else {
                return $('<tr id="queue-'+id+'" class="queue"></tr>');
            }
        },
    });
});
