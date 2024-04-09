CREATE DATABASE IF NOT EXISTS passwordless;

use passwordless;

CREATE TABLE credentials (
    credential_id VARCHAR(64) PRIMARY KEY,
    credential_public_key BLOB,
    sign_count INT,
    aaguid VARCHAR(36),
    fmt ENUM('packed', 'tpm', 'android-key', 'android-safetynet', 'fido-u2f', 'apple', 'none'),
    credential_type ENUM('public-key'),
    user_verified BOOLEAN,
    attestation_object BLOB,
    credential_device_type ENUM('single_device', 'multi_device'),
    credential_backed_up BOOLEAN
);
