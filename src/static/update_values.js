// Funzione per gestire l'update del flow rate
function flowUpdate() {
    value = document.getElementById('flow_box').value;
    // Invio del valore al server tramite una richiesta POST
    fetch('/flowUpdate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 'value': value })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            document.getElementById('flow_box').value == '';
            console.log('Update sent successfully');
        })
        .catch(error => {
            console.log(response);
            console.error('There was a problem with the fetch operation:', error);
        });
}

// Funzione per gestire l'update del drain rate
function drainUpdate() {
    value = document.getElementById('drain_box').value;
    // Invio del valore al server tramite una richiesta POST
    fetch('/drainUpdate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 'value': value })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            document.getElementById('drain_box').value == '';
            console.log('Update sent successfully');
        })
        .catch(error => {
            console.log(response);
            console.error('There was a problem with the fetch operation:', error);
        });
}

// Aggiungi un gestore di eventi per il click del pulsante di update
document.getElementById('flowButton').addEventListener('click', flowUpdate);
document.getElementById('drainButton').addEventListener('click', drainUpdate);