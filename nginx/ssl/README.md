# SSL Certificates

Place your SSL certificates in this directory for HTTPS support.

## Required Files

- `cert.pem` - SSL certificate
- `key.pem` - Private key
- `chain.pem` (optional) - Certificate chain

## Generating Self-Signed Certificate (Development Only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

## Using Let's Encrypt (Production)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com

# Copy to Docker volume
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./key.pem
```

## Security Notes

- Never commit private keys to version control
- Use strong key sizes (minimum 2048-bit RSA)
- Rotate certificates before expiration
- Keep private keys secure with appropriate file permissions (chmod 600)

