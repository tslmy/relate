function stringStartsWith (string, prefix) {
    return string.slice(0, prefix.length) == prefix;
} //http://stackoverflow.com/questions/646628/how-to-check-if-a-string-startswith-another-string
$( document ).ready(function () {
    arrowUp_div = '<div class="arrowUp"></div>';
    arrowDown_div = '<div class="arrowDown"></div>';
    result_div = $("#result");
    button_div = $("#button");
});
$('#form').submit(function () {
    button_div.addClass('pure-button-disabled');
    userInputA = $('input#A').val();
    userInputB = $('input#B').val();
    result_div.hide();
    result_div.html('');
    $.post( "/run", 
            {a:userInputA, b:userInputB}, 
            function( data ) {
                r = data.r;
                //console.log(r);
                previousItem = '';
                ifReversed = false;
                toAppend = [];
                for (var i in r) {
                    if (r.hasOwnProperty(i)) { 
                        pair = r[i];
                        property = pair[0];
                        entity = pair[1];
                        propertyUp_div = '<section class="property up" id="'+property+'"><dt class="label">'+property+'</dt></section>';
                        propertyDown_div = '<section class="property down" id="'+property+'">'+property+'</section>';
                        entity_div = '<section class="entity" id="'+entity+'">'+entity+'</section>';
                        if (previousItem == entity) {
                            ifReversed = true;
                            toAppend.push(propertyUp_div);
                        } else if (ifReversed) {
                            toAppend.push(entity_div);
                            toAppend.push(propertyUp_div);
                        } else {
                            toAppend.push(propertyDown_div);
                            toAppend.push(entity_div);
                        };
                        previousItem = entity;
                    };
                };
                result_div.append(toAppend.join('\n'));
                var ids = [].concat.apply([], r);
                for(var i = ids.length-1; i--;){
                    if (ids[i] === "TERMINAL") ids.splice(i, 1);
                };
                console.log(ids);
                var url = wdk.getEntities({
                    ids: ids,
                    properties: ['descriptions','labels'], // returns all data if not specified
                    languages: 'en'
                });
                $.ajax({
                    type: 'GET',
                    url: url,
                    dataType: 'jsonp',
                    success: function(data) {
                        r = data.entities;
                        for (var i in r) {
                            if (r.hasOwnProperty(i)) {
                                try {
                                    label_div = '<dt class="label">'+r[i].labels.en.value+'</dt>';
                                }
                                catch(err) {
                                    label_div = '<dt class="label">'+i+'</dt>';
                                };
                                try {
                                    description_div = '<dd class="description">'+r[i].descriptions.en.value+'</dd>';
                                }
                                catch(err) {
                                    description_div = '<dd class="description"></dd>';
                                };
                                $('#'+i).html(label_div+description_div);
                            };
                            button_div.removeClass('pure-button-disabled');
                            result_div.show();
                        };
                    }
                });
            });
    return false;
});
