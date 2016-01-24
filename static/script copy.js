function stringStartsWith (string, prefix) {
    return string.slice(0, prefix.length) == prefix;
} //http://stackoverflow.com/questions/646628/how-to-check-if-a-string-startswith-another-string

getIdByInput = function (userInput, onSuccess) {
    var language = 'en'; // will default to 'en'
    var limit = 20; // default 20
    var format = 'json'; // default to json
    var url = wdk.searchEntities(userInput, language, limit, format);
    $.ajax({
	    type: 'GET',
		url: url,
		dataType: 'jsonp',
        success: function (data) {
            bestGuessOfId = data.search[0].id;
            onSuccess(bestGuessOfId);
        }
	});
};

getClaimsById = function (id, onSuccess, path) {
    var url = wdk.getEntities({
        ids: id,
        properties: 'claims', // returns all data if not specified
        languages: 'en'
    });
    $.ajax({
	    type: 'GET',
		url: url,
		dataType: 'jsonp',
        success: function(data) {
            claims = wdk.simplifyClaims(data.entities[id].claims);
            onSuccess(claims);
        }
	});
};

returnSuccess = function (path) {
    alert('Success with path '+path+'!');
}

checkExistenceOfB = function (claims, path) {
    for (var property in Object.keys(claims)) {
        for (var entity in claims[property]) {
            if (stringStartsWith(entity,'Q')) {//I want to make sure it's indeed a entity.
                if (map.hasOwnProperty(entity)) {
                    if (map[entity].ifLinkedToB) {
                        return returnSuccess(path);
                    } else {
                        console.log('Meet '+entity+' again. Ignoring.');
                    };
                } else {
                    map[entity] = {
                        ifLinkedToA:true,
                        ifLinkedToB:false
                    };
                    getClaimsById(entity, checkExistenceOfB, path.concat([entity]));
                };
            }
        }
    }
};

var map = []; // create an empty array
$( document ).ready(function () {
    $('#log').html('ready');
    userInputA = $('input#A').val();
    userInputB = $('input#B').val();
    getIdByInput(userInputB, function(id){
        map[id] = {
            ifLinkedToA:false,
            ifLinkedToB:true
        };
    });
    getIdByInput(userInputA, function(id){
        getClaimsById(id, checkExistenceOfB,[id]);
    });

});
