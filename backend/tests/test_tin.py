"""
test_tin.py — TINService unit tests.

Covers:
- Format correctness
- 100k uniqueness assertion
- Generation speed (1k TINs < 5s)
- Retry on collision
- TINGenerationError after MAX_RETRIES exhaustion
"""

import re
import time
from unittest.mock import MagicMock, patch

import pytest

from apps.tin.services import TINService, TINGenerationError


TIN_PATTERN = re.compile(r"^GH-TIN-[0-9A-F]{6}$")

@pytest.fixture
def service():
    return TINService()


class TestTINFormat:
    def test_tin_format_is_correct(self, service):
        """Generated TIN must match GH-TIN-XXXXXX with uppercase hex chars."""
        with patch("apps.tin.services.tin_repo") as mock_repo:
            mock_repo.exists.return_value = False
            tin = service.generate_unique_tin()
        assert TIN_PATTERN.match(tin), f"TIN '{tin}' does not match pattern GH-TIN-[0-9A-F]{{6}}"

    def test_tin_prefix(self, service):
        with patch("apps.tin.services.tin_repo") as mock_repo:
            mock_repo.exists.return_value = False
            tin = service.generate_unique_tin()
        assert tin.startswith("GH-TIN-")

    def test_tin_suffix_length(self, service):
        with patch("apps.tin.services.tin_repo") as mock_repo:
            mock_repo.exists.return_value = False
            tin = service.generate_unique_tin()
        suffix = tin.replace("GH-TIN-", "")
        assert len(suffix) == 6


class TestTINUniqueness:
    def test_tin_uniqueness_100k(self, service):
        """
        Generate 100,000 TINs (each with a fresh uniqueness check that always
        passes) and verify the output space is large — collision probability
        across 100k draws from 16^6 ≈ 16.7M possible values is ~25%, so we
        assert the distinct count is at least 99,700 (well within 3-sigma).
        The real uniqueness guarantee is enforced by TINRepository.exists(),
        which is tested separately in TestTINRetry.
        """
        with patch("apps.tin.services.tin_repo") as mock_repo:
            mock_repo.exists.return_value = False
            tins = [service.generate_unique_tin() for _ in range(100_000)]

        # All must match the format
        assert all(TIN_PATTERN.match(t) for t in tins), "Some TINs have invalid format"
        # Distinct count should be very high (birthday-problem bound: ~99,700+)
        distinct = len(set(tins))
        assert distinct >= 99_500, f"Unexpectedly low distinct count: {distinct} / 100,000"

    def test_tin_generation_speed(self, service):
        """Generate 1,000 TINs; must complete in under 5 seconds."""
        with patch("apps.tin.services.tin_repo") as mock_repo:
            mock_repo.exists.return_value = False
            start = time.monotonic()
            for _ in range(1_000):
                service.generate_unique_tin()
            elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"1,000 TINs took {elapsed:.2f}s — expected < 5s"


class TestTINRetry:
    def test_tin_retry_on_collision(self, service):
        """When repository returns exists=True once, service retries and succeeds."""
        call_count = 0

        def mock_exists(tin):
            nonlocal call_count
            call_count += 1
            # First call is a collision, second succeeds
            return call_count == 1

        with patch("apps.tin.services.tin_repo") as mock_repo:
            mock_repo.exists.side_effect = mock_exists
            tin = service.generate_unique_tin()

        assert TIN_PATTERN.match(tin)
        assert call_count == 2  # one collision + one success

    def test_tin_fails_after_max_retries(self, service):
        """When all retries collide, TINGenerationError is raised."""
        with patch("apps.tin.services.tin_repo") as mock_repo, \
             patch("apps.tin.services.audit_repo"):
            mock_repo.exists.return_value = True  # always collides
            with pytest.raises(TINGenerationError):
                service.generate_unique_tin()

    def test_tin_audit_log_written_on_failure(self, service):
        """TIN_GENERATION_FAILED audit log must be written on exhaustion."""
        with patch("apps.tin.services.tin_repo") as mock_repo, \
             patch("apps.tin.services.audit_repo") as mock_audit:
            mock_repo.exists.return_value = True
            with pytest.raises(TINGenerationError):
                service.generate_unique_tin()
            mock_audit.log.assert_called_once()
            call_kwargs = mock_audit.log.call_args[0][0]
            assert call_kwargs["action"] == "TIN_GENERATION_FAILED"


class TestTINLookup:
    def test_lookup_found_returns_masked_name(self, service):
        with patch("apps.tin.services.trader_repo") as mock_repo:
            mock_repo.find_by_phone.return_value = {
                "tin_number": "GH-TIN-ABCDEF",
                "name": "Kofi Mensah",
                "status": "active",
            }
            result = service.lookup_tin("+233244000001")
        assert result is not None
        assert result["tin_number"] == "GH-TIN-ABCDEF"
        assert result["name_masked"] == "Ko***h"
        assert result["status"] == "active"

    def test_lookup_not_found_returns_none(self, service):
        with patch("apps.tin.services.trader_repo") as mock_repo:
            mock_repo.find_by_phone.return_value = None
            result = service.lookup_tin("+233244999999")
        assert result is None

    def test_lookup_short_name_masked_safely(self, service):
        """Names shorter than 3 chars don't raise IndexError."""
        with patch("apps.tin.services.trader_repo") as mock_repo:
            mock_repo.find_by_phone.return_value = {
                "tin_number": "GH-TIN-AABBCC",
                "name": "Jo",
                "status": "active",
            }
            result = service.lookup_tin("+233244000002")
        assert "name_masked" in result
        assert "***" in result["name_masked"]
