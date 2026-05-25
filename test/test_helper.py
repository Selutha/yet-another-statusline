from datetime import datetime, timezone, tzinfo

import pytest

import statusline_command as sl
from helper import strip_ansi

_visible_width = sl._visible_width
Renderer = sl.Renderer
RateBucket = sl.RateBucket

_NOW = 1_000_000_000.0  # fixed timestamp for deterministic tests


class TestBurndownTrend:
    """Tests for Renderer.burndown_trend colour buckets and glyph selection."""

    _r = Renderer()
    _W = sl.FIVE_HOUR_MINUTES
    _WU = sl.FIVE_HOUR_WARMUP_MINUTES

    def _trend(self, used_pct: float, delta_minutes: float) -> str:
        resets_at = int(_NOW + delta_minutes * 60)
        return self._r.burndown_trend(used_pct, resets_at, self._W, self._WU, now=_NOW)

    def test_suppressed_no_window(self) -> None:
        assert self._r.burndown_trend(50.0, 0, self._W, self._WU) == ''

    def test_suppressed_expired(self) -> None:
        assert self._r.burndown_trend(50.0, int(_NOW) - 1, self._W, self._WU, now=_NOW) == ''

    def test_suppressed_warmup(self) -> None:
        # 2 min elapsed < 5 min warmup
        resets_at = int(_NOW + 298 * 60)
        assert self._r.burndown_trend(10.0, resets_at, self._W, self._WU, now=_NOW) == ''

    def test_on_pace_dot_positive_boundary(self) -> None:
        # delta = +0.3 → dot
        # elapsed = 150 → ideal = 50%; used = 50.3% → delta = +0.3
        out = self._trend(50.3, 150)
        assert strip_ansi(out) == '·'

    def test_on_pace_dot_negative_boundary(self) -> None:
        # delta = -0.5 → dot
        # elapsed = 150 → ideal = 50%; used = 49.5% → delta = -0.5
        out = self._trend(49.5, 150)
        assert strip_ansi(out) == '·'

    # Over-burn direction ()
    def test_over_burn_safe_bucket(self) -> None:
        # delta = +3.0 → safe colour
        out = self._trend(53.0, 150)
        assert strip_ansi(out) == f'{sl.GLYPH_FAST} 3.0%'
        assert sl.CLR_GREEN_OK in out  # self.safe = CLR_GREEN_OK

    def test_over_burn_warn_bucket(self) -> None:
        # delta = +8.0 → warn colour
        out = self._trend(58.0, 150)
        assert strip_ansi(out) == f'{sl.GLYPH_FAST} 8.0%'
        assert sl.CLR_WARN in out

    def test_over_burn_alert_bucket(self) -> None:
        # delta = +20.0 → alert colour
        out = self._trend(70.0, 150)
        assert strip_ansi(out) == f'{sl.GLYPH_FAST} 20.0%'
        assert sl.CLR_ALERT in out

    # Under-burn direction (▼)
    def test_under_burn_dim_green_bucket(self) -> None:
        # delta = -3.0 → dim green
        out = self._trend(47.0, 150)
        assert strip_ansi(out) == '▼ 3.0%'
        assert sl.CLR_GREEN_DIM in out

    def test_under_burn_mid_green_bucket(self) -> None:
        # delta = -8.0 → mid green (self.safe = CLR_GREEN_OK)
        out = self._trend(42.0, 150)
        assert strip_ansi(out) == '▼ 8.0%'
        assert sl.CLR_GREEN_OK in out

    def test_under_burn_bright_green_bucket(self) -> None:
        # delta = -20.0 → bright green (self.ARROW = CLR_GREEN_BRT)
        out = self._trend(30.0, 150)
        assert strip_ansi(out) == '▼ 20.0%'
        assert sl.CLR_GREEN_BRT in out


class TestHelperBurndownIntegration:
    """Integration tests for burndown trend inside helper()."""

    _FIXED = datetime(2001, 9, 9, 1, 46, 40, tzinfo=timezone.utc)  # == _NOW = 1_000_000_000.0

    def _patch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fixed = self._FIXED

        class _FakeDatetime(datetime):
            @classmethod
            def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
                if tz is not None:
                    return fixed.astimezone(tz)
                return fixed

        monkeypatch.setattr(sl, 'datetime', _FakeDatetime)
        monkeypatch.setattr(sl.time, 'time', lambda: _NOW)

    def test_pre_warmup_no_trend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch)
        # 2 min elapsed < 5 min warmup → no trend
        resets_at = int(_NOW + 298 * 60)
        r = Renderer()
        out = r.helper(RateBucket(used_percentage=60.0, resets_at=resets_at))
        stripped = strip_ansi(out)
        assert sl.GLYPH_FAST not in stripped
        assert '▼' not in stripped
        assert 'T-' in stripped

    def test_mid_window_over_burn_trend_between_pct_and_t(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch)
        # 150 min elapsed, 150 min left → over-burn
        resets_at = int(_NOW + 150 * 60)
        r = Renderer()
        out = r.helper(RateBucket(used_percentage=60.0, resets_at=resets_at))
        stripped = strip_ansi(out)
        assert '60.0%' in stripped
        assert sl.GLYPH_FAST in stripped
        t_pos = stripped.index('T-')
        arrow_pos = stripped.index(sl.GLYPH_FAST)
        assert arrow_pos < t_pos

    def test_expired_window_infinity_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch)
        past_ts = int(_NOW) - 60
        r = Renderer()
        out = r.helper(RateBucket(used_percentage=80.0, resets_at=past_ts))
        stripped = strip_ansi(out)
        assert '∞' in stripped
        assert 'T-' not in stripped

    def test_helper_uses_five_hour_constants(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch)
        # warmup = 5 min, so at 6 min elapsed trend should appear
        resets_at = int(_NOW + 294 * 60)  # 6 min elapsed
        r = Renderer()
        out = r.helper(RateBucket(used_percentage=60.0, resets_at=resets_at))
        stripped = strip_ansi(out)
        assert sl.GLYPH_FAST in stripped or '▼' in stripped or sl.GLYPH_NEUTRAL in stripped


def test_helper_no_usage_no_reset() -> None:
    r = Renderer()
    out = r.helper(RateBucket())
    assert out == '∞'


def test_helper_used_no_reset() -> None:
    r = Renderer()
    out = r.helper(RateBucket(used_percentage=10.0, resets_at=0))
    stripped = strip_ansi(out)
    assert stripped.endswith('∞')
    assert '10.0%' in stripped


def test_helper_reset_in_future(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now = datetime(2026, 5, 20, 12, 0, 0, tzinfo=timezone.utc)

    class _FakeDatetime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
            if tz is not None:
                return fixed_now.astimezone(tz)
            return fixed_now

    monkeypatch.setattr(sl, 'datetime', _FakeDatetime)

    future_ts = int(fixed_now.timestamp()) + 3600
    r = Renderer()
    out = r.helper(RateBucket(used_percentage=50.0, resets_at=future_ts))
    stripped = strip_ansi(out)
    assert '50.0%' in stripped
    assert 'T-' in stripped
