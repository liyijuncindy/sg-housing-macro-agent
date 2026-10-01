"""Independent calendar, chronology and numerical contracts for research checks."""
from copy import deepcopy
import math
import unittest

from housing_agent.research import (_correlation, _features, _walk_forward,
                                    build_research, _vacancy_rate)


def evaluation(key="candidate", frequency="Q", kind="percentage_point", observations=None, unit="Per Cent"):
    return {"id":key,"metadata":{"name":key,"frequency":frequency,"change_kind":kind,"unit":unit},
            "quality":{"eligible":True},"observations":observations or []}


def quarters(start=2015, years=12):
    return [{"period":f"{y}-Q{q}","value":100+(y-start)*4+q} for y in range(start,start+years) for q in range(1,5)]


class ResearchTests(unittest.TestCase):
    def test_calendar_year_baseline_never_substitutes_adjacent_quarter(self):
        rows=quarters(2015,3)
        rows=[r for r in rows if r["period"]!="2015-Q2"]
        _,values,_=_features(evaluation(observations=rows),__import__('datetime').date(2017,12,31))
        self.assertNotIn(2016*4+1,values)
        self.assertEqual(values[2016*4],4)

    def test_monthly_alignment_uses_only_real_quarter_end_month(self):
        rows=[{"period":f"{y}-{m:02}","value":y-2015+m} for y in (2015,2016,2017) for m in range(1,13)]
        rows=[r for r in rows if r["period"]!="2016-06"]
        _,values,points=_features(evaluation(frequency="M",observations=rows),__import__('datetime').date(2017,12,31))
        self.assertNotIn(2016*4+1,values)
        self.assertNotIn(2017*4+1,values)
        self.assertTrue(all(int(p["source_period"][-2:]) in (3,6,9,12) for p in points))

    def test_both_feature_endpoints_after_methodology_floor(self):
        _,values,_=_features(evaluation(observations=quarters(2014,4)),__import__('datetime').date(2017,12,31))
        self.assertEqual(min(values),2016*4)

    def test_basis_point_feature_is_rate_difference_not_percentage_change(self):
        rows=quarters(2015,3)
        _,values,_=_features(evaluation(kind="basis_point",observations=rows),__import__('datetime').date(2017,12,31))
        self.assertEqual(values[2016*4],400)

    def test_zero_percent_denominator_is_omitted(self):
        rows=quarters(2015,3);rows[0]["value"]=0
        _,values,_=_features(evaluation(kind="percent",observations=rows),__import__('datetime').date(2017,12,31))
        self.assertNotIn(2016*4,values)

    def test_correlation_lead_direction_and_min_sample(self):
        features={2016*4+i:float(i*i) for i in range(12)}
        target={k+1:2*v+3 for k,v in features.items()}
        result=_correlation(features,target,1,False)
        self.assertEqual(result["n"],12);self.assertAlmostEqual(result["pearson_r"],1)
        sparse=_correlation(dict(list(features.items())[:7]),target,1,False)
        self.assertIsNone(sparse["pearson_r"]);self.assertEqual(sparse["n"],7)

    def test_constant_feature_does_not_fabricate_correlation(self):
        result=_correlation({i:1 for i in range(10)},{i:i for i in range(10)},0,False)
        self.assertIsNone(result["pearson_r"])

    def test_forecast_training_scaling_and_fit_uses_training_only(self):
        first=2016*4
        features={first+i:float(i) for i in range(40)}
        targets={k:float(2*(k-first-1)+3) for k in range(first,first+41)}
        run=_walk_forward(features,targets);self.assertEqual(run["status"],"evaluated")
        row=run["predictions"][0]
        self.assertEqual(row["training_count"],24)
        self.assertEqual(row["origin_period"],"2022-Q1")
        self.assertEqual(row["target_period"],"2022-Q2")
        self.assertEqual(row["training_feature_mean"],11.5)
        scale=math.sqrt(sum((i-11.5)**2 for i in range(24))/24)
        self.assertAlmostEqual(row["training_feature_scale"],scale)
        # Independent standardized ridge calculation: variance sum is 24,
        # true slope is two, ridge penalty is one.
        self.assertAlmostEqual(row["coefficient_standardized"],2*scale*24/25)
        self.assertAlmostEqual(row["ridge"],26+2*24/25*(24-11.5))
        changed=deepcopy(targets)
        for key in list(changed):
            if key>first+24:changed[key]+=10000
        self.assertEqual(row["ridge"],_walk_forward(features,changed)["predictions"][0]["ridge"])

    def test_all_baselines_share_exact_prediction_dates(self):
        f={2016*4+i:i for i in range(40)};t={2016*4+i:(i%4)-1 for i in range(41)}
        result=_walk_forward(f,t)
        self.assertEqual({m["n"] for m in result["metrics"].values()},{16})
        for row in result["predictions"]:
            self.assertLessEqual(row["training_target_end"],row["origin_period"])
            self.assertEqual(row["last_change"],t[int(row["origin_period"][:4])*4+int(row["origin_period"][-1])-1])

    def test_short_history_is_skipped_not_zero_error(self):
        result=_walk_forward({i:i for i in range(31)},{i:i for i in range(32)})
        self.assertEqual(result["status"],"skipped");self.assertEqual(result["metrics"],{})

    def test_matching_vacancy_rate_and_pp_changes(self):
        v=evaluation("M400841:2",unit="Number Of Units",observations=[{"period":"2025-Q2","value":20},{"period":"2026-Q1","value":18},{"period":"2026-Q2","value":15}])
        s=evaluation("M400841:1",unit="Number Of Units",observations=[{"period":"2025-Q2","value":100},{"period":"2026-Q1","value":120},{"period":"2026-Q2","value":150}])
        r=_vacancy_rate({v['id']:v,s['id']:s},__import__('datetime').date(2026,10,1))
        self.assertEqual(r["latest"]["value"],10)
        self.assertEqual([c["value"] for c in r["changes"]],[-5,-10])
        self.assertEqual(r["latest"]["total_units"],150)

    def test_vacancy_rejects_invalid_pairs_and_missing_denominator(self):
        v=evaluation("M400841:2",unit="Number Of Units",observations=[{"period":"2026-Q2","value":200}])
        s=evaluation("M400841:1",unit="Number Of Units",observations=[{"period":"2026-Q2","value":100}])
        r=_vacancy_rate({v['id']:v,s['id']:s},__import__('datetime').date(2026,10,1))
        self.assertIsNone(r["latest"]);self.assertEqual(r["excluded_invalid_pairs"],1)
        self.assertIsNone(_vacancy_rate({v['id']:v},__import__('datetime').date(2026,10,1))["latest"])

    def test_annual_analysis_never_generates_quarterly_forecast(self):
        annual=evaluation(frequency="A",observations=[{"period":str(y),"value":y-1900} for y in range(2015,2026)])
        outcome=evaluation("outcome",kind="percent",unit="Index",observations=quarters())
        result=build_research([annual],[outcome],"2026-10-01")
        comp=result["comparisons"][0]
        self.assertEqual(comp["analysis_frequency"],"annual")
        self.assertEqual(comp["walk_forward"]["status"],"skipped")
        self.assertTrue(all(r["lag_unit"]=="years" for r in comp["correlations"]))

    def test_complete_comparison_grid_includes_ineligible_and_future_filter(self):
        good=evaluation(observations=quarters());bad=evaluation("bad",observations=[]);bad["quality"]["eligible"]=False
        outcome=evaluation("outcome",kind="percent",unit="Index",observations=quarters())
        result=build_research([good,bad],[outcome],"2026-06-30")
        self.assertEqual(len(result["comparisons"]),2)
        self.assertEqual(result["outcomes"][0]["latest"]["period"],"2026-Q2")
        self.assertTrue(all(p['target_period']<="2026-Q2" for p in result['comparisons'][0]['walk_forward']['predictions']))
        self.assertEqual(result['comparisons'][1]['walk_forward']['status'],'skipped')

    def test_duplicate_or_nonfinite_history_is_not_silently_used(self):
        outcome=evaluation("outcome",kind="percent",unit="Index",observations=quarters())
        candidate=evaluation(observations=[{"period":"2025-Q1","value":1},{"period":"2025-Q1","value":2}])
        result=build_research([candidate],[outcome],"2026-10-01")
        self.assertEqual(result["candidates"][0]["status"],"unavailable")
        self.assertIn("Duplicate",result["candidates"][0]["reason"])


if __name__=="__main__":unittest.main()
