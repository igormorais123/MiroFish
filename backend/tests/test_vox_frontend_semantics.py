from pathlib import Path


def test_vox_frontend_distinguishes_verified_c0_from_unverified_without_raw_details():
    component = (
        Path(__file__).parents[2] / "frontend" / "src" / "components" / "Step4Report.vue"
    ).read_text(encoding="utf-8")

    assert "Bloqueado · ${voxClaimLevel.value || 'C0'}" in component
    assert "Não verificado · sem claim" in component
    assert "Execução bloqueada; nenhum claim autorizado" in component
    assert "Integridade e autenticidade não verificadas" in component
    assert 'v-if="voxScienceAuthoritativeDetails" class="vox-science-metrics"' in component
    assert "if (!voxScienceAuthoritativeDetails.value) return []" in component
    assert "verifiedVoxClaim.value?.calibrated === true" in component
    assert "calibration_mode === 'materialized_external_baseline'" in component
    assert "if (verifiedVoxClaim.value?.verified !== true) return []" in component
    assert "Não verificado · C1" not in component
