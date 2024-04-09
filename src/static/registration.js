// Codifica un array di byte in base64url
function base64urlEncode(array) {
    return btoa(String.fromCharCode.apply(null, array))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

async function register() {
    try {
        const username = document.getElementById('username').value;
        if (username) {
            // Effettuare la richiesta al server per ottenere le opzioni di registrazione
            const response = await fetch('/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username})
            });

            const registrationOptions = await response.json();

            // Convertire le opzioni da stringa a oggetto JSON per poter accedere ai vari attributi
            jsonOptions = JSON.parse(registrationOptions);

            // Limitare la lunghezza dell'ID dell'utente a 64 byte come da specifica
            const encoder = new TextEncoder();
            const userIdBytes = encoder.encode(jsonOptions.user.id);

            // Calcola l'hash SHA-256 dell'ID dell'utente
            const hashBuffer = await crypto.subtle.digest('SHA-256', userIdBytes);

            // Converti l'hash in una stringa esadecimale
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
 
            challenge = Uint8Array.from(jsonOptions.challenge, c => c.charCodeAt(0));
            
            // Decodifica di alcuni valori ricevuti dal server in byte
            const publicKeyCredentialCreationOptions = {
                challenge: challenge,
                rp: {
                    name: jsonOptions.rp.name,
                    id: jsonOptions.rp.id,
                },
                user: {
                    id: Uint8Array.from(
                        hashHex, c => c.charCodeAt(0)),
                    name: jsonOptions.user.name,
                    displayName: jsonOptions.user.displayName,
                },
                pubKeyCredParams: jsonOptions.pubKeyCredParams,
                authenticatorSelection: jsonOptions.authenticatorSelection,
                timeout: jsonOptions.timeout,
                attestation: jsonOptions.attestation
            };
            
            var createCredentialDefaultArgs = {
                publicKey: publicKeyCredentialCreationOptions
            };

            // Effettuare la registrazione utilizzando WebAuthn
            const credential = await navigator.credentials.create(createCredentialDefaultArgs);

            // Converti alcuni valori restituiti da WebAuthn in stringhe base64url per poterlo inviare al server
            const publicCredential = {
                id: credential.id,
                rawId: base64urlEncode(new Uint8Array(credential.rawId)),
                response: {
                    attestationObject:  base64urlEncode(new Uint8Array(credential.response.attestationObject)),
                    clientDataJSON: base64urlEncode(new Uint8Array(credential.response.clientDataJSON))
                },
                type: credential.type
            };

            // Invia la risposta di registrazione al server
            const registrationResponse = await fetch('/complete-registration', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    credential: publicCredential,
                    challenge: base64urlEncode(challenge)
                })
            });

            const result = await registrationResponse.json();

            if (result.success) {
                // Se la registrazione ha successo, mostra un messaggio di conferma
                document.getElementById('registrationResult').innerText = 'Registrazione completata con successo!';
            } else {
                // Altrimenti, mostra un messaggio di errore
                document.getElementById('registrationResult').innerText = 'Errore durante la registrazione.';
            }
        } else {
            console.error('Inserisci un username valido');
            document.getElementById('registrationResult').innerText = 'Inserisci un username valido.';
        }
    } 
    catch (error) {
        console.error('Errore durante la registrazione:', error);
        document.getElementById('registrationResult').innerText = 'Errore durante la registrazione:';
    } 
}

// Aggiungi un gestore di eventi per il click del pulsante di registrazione
document.getElementById('registerButton').addEventListener('click', register);

