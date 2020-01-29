
if(!window.MONKEY_PATCHING){
    window.MONKEY_PATCHING = 1;

    window.TOT = {};
    window.TOT2 = {};

    window.TIMEOUT_COUNT = 0;
    window.TIMEOUT_CALLS = {};

    setTimeout(function(){
        window.openerp.ui.Tips.prototype.show = function(){}
    }, 0)

    realSetTimeout = window.setTimeout;
    realClearTimeout = window.clearTimeout;

    window.setTimeout = function(a,b){

        // we don't want to wait for the header to be updated (hidden/visible)
        //   because it's not part of a process.
        if(b === 30000 || b === 5000)
            return realSetTimeout(a,b);

        window.TIMEOUT_COUNT += 1;
        var save_id_dict = {};

        id = realSetTimeout(function callA(){
            a(b);

            if(window.TIMEOUT_CALLS[save_id_dict.id])
                window.TIMEOUT_COUNT -= 1;

            window.TIMEOUT_CALLS[save_id_dict.id] = false;
        },b);
        save_id_dict.id = id;

        window.TIMEOUT_CALLS[id] = true;

        return id;
    }
    window.clearTimeout = function(b){

        if(window.TIMEOUT_CALLS[b])
            window.TIMEOUT_COUNT -= 1;

        window.TIMEOUT_CALLS[b] = false;

        return realClearTimeout(b);
    }

    window.confirm = function(a){return true;}

    window.onChange = function(caller){

        if(jQuery(caller).attr("id")){
            window.TOT2[jQuery(caller).attr("id")] = true;
            window.TOT[jQuery(caller).attr("id")] = (window.TOT[jQuery(caller).attr("id")] || 0) + 1;
        }

        if (openobject.http.AJAX_COUNT > 0) {
            if(jQuery(caller).attr("id"))
                window.TOT[jQuery(caller).attr("id")] = (window.TOT[jQuery(caller).attr("id")] || 0) - 1;
            callLater(1, onChange, caller);
            return;
        }

        var $caller = jQuery(openobject.dom.get(caller));
        var $form = $caller.closest('form');
        var callback = $caller.attr('callback');
        var change_default = $caller.attr('change_default');

        if (!(callback || change_default) || $caller[0].__lock_onchange) {
            if(jQuery(caller).attr("id")){
                window.TOT2[jQuery(caller).attr("id")] = false;
                window.TOT[jQuery(caller).attr("id")] = (window.TOT[jQuery(caller).attr("id")] || 0) - 1;
            }
            return;
        }

        var is_list = $caller.attr('id').indexOf('_terp_listfields') == 0;
        var prefix = $caller.attr('name') || $caller.attr('id');
        prefix = prefix.slice(0, prefix.lastIndexOf('/') + 1);

        var id_slice_offset = is_list ? 17 : 0;
        var id_prefix = prefix.slice(id_slice_offset);
        var select = function (id) { return $form.find(idSelector(id_prefix + id)); };

        var post_url = callback ? '/openerp/form/on_change' : '/openerp/form/change_default_get';

        var form_data = getFormData(1, true, $form);
        /* testing if the record is an empty record, if it does not contain anything except
         * an id, the on_change method is not called
         */
        var nbr_elems = 0;
        var elem_id;
        for(var key in form_data) {
            nbr_elems++;
            if (nbr_elems > 1)
                break;
            elem_id = key;
        }
        if(nbr_elems == 1 && /\/__id$/.test(elem_id)) {
            if(jQuery(caller).attr("id")){
                window.TOT2[jQuery(caller).attr("id")] = false;
                window.TOT[jQuery(caller).attr("id")] = (window.TOT[jQuery(caller).attr("id")] || 0) - 1;
            }
            return;
        }

        openobject.http.postJSON(post_url, jQuery.extend({}, form_data, {
            _terp_callback: callback,
            _terp_caller: $caller.attr('id').slice(id_slice_offset),
            _terp_value: $caller.val(),
            _terp_model: select('_terp_model').val(),
            _terp_context: select('_terp_context').val(),
            id: select('_terp_id').val()
        })).addCallback(function(obj){

            if (obj.error) {

                if(jQuery(caller).attr("id")){
                    window.TOT2[jQuery(caller).attr("id")] = false;
                    window.TOT[jQuery(caller).attr("id")] = (window.TOT[jQuery(caller).attr("id")] || 0) - 1;
                }

                return error_popup(obj)
            }

            var values = obj['value'];
            var domains = obj['domain'];

            domains = domains ? domains : {};
            var fld;
            for (var domain in domains) {
                fld = openobject.dom.get(prefix + domain);
                if (fld) {
                    jQuery(fld).attr('domain', domains[domain]);
                }
            }
            var flag;
            var value;
            for (var k in values) {
                flag = false;
                var $fld = jQuery(idSelector(prefix + k));
                if(!$fld.length)
                    continue;
                fld = $fld[0];
                value = values[k];
                value = value === false || value === null ? '' : value;

                // prevent recursive onchange
                fld.__lock_onchange = true;

                if (openobject.dom.get(prefix + k + '_id')) {
                    fld = openobject.dom.get(prefix + k + '_id');
                    flag = true;
                }

                if ((fld.value !== value) || flag) {
                    fld.value = value;
                    var $current_field = jQuery(fld);
                    var kind = $current_field.attr('kind')

                    //o2m and m2m
                    if ($current_field.hasClass('gridview') && !kind){
                        if (jQuery('#_terp_id').val()=='False') {//default o2m
                            var $o2m_current = jQuery(fld);
                            var k_o2m = k;
                            var $default_o2m = jQuery(idSelector('_terp_default_o2m/'+k));

                            if ($default_o2m.length && !value) {
                                if($default_o2m.val()) {
                                    $default_o2m.val('');
                                    new ListView(prefix + k).reload();
                                } else {
                                    continue;
                                }
                            } else if (value) {
                                jQuery.ajax({
                                    // This request should not be asynchronous in order to keep onChange precedence
                                    // If asynchronous is needed, the onChange function design should be reviewed
                                    async : false,
                                    type: 'POST',
                                    url: '/openerp/listgrid/get_o2m_defaults',
                                    dataType : 'json',
                                    data: {
                                        o2m_values: serializeJSON(value),
                                        model: jQuery('#_terp_model').val(),
                                        o2m_model: jQuery(idSelector(prefix+k+'/_terp_model')).val(),
                                        name: k,
                                        view_type: jQuery('#_terp_view_type').val(),
                                        view_id: jQuery('#_terp_view_id').val(),
                                        o2m_view_type: jQuery(idSelector(prefix+k+'/_terp_view_type')).val(),
                                        o2m_view_id: jQuery(idSelector(prefix+k+'/_terp_view_id')).val(),
                                        editable: jQuery(idSelector(prefix+k+'/_terp_editable')).val(),
                                        limit: jQuery(idSelector(prefix+k+'/_terp_limit')).val(),
                                        offset: jQuery(idSelector(prefix+k+'/_terp_offset')).val(),
                                        o2m_context: jQuery(idSelector(prefix+k+'/_terp_context')).val(),
                                        o2m_domain: jQuery(idSelector(prefix+k+'/_terp_domain')).val()
                                    },
                                    success: function(obj) {
                                        $o2m_current.closest('.list-a').replaceWith(obj.view);
                                        if ($default_o2m.length) {
                                            $default_o2m.val(obj.formated_o2m_values);
                                        } else {
                                            jQuery(idSelector(k_o2m)).parents('td.o2m_cell').append(
                                                jQuery('<input>', {
                                                    id: '_terp_default_o2m/'+k_o2m,
                                                    type: 'hidden',
                                                    name:'_terp_default_o2m/'+k_o2m,
                                                    value: obj.formated_o2m_values
                                                })
                                            );
                                        }
                                        $o2m_current.attr('__lock_onchange', false);
                                    }
                                });
                            }
                        } else if(value){
                            new ListView(prefix + k).reload();
                        }
                    }
                    switch (kind) {
                        case 'picture':
                            fld.src = value;
                            break;
                        case 'many2many':
                            var fld_val = '[]';
                            if(value){
                                fld_val = '['+ value.join(',') + ']';
                            }
                            var fld_name = jQuery(fld).attr('name');
                            if (!jQuery(fld).attr('name')) {
                                // guess we are in editable tree view
                                jQuery(idSelector(prefix + k)).val(fld_val);
                                break;
                            }
                            var old_m2m = jQuery(idSelector(fld_name)).closest('.list-a');
                            $(idSelector(fld_name+'/_terp_id')).val('');
                            $(idSelector(fld_name+'/_terp_ids')).val('[]');
                            jQuery.ajax({
                                url: '/openerp/listgrid/get_m2m',
                                context: old_m2m,
                                data: {
                                    'name': fld_name,
                                    'model': jQuery(fld).attr('relation'),
                                    'view_id': jQuery(idSelector(fld_name + '/_terp_view_id')).val(),
                                    'view_type': jQuery(idSelector(fld_name + '/_terp_view_type')).val(),
                                    'ids': fld_val
                                },
                                dataType: 'json',
                                error: loadingError(),
                                success: function(obj){
                                    $(this).replaceWith(obj.m2m_view);
                                }
                            });
                            break;
                        case 'many2one':
                            if (value.length > 2 || typeof(value[0])=='object') {
                                // bug: quick switch from list to form view on product, should be fixed in 6.1 :)
                                fld.__lock_onchange = false;

                                if(jQuery(caller).attr("id")){
                                    window.TOT2[jQuery(caller).attr("id")] = false;
                                    window.TOT[jQuery(caller).attr("id")] = (window.TOT[jQuery(caller).attr("id")] || 0) - 1;
                                }
                                return;
                            }
                            fld.value = value[0] || '';
                            try {
                                openobject.dom.get(prefix + k + '_text').value = value[1] || '';
                                fld._m2o.change_icon();
                            }
                            catch (e) {
                            }
                            break;
                        case 'boolean':
                            obj1 = openobject.dom.get(prefix + k + '_checkbox_')
                            if (obj1) {
                                obj1.checked = value || 0;
                            } else {
                                openobject.dom.get(prefix + k).value = value || 0;
                            }
                            break;
                        case 'text_html':
                            $('#' + prefix + k).val(value || '');
                            break;
                        case 'selection':
                            if (typeof(value)=='object') {
                                var opts = [OPTION({'value': ''})];
                                for (var opt = 0; opt < value.length; opt++) {
                                    if (value[opt].length > 0) {
                                        opts.push(OPTION({'value': value[opt][0]}, value[opt][1]));
                                    } 
                                }
                                MochiKit.DOM.replaceChildNodes(fld, opts);
                                if (jQuery.browser.msie && $fld.attr('callback')) {
                                    jQuery(fld).live("change", function(){
                                        onChange(this);
                                    });
                                }
                            }
                            else {
                                fld.value = value;
                            }
                            break;
                        case 'progress':
                            var progress = values['progress'].toString() + '%';
                            jQuery('.progress-bar').text(progress).append(jQuery('<div>', {
                                'width': progress
                            }));
                            break;
                        case 'reference':
                            if (value) {
                                ref = openobject.dom.get(prefix + k + '_reference');
                                if (typeof(value)=='object') {
                                    var opts = [OPTION({'value': ''})];
                                    for (var opt in value['options']) {
                                        opts.push(OPTION({'value': value['options'][opt][0]}, value['options'][opt][1]));
                                    }
                                    MochiKit.DOM.replaceChildNodes(ref, opts);
                                    value = value['selection'];
                                }
                                v = value.split(',');
                                ref.value = v[0];
                                fld.value = v[1] || '';
                                fld._m2o.on_reference_changed();
                                try {
                                    openobject.dom.get(prefix + k + '_text').value = v[2] || '';
                                }
                                catch (e) {
                                }
                            }
                            break;
                        default:
                        // do nothing on default
                    }
                    $fld.trigger('change');
                    MochiKit.Signal.signal(window.document, 'onfieldchange', fld);
                }

                fld.__lock_onchange = false;
            }

            if (obj.warning && obj.warning.message) {
                error_display(obj.warning.message);
            }

            if(jQuery(caller).attr("id")){
                window.TOT2[jQuery(caller).attr("id")] = false;
                window.TOT[jQuery(caller).attr("id")] = (window.TOT[jQuery(caller).attr("id")] || 0) - 1;
            }
        }).addErrback(function(xmlHttp){
            window.TOT = {}
            window.TOT2 = {}
        });

    };
}

