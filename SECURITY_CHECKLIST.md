# Production Security Checklist

## 🔒 Pre-Production Security Audit

Use this checklist before deploying to production to ensure all security measures are in place.

---

## Critical Security Items

### ✅ Authentication & Authorization

- [ ] **JWT Secret Key**
  - [ ] Generated using cryptographically secure random generator
  - [ ] Minimum 32 characters long
  - [ ] Different from default `"change-this-in-production"`
  - [ ] Stored in secrets manager (not in code or `.env` file in repo)
  - [ ] Rotated every 90 days

- [ ] **Authentication Enabled**
  - [ ] `REQUIRE_AUTHENTICATION=true` in production
  - [ ] All endpoints require valid authentication
  - [ ] X-User-Id header blocked in production (dev only)
  - [ ] JWT validation properly implemented

- [ ] **API Keys**
  - [ ] Strong, unique keys generated per user
  - [ ] Keys stored hashed in database (if using database-backed keys)
  - [ ] Key rotation policy in place

---

### ✅ Database Security

- [ ] **Credentials**
  - [ ] Strong password (16+ characters, mixed case, numbers, symbols)
  - [ ] Not using default `postgres/postgres`
  - [ ] Stored in secrets manager
  - [ ] Different for each environment (dev/staging/prod)

- [ ] **Connection Security**
  - [ ] SSL/TLS enabled for database connections
  - [ ] Connection string uses SSL mode (`?sslmode=require`)
  - [ ] Database not exposed to public internet
  - [ ] Firewall rules restrict access to application servers only

- [ ] **Access Control**
  - [ ] Application user has minimal required permissions
  - [ ] No superuser privileges for application
  - [ ] Read-only users for reporting/analytics

---

### ✅ Network Security

- [ ] **HTTPS/TLS**
  - [ ] HTTPS enforced for all endpoints
  - [ ] Valid SSL certificate installed
  - [ ] HTTP redirects to HTTPS
  - [ ] TLS 1.2 or higher required
  - [ ] Strong cipher suites configured

- [ ] **CORS Configuration**
  - [ ] Specific origins listed (not `*`)
  - [ ] Origins use HTTPS
  - [ ] Credentials allowed only for trusted origins

- [ ] **Rate Limiting**
  - [ ] Rate limits configured appropriately
  - [ ] Different limits for different endpoints
  - [ ] DDoS protection in place

---

### ✅ Application Security

- [ ] **Input Validation**
  - [ ] Maximum message length enforced (4000 chars default)
  - [ ] SQL injection protection (using parameterized queries)
  - [ ] XSS protection in place
  - [ ] Request size limits enforced

- [ ] **Error Handling**
  - [ ] Sensitive information not exposed in error messages
  - [ ] Stack traces disabled in production
  - [ ] Errors logged but not returned to client

- [ ] **Secrets Management**
  - [ ] No secrets in code
  - [ ] No secrets in version control
  - [ ] `.env` files in `.gitignore`
  - [ ] Secrets stored in dedicated secrets manager

---

### ✅ Infrastructure Security

- [ ] **Docker Security**
  - [ ] Running as non-root user (`appuser`)
  - [ ] Minimal base image (slim)
  - [ ] No secrets in Dockerfile
  - [ ] Images scanned for vulnerabilities

- [ ] **Container Registry**
  - [ ] Images stored in private registry
  - [ ] Access controls configured
  - [ ] Image signing enabled

- [ ] **Kubernetes/Orchestration** (if applicable)
  - [ ] Network policies configured
  - [ ] Pod security policies enforced
  - [ ] Secrets stored in cluster secrets
  - [ ] RBAC configured correctly

---

### ✅ Monitoring & Logging

- [ ] **Logging**
  - [ ] All authentication attempts logged
  - [ ] Failed login attempts monitored
  - [ ] Sensitive data not logged (passwords, tokens)
  - [ ] Logs retained for 90+ days
  - [ ] Logs shipped to central system

- [ ] **Monitoring**
  - [ ] Health checks configured
  - [ ] Metrics exposed and collected
  - [ ] Alerts configured for critical issues
  - [ ] On-call rotation established

- [ ] **Request Tracing**
  - [ ] Request IDs generated for all requests
  - [ ] Request IDs logged consistently
  - [ ] Distributed tracing enabled

