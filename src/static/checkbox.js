// Funzione per inviare i valori dei checkbox al server quando vengono modificati
function sendCheckboxValue(checkboxId) {
    var checkbox = document.getElementById(checkboxId);
    var value = checkbox.checked;
    checkbox_name = checkbox.name;
    fetch('/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'name': checkbox_name, 'value': value})
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            console.log('Checkbox value sent successfully');
        })
        .catch(error => {
            console.log(response);
            console.error('There was a problem with the fetch operation:', error);
        });
}

// Aggiungi un event listener per intercettare i cambiamenti nelle checkbox
document.getElementById('flow').addEventListener('change', function () {
    sendCheckboxValue('flow');
});

document.getElementById('drain').addEventListener('change', function () {
    sendCheckboxValue('drain');
});
