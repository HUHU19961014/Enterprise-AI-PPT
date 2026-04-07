from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.scenario_generators.build_sie_traceability_onepage import data_gap_vendors, quadrant_groups, vendor_stats


def test_vendor_stats_skip_missing_values_in_average():
    stats = vendor_stats()
    assert stats["一道新能"]["overall"] == 2.33
    assert stats["英发睿能"]["overall"] == 2.17
    assert stats["一道新能"]["missing_count"] == 1
    assert stats["英发睿能"]["coverage"] == 0.92


def test_quadrant_groups_follow_current_dataset_distribution():
    stats = vendor_stats()
    groups = quadrant_groups(stats)
    assert groups["优先合作"] == ["晶科能源", "天合光能", "晶澳科技", "正泰新能"]
    assert groups["重点补强"] == ["横店东磁", "一道新能", "无锡博达", "英发睿能"]
    assert groups["可切入"] == []
    assert groups["观察池"] == []
    assert data_gap_vendors(stats) == ["一道新能", "英发睿能"]
