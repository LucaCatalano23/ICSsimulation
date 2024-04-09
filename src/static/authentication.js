// Codifica un array di byte in base64url
function base64urlEncode(array) {
    return btoa(String.fromCharCode.apply(null, array))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

// Funzione per gestire l'autenticazione
async function authenticate() {
    try {
        // Effettuare la richiesta al server per ottenere le opzioni di autenticazione
        const response = await fetch('/auth', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });

        const authenticationOptions = await response.json();

        // Convertire le opzioni da stringa a oggetto JSON per poter accedere ai vari attributi
        jsonOptions = JSON.parse(authenticationOptions);

        const publicKeyCredentialRequestOptions = {
            challenge: Uint8Array.from(
                jsonOptions.challenge, c => c.charCodeAt(0)),
            allowCredentials: jsonOptions.allowCredentials,
            timeout: jsonOptions.timeout,
        }

        // Effettuare l'autenticazione utilizzando WebAuthn
        const credential = await navigator.credentials.get({
            publicKey: publicKeyCredentialRequestOptions
        });

        // Converti alcuni valori restituiti da WebAuthn in stringhe base64url per poterlo inviare al server
        const publicCredential = {
            id: credential.id,
            rawId: base64urlEncode(new Uint8Array(credential.rawId)),
            response: AuthenticatorAttestationResponse = {
                authenticatorData: base64urlEncode(new Uint8Array(credential.response.authenticatorData)),
                clientDataJSON: base64urlEncode(new Uint8Array(credential.response.clientDataJSON)),
                signature: base64urlEncode(new Uint8Array(credential.response.signature)),
                userHandle: base64urlEncode(new Uint8Array(credential.response.userHandle))
            },
            type: credential.type
        };

        // Invia la risposta di autenticazione al server
        const authenticationResponse = await fetch('/verify', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                credential: publicCredential,
                challenge: base64urlEncode(publicKeyCredentialRequestOptions.challenge)
            })
        });

        const registrationResult = await authenticationResponse.json();

        // Mostra il risultato dell'autenticazione
        if (registrationResult.success) {
            document.getElementById('authenticationResult').innerText = 'Autenticazione riuscita!';
            window.location.href = '/panel';
        } else {
            document.getElementById('authenticationResult').innerText = 'Autenticazione fallita.';
        }
    } catch (error) {
        console.error('Errore durante l\'autenticazione:', error);
        document.getElementById('authenticationResult').innerText = 'Errore durante l\'autenticazione.';
    }
}

// Aggiungi un gestore di eventi per il click del pulsante di autenticazione
document.getElementById('authenticateButton').addEventListener('click', authenticate);