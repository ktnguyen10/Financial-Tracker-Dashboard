function getNum(str) {
    var res = [/^\D+/g,/\D+$/g,/^\D+|\D+$/g,/\D+/g,/\D.*/g, /.*\D/g,/^\D+|\D.*$/g,/.*\D(?=\d)|\D+$/g];
    for(var i = 0; i < res.length; i++)
        if(str.replace(res[i], '') === num)
            var thenum = thestring.replace(/^\D+/g, '');
            return thenum;
}

function getFormValues() {
    for (var x of form){
       valueArr.push({label:x.name, value:x.value})
    }
    console.log(valueArr);
    return valueArr;
}

function updateBudget() {
    var formElements = $('#itemList').find(':input').toArray();
    var formData = {};
    for (var i = 0; i < formElements.length; i++) {
        var element = formElements[i];
        // Check if the element is an input field
        if (element.tagName === 'INPUT') {
            formData[element.name] = element.value;
        }
    }
    console.log(formData.value);
    $.ajax({
        url: '/budget',
        type : 'POST',
        cache : false,
        dataType : 'json',
        contentType: 'application/json; charset=utf-8',
        data : JSON.stringify(formData),
        success : function(response) {
            console.log('Successful Response');

            var returned = JSON.parse(response)
            var categories = returned.category;
            var amounts = returned.amount;
//            alert(result.success); // result is an object which is created from the returned JSON
        }
    }).done( function(result) {
        console.log(result);
    }).fail( {
    });
}