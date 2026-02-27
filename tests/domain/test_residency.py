"""Tests for Data Residency Service."""
import pytest

from src.domain.services.residency_service import (
    DataResidencyViolationError,
    ResidencyService,
)
from src.domain.value_objects.residency import ResidencyPolicy


class TestResidencyService:
    def setup_method(self):
        self.service = ResidencyService()

    def test_localhost_allowed(self):
        assert self.service.validate_endpoint("localhost") is True

    def test_loopback_allowed(self):
        assert self.service.validate_endpoint("127.0.0.1") is True

    def test_private_ip_allowed(self):
        assert self.service.validate_endpoint("10.0.0.1") is True
        assert self.service.validate_endpoint("192.168.1.100") is True
        assert self.service.validate_endpoint("172.16.0.50") is True

    def test_sa_domain_allowed(self):
        assert self.service.validate_endpoint("fhir.kfshrc.sa") is True
        assert self.service.validate_endpoint("api.moh.gov.sa") is True
        assert self.service.validate_endpoint("nphies.sa") is True

    def test_foreign_domain_rejected(self):
        assert self.service.validate_endpoint("hapi.fhir.org") is False
        assert self.service.validate_endpoint("api.example.com") is False
        assert self.service.validate_endpoint("cloud.us-east.aws.com") is False

    def test_validate_url_sa(self):
        assert self.service.validate_url("https://fhir.kfshrc.sa/baseR4") is True

    def test_validate_url_localhost(self):
        assert self.service.validate_url("postgresql://localhost:5432/omop") is True

    def test_validate_url_foreign(self):
        assert self.service.validate_url("https://hapi.fhir.org/baseR4") is False

    def test_enforce_source_passes(self):
        # Should not raise
        self.service.enforce_source("https://fhir.kfshrc.sa/baseR4")

    def test_enforce_source_fails(self):
        with pytest.raises(DataResidencyViolationError):
            self.service.enforce_source("https://hapi.fhir.org/baseR4")

    def test_enforce_target_passes(self):
        self.service.enforce_target("postgresql://10.0.0.5:5432/omop")

    def test_enforce_target_fails(self):
        with pytest.raises(DataResidencyViolationError):
            self.service.enforce_target("postgresql://us-east.rds.amazonaws.com:5432/omop")

    def test_enforcement_disabled(self):
        policy = ResidencyPolicy(enforce_on_source=False, enforce_on_target=False)
        service = ResidencyService(policy=policy)
        # Should not raise even for foreign hosts
        service.enforce_source("https://hapi.fhir.org/baseR4")
        service.enforce_target("postgresql://foreign.host.com:5432/omop")

    def test_custom_allowed_hostnames(self):
        service = ResidencyService(
            allowed_hostnames=("custom.host.com", "*.internal.net")
        )
        assert service.validate_endpoint("custom.host.com") is True
        assert service.validate_endpoint("app.internal.net") is True
        assert service.validate_endpoint("other.com") is False

    def test_internal_network_check(self):
        assert self.service.is_internal_network("10.0.0.1") is True
        assert self.service.is_internal_network("8.8.8.8") is False

    def test_wildcard_sa_subdomain(self):
        assert self.service.validate_endpoint("deep.sub.kfshrc.sa") is True