---

### ✅ Data Protection

- [ ] **Encryption at Rest**
  - [ ] Database encryption enabled
  - [ ] Backups encrypted
  - [ ] Disk encryption enabled

- [ ] **Encryption in Transit**
  - [ ] TLS for all external communications
  - [ ] TLS for database connections
  - [ ] TLS for Redis connections

- [ ] **Data Retention**
  - [ ] Retention policy documented
  - [ ] Old data purged automatically
  - [ ] User data deletion implemented (GDPR)

---

### ✅ Backup & Recovery

- [ ] **Backups**
  - [ ] Automated daily backups
  - [ ] Backups stored in separate location
  - [ ] Backups encrypted
  - [ ] Backup restoration tested

- [ ] **Disaster Recovery**
  - [ ] DR plan documented
  - [ ] RTO/RPO defined
  - [ ] Failover procedures tested
  - [ ] Backup restoration verified

---

### ✅ Dependency Management

- [ ] **Vulnerability Scanning**
  - [ ] Dependencies scanned for CVEs
  - [ ] Automated scanning in CI/CD
  - [ ] Critical vulnerabilities addressed immediately

- [ ] **Updates**
  - [ ] Update policy defined
  - [ ] Security patches applied promptly
  - [ ] Dependencies updated monthly

---

### ✅ Compliance & Documentation

- [ ] **Documentation**
  - [ ] Production deployment guide reviewed
  - [ ] Security policies documented
  - [ ] Incident response plan created
  - [ ] Runbook for common issues

- [ ] **Access Control**
  - [ ] Principle of least privilege applied
  - [ ] Admin access logged and audited
  - [ ] Multi-factor authentication for admin access

- [ ] **Compliance** (if applicable)
  - [ ] GDPR compliance verified
  - [ ] HIPAA compliance verified (if handling health data)
  - [ ] SOC 2 requirements met (if required)

---

## Quick Validation Commands

```bash
# Verify production validation works
ENVIRONMENT=production python -c "from app.core.config import settings; settings.validate_production_settings()"

# Check JWT secret strength
echo -n "$JWT_SECRET_KEY" | wc -c  # Should be 32+

# Verify HTTPS redirect
curl -I http://yourdomain.com  # Should redirect to https://

# Test authentication required
curl http://yourdomain.com/api/chat  # Should return 401

# Check health endpoint
curl https://yourdomain.com/health

# Verify metrics endpoint
curl https://yourdomain.com/metrics | grep http_requests_total
```

---

## Security Testing

### Penetration Testing

Before production deployment, conduct:

1. **Authentication Testing**
   - Token expiration
   - Token signature verification
   - Invalid token handling
   - Authorization bypass attempts

2. **Input Validation Testing**
   - SQL injection attempts
   - XSS attempts
   - Large payload handling
   - Special character handling

3. **API Security Testing**
   - Rate limit bypass attempts
   - CORS policy verification
   - CSRF protection
   - API endpoint enumeration

4. **Infrastructure Testing**
   - Network segmentation
   - Firewall rules
   - Port scanning
   - Service enumeration

---

## Incident Response

### Security Incident Procedure

1. **Detection**
   - Monitor alerts
   - Review logs for anomalies
   - Check failed authentication attempts

2. **Response**
   - Isolate affected systems
   - Rotate compromised credentials
   - Block malicious IPs
   - Notify stakeholders

3. **Recovery**
   - Restore from backups if needed
   - Patch vulnerabilities
   - Verify system integrity

4. **Post-Incident**
   - Document incident
   - Update security measures
   - Conduct retrospective
   - Improve monitoring

---

## Regular Security Reviews

**Monthly:**
- [ ] Review access logs
- [ ] Check for failed authentication attempts
- [ ] Update dependencies
- [ ] Review security alerts

**Quarterly:**
- [ ] Rotate JWT secret key
- [ ] Review and update firewall rules
- [ ] Conduct security training
- [ ] Review backup procedures

**Annually:**
- [ ] Full security audit
- [ ] Penetration testing
- [ ] Review and update security policies
- [ ] Disaster recovery drill

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Security is an ongoing process, not a one-time checklist!**

Stay vigilant and keep your systems updated.

