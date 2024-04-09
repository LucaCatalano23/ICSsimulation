// Funzione per richiedere dati al server e aggiornare la pagina
function requestData() {
    $.ajax({
        url: '/monitor', // URL per richiedere i dati al server
        type: 'GET',
        dataType: 'json', // Tipo di dati attesi in risposta
        success: function(response) {
            // Aggiorna la pagina con i nuovi dati ricevuti dal server
            $('#level').text(JSON.stringify(response.level));
            $('#drain_rate').text(JSON.stringify(response.drain_rate));
            $('#flow_rate').text(JSON.stringify(response.flow_rate));
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
        }
    });
}

// Esegui la funzione requestData() ogni secondo
setInterval(requestData, 1000);