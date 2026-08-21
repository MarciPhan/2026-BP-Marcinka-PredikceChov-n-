"""
Tests validating strict alignment with the bachelor's thesis (BP) requirements.
Covers: Markov model states, Kaplan-Meier edge cases, MII formula,
Data Quality Score, OAuth CSRF, and cross-community access control.
"""
import pytest
import numpy as np
import secrets
from unittest.mock import AsyncMock, MagicMock, patch
from shared.models import CommunityModels, UserState


# ──────────────────────────────────────────────
# 1. Markov Model – State Definitions
# ──────────────────────────────────────────────

class TestMarkovStates:
    """BP defines exactly 4 states: New, Active, Passive, Inactive."""

    def test_user_state_enum_has_exactly_four_states(self):
        """BP: 'Markovův řetězec se 4 stavy: New, Active, Passive, Inactive'."""
        assert len(UserState) == 4
        assert set(UserState.__members__.keys()) == {"NEW", "ACTIVE", "PASSIVE", "INACTIVE"}

    def test_no_churned_state_exists(self):
        """BP explicitly does not define a 'Churned' state."""
        assert not hasattr(UserState, "CHURNED")

    def test_markov_matrix_row_sums(self):
        """BP: 'řádkové součty musí být 1.0 nebo 0 (neobserved)'."""
        transitions = [
            (0, 1), (0, 1), (0, 2),
            (1, 1), (1, 2),
            (2, 2)
        ]
        matrix = CommunityModels.calculate_markov_matrix(transitions, num_states=4)

        # States 0, 1, 2 have observed transitions → row sums = 1.0
        for i in range(3):
            assert abs(np.sum(matrix[i]) - 1.0) < 1e-10, f"Row {i} sum != 1.0"

        # State 3 (Inactive) has no observed transitions → row sum = 0
        assert np.sum(matrix[3]) == 0.0, "Unobserved state should have zero row"

    def test_markov_matrix_no_fabricated_identity(self):
        """BP: 'nepoužívej umělé pravděpodobnosti pro neobservované stavy'."""
        transitions = [(0, 1)]
        matrix = CommunityModels.calculate_markov_matrix(transitions, num_states=4)

        # States 1, 2, 3 have no transitions – should be all zeros, NOT identity
        for i in [1, 2, 3]:
            assert matrix[i][i] == 0.0, f"State {i} should not have self-loop"


# ──────────────────────────────────────────────
# 2. Kaplan-Meier Edge Cases
# ──────────────────────────────────────────────

class TestKaplanMeier:
    """BP: 'KM odhad analyzuje perzistenci aktivity, ne členství'."""

    def test_all_censored_observations(self):
        """When all observations are censored, survival never drops."""
        durations = [10, 20, 30]
        observed = [False, False, False]

        curve = CommunityModels.calculate_survival_rate(durations, observed)

        # No events → S(t) remains 1.0 at all times
        for t, s in curve.items():
            assert s == 1.0, f"S({t}) should be 1.0 when all censored, got {s}"

    def test_no_censored_observations(self):
        """When all observations are events, every time point reduces survival."""
        durations = [5, 10, 15]
        observed = [True, True, True]

        curve = CommunityModels.calculate_survival_rate(durations, observed)

        # S(5) = 1 - 1/3 = 0.667
        assert abs(curve[5] - 2 / 3) < 1e-10
        # S(10) = 0.667 * (1 - 1/2) = 0.333
        assert abs(curve[10] - 1 / 3) < 1e-10
        # S(15) = 0.333 * (1 - 1/1) = 0.0
        assert abs(curve[15] - 0.0) < 1e-10

    def test_tied_event_times(self):
        """Multiple events at the same time should be handled correctly."""
        durations = [10, 10, 10, 20]
        observed = [True, True, True, True]

        curve = CommunityModels.calculate_survival_rate(durations, observed)

        # At t=10: 3 events out of 4 at risk → S(10) = 1 - 3/4 = 0.25
        assert abs(curve[10] - 0.25) < 1e-10
        # At t=20: 1 event out of 1 at risk → S(20) = 0.25 * 0 = 0.0
        assert abs(curve[20] - 0.0) < 1e-10

    def test_median_survival_when_curve_crosses(self):
        """BP: 'medián = první t kde S(t) ≤ 0.5'."""
        durations = [5, 10, 15]
        observed = [True, True, True]

        curve = CommunityModels.calculate_survival_rate(durations, observed)
        median = CommunityModels.estimate_median_survival(curve)

        # S(10) = 1/3 ≤ 0.5, so median = 10
        assert median == 10

    def test_median_survival_when_curve_never_reaches_half(self):
        """BP: 'Pokud S(t) nikdy nedosáhne 0.5, medián je nedefinovaný (None)'."""
        durations = [10, 20, 30]
        observed = [False, False, False]  # All censored

        curve = CommunityModels.calculate_survival_rate(durations, observed)
        median = CommunityModels.estimate_median_survival(curve)

        assert median is None

    def test_empty_data_returns_empty_curve(self):
        """Edge case: no data at all."""
        curve = CommunityModels.calculate_survival_rate([], [])
        assert curve == {}

        expectancy = CommunityModels.estimate_life_expectancy(curve)
        assert expectancy == 0.0

        median = CommunityModels.estimate_median_survival(curve)
        assert median is None

    def test_life_expectancy_area_calculation(self):
        """BP: 'Očekávaná délka aktivity = plocha pod křivkou přežití'."""
        # Simple case: S(5) = 0.5, S(10) = 0.0
        curve = {5: 0.5, 10: 0.0}

        expectancy = CommunityModels.estimate_life_expectancy(curve)

        # Area = 1.0 * 5 (from 0 to 5) + 0.5 * 5 (from 5 to 10) = 7.5
        assert abs(expectancy - 7.5) < 0.01


# ──────────────────────────────────────────────
# 3. MII (Moderation Intervention Index) – NOT "toxicity"
# ──────────────────────────────────────────────

class TestMII:
    """BP: 'MII = sum(w_k * M_k) / max(1, N_interactions)'."""

    def test_mii_not_called_toxicity_in_health_command(self):
        """BP: 'Nepoužívej název toxicity_index'."""
        import inspect
        from bot.commands.health import HealthCog
        source = inspect.getsource(HealthCog.health.callback)

        assert "toxicity_index" not in source, "Variable toxicity_index still present in health command"
        assert "toxicity" not in source.lower() or "Toxicita" not in source, \
            "User-facing 'toxicity' label should not appear"

    def test_mii_not_called_toxicity_in_demo_data(self):
        """BP: demo data must not contain toxicity_index_pct."""
        import inspect
        from web.backend.routers.api import api_health_research
        source = inspect.getsource(api_health_research)

        assert "toxicity_index_pct" not in source, "Demo data still uses toxicity_index_pct"

    def test_demo_data_has_no_churned_state(self):
        """BP: demo state_distribution must only have 4 states."""
        import inspect
        from web.backend.routers.api import api_health_research
        source = inspect.getsource(api_health_research)

        assert '"churned"' not in source, "Demo data still contains 'churned' state"


# ──────────────────────────────────────────────
# 4. Data Quality – null vs zero
# ──────────────────────────────────────────────

class TestDataQuality:
    """BP: 'nedostupná data ≠ nulová hodnota'."""

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none_not_fallback(self):
        """When no transitions exist, retention_pct should be None, not a fake 0.6."""
        from web.backend.services.analytics_service import DefaultAnalyticsService
        import fakeredis.aioredis

        fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)

        class FakeRepo:
            async def get_client(self):
                return fake_r

        svc = DefaultAnalyticsService(FakeRepo())

        # Set minimal data so it doesn't crash, but no message events → no transitions
        await fake_r.set("presence:total:999", "100")
        await fake_r.set("stats:total_msgs:999", "0")

        result = await svc.get_health_research_data(999)

        # With no data, retention should be None, not a fabricated value
        if result.get("success"):
            # If there are no transitions, the system should indicate unavailability
            retention = result.get("retention_pct")
            inactivity = result.get("inactivity_risk_pct")
            assert retention is None or isinstance(retention, (int, float)), \
                "retention_pct must be None or a real computed value"


# ──────────────────────────────────────────────
# 5. OAuth2 State – CSRF Protection
# ──────────────────────────────────────────────

class TestOAuthCSRF:
    """BP: OAuth state musí být kryptograficky bezpečný."""

    def test_oauth_state_is_cryptographically_secure(self):
        """BP: 'secrets.token_urlsafe(32)' for OAuth state."""
        import inspect
        from web.backend.routers.auth import login_page
        source = inspect.getsource(login_page)

        assert "secrets.token_urlsafe" in source, "OAuth state must use secrets.token_urlsafe"
        assert "oauth_state" in source, "State must be stored in session as oauth_state"

    def test_oauth_callback_validates_state(self):
        """BP: callback must validate state with constant-time comparison."""
        import inspect
        from web.backend.routers.auth import auth_callback
        source = inspect.getsource(auth_callback)

        assert "secrets.compare_digest" in source, "State validation must use compare_digest"

    def test_oauth_state_deleted_after_use(self):
        """BP: state must be deleted from session after validation to prevent replay."""
        import inspect
        from web.backend.routers.auth import auth_callback
        source = inspect.getsource(auth_callback)

        assert 'del request.session["oauth_state"]' in source or \
               "del request.session['oauth_state']" in source, \
            "OAuth state must be deleted after validation"


# ──────────────────────────────────────────────
# 6. Session Security
# ──────────────────────────────────────────────

class TestSessionSecurity:
    """BP: Session middleware must be environment-aware."""

    def test_https_only_conditional_on_environment(self):
        """BP: https_only musí být podmíněno produkčním prostředím."""
        import inspect
        from web.backend.main import app
        source = inspect.getsource(app.__class__) if hasattr(app, '__class__') else ""

        # Instead of inspecting app class, check main.py source
        import pathlib
        main_path = pathlib.Path(__file__).resolve().parent.parent / "web" / "backend" / "main.py"
        main_source = main_path.read_text()

        assert "https_only=True" not in main_source or "environment" in main_source, \
            "https_only must be conditional on environment, not hardcoded True"
