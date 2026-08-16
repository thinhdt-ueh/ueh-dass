import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.state import get_df, require_data, numeric_columns
from utils.stats import cronbach_alpha, alpha_interpretation_key, cr_ave
from utils.i18n import t
from utils.footer import render_footer
from utils.report import add_report_entry


def draw_cfa_diagram(factor_specs, ins: pd.DataFrame, standardized: bool = False):
    """AMOS-style CFA path diagram: item boxes + error terms -> latent ellipses,
    with loadings/variances/covariances labeled. `ins` is semopy's raw
    Model.inspect() output (original lval/rval/op/Estimate/Est. Std columns)."""
    est_col = "Est. Std" if standardized else "Estimate"
    names = [f[0] for f in factor_specs]

    x_err, x_item, x_factor = 0.3, 1.6, 3.6
    item_h, factor_gap = 0.7, 0.9

    item_positions, factor_positions = {}, {}
    y_cursor = 0.0
    for name, items in factor_specs:
        item_ys = [y_cursor - i * item_h for i in range(len(items))]
        for it, y in zip(items, item_ys):
            item_positions[(name, it)] = y
        factor_positions[name] = sum(item_ys) / len(item_ys)
        y_cursor = min(item_ys) - factor_gap

    n_factors = len(names)
    fig_h = max(5.0, (abs(y_cursor) + 2.5) * 0.55)
    fig_w = max(9.0, 9.0 + 0.35 * n_factors)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(-0.3, x_factor + 1.6 + 0.28 * n_factors)
    ax.set_ylim(y_cursor - 1, 2)
    ax.set_aspect("equal")
    ax.axis("off")

    def _val(lval, rval, op):
        row = ins[(ins["lval"] == lval) & (ins["rval"] == rval) & (ins["op"] == op)]
        if row.empty:
            return None
        v = row.iloc[0][est_col]
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    for name, items in factor_specs:
        fy = factor_positions[name]
        for it in items:
            y = item_positions[(name, it)]
            box = FancyBboxPatch(
                (x_item - 0.55, y - 0.2), 1.1, 0.4,
                boxstyle="round,pad=0.02", ec="black", fc="white", zorder=3,
            )
            ax.add_patch(box)
            ax.text(x_item, y, it, ha="center", va="center", fontsize=8, zorder=4)

            ex, ey = x_item - 0.75, y + 0.55
            err = Ellipse((ex, ey), 0.4, 0.32, ec="black", fc="white", zorder=3)
            ax.add_patch(err)
            err_val = _val(it, it, "~~")
            if err_val is not None:
                ax.text(ex, ey, f"{err_val:.2f}", fontsize=6, ha="center", va="center", zorder=4)
            ax.add_patch(FancyArrowPatch(
                (ex, ey - 0.17), (x_item - 0.45, y + 0.13),
                arrowstyle="-|>", mutation_scale=8, color="black", zorder=2,
            ))

            ax.add_patch(FancyArrowPatch(
                (x_factor - 0.6, fy), (x_item + 0.56, y),
                arrowstyle="-|>", mutation_scale=10, color="black", shrinkA=2, shrinkB=2, zorder=2,
            ))
            lv = _val(it, name, "~")
            if lv is not None:
                midx, midy = (x_factor - 0.6 + x_item + 0.56) / 2, (fy + y) / 2
                ax.text(
                    midx, midy + 0.1, f"{lv:.2f}", fontsize=7, ha="center", va="center", zorder=4,
                    bbox=dict(boxstyle="round,pad=0.05", fc="white", ec="none"),
                )

    for name in names:
        fy = factor_positions[name]
        ax.add_patch(Ellipse((x_factor, fy), 1.2, 0.75, ec="black", fc="white", zorder=3))
        ax.text(x_factor, fy, name, ha="center", va="center", fontsize=10, fontweight="bold", zorder=4)
        var_val = _val(name, name, "~~")
        if var_val is not None:
            ax.text(x_factor + 0.7, fy + 0.42, f"{var_val:.2f}", fontsize=7, ha="left", va="center", zorder=4)

    seen_pairs = set()
    cov_rows = ins[
        (ins["op"] == "~~") & (ins["lval"].isin(names)) & (ins["rval"].isin(names)) & (ins["lval"] != ins["rval"])
    ]
    for _, r in cov_rows.iterrows():
        a, b = r["lval"], r["rval"]
        pair = tuple(sorted([a, b]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        ya, yb = factor_positions[a], factor_positions[b]
        dist_idx = abs(names.index(a) - names.index(b))
        rad = 0.12 + 0.10 * dist_idx
        try:
            val = float(r[est_col])
        except (TypeError, ValueError):
            continue
        ax.add_patch(FancyArrowPatch(
            (x_factor + 0.62, ya), (x_factor + 0.62, yb),
            connectionstyle=f"arc3,rad={rad}",
            arrowstyle="<->", mutation_scale=8, color="dimgray", lw=0.9, zorder=1,
        ))
        label_x = x_factor + 0.62 + rad * abs(yb - ya) * 0.5 + 0.15
        ax.text(label_x, (ya + yb) / 2, f"{val:.2f}", fontsize=6, ha="center", va="center", zorder=4)

    fig.tight_layout()
    return fig


def _patch_semopy_bivariate_cdf():
    """semopy.polycorr.bivariate_cdf calls scipy.stats.mvn.mvnun, which scipy
    removed (deprecated sub-module, no longer has that attribute). Replace it
    with an equivalent rectangle-probability computation via the current
    scipy.stats.multivariate_normal API (same math, inclusion-exclusion over
    the bivariate normal CDF). Idempotent - safe to call on every run."""
    import semopy.polycorr as _pc
    from scipy.stats import multivariate_normal as _mvn

    def _bivariate_cdf_fixed(lower, upper, r):
        r = float(np.clip(r, -0.999999, 0.999999))
        dist = _mvn(mean=[0, 0], cov=[[1, r], [r, 1]])
        return (dist.cdf(upper) - dist.cdf([upper[0], lower[1]])
                - dist.cdf([lower[0], upper[1]]) + dist.cdf(lower))

    _pc.bivariate_cdf = _bivariate_cdf_fixed


def polychoric_cov(data: pd.DataFrame, items: list) -> pd.DataFrame:
    """Pairwise polychoric correlation matrix for ordinal (Likert) items.
    Bypasses semopy.polycorr.hetcor(), which has its own separate bug (indexes
    a transposed DataFrame column-style after transposing it to row-style)."""
    _patch_semopy_bivariate_cdf()
    from semopy.polycorr import polychoric_corr

    n_items = len(items)
    mat = np.eye(n_items)
    arrays = {it: data[it].to_numpy(dtype=float) for it in items}
    for i in range(n_items):
        for j in range(i + 1, n_items):
            r = polychoric_corr(arrays[items[i]], arrays[items[j]])
            mat[i, j] = mat[j, i] = r
    return pd.DataFrame(mat, index=items, columns=items)


st.title(f"✅ {t('nav.scale')}")
require_data()
df = get_df()

tab_alpha, tab_efa, tab_cfa = st.tabs([
    f"🎯 {t('sc.alpha.tab')}", f"🧩 {t('sc.efa.tab')}", f"🧭 {t('sc.cfa.tab')}",
])

# ----------------------------------------------------------------------------
# CRONBACH'S ALPHA
# ----------------------------------------------------------------------------
with tab_alpha:
    st.caption(t("sc.alpha.caption"))
    items = st.multiselect(t("sc.alpha.items_select"), numeric_columns(df), key="alpha_items")
    alpha_add_report = st.checkbox(t("report.add_checkbox"), key="alpha_add_report")

    if len(items) < 2:
        st.info(t("sc.alpha.warn_min_items"))
    elif st.button(t("sc.alpha.run_btn"), key="btn_alpha"):
        alpha, item_stats, n_obs = cronbach_alpha(df[items])
        item_stats = item_stats.rename(columns={
            "Biến": t("home.var_name"),
            "Tương quan biến-tổng hiệu chỉnh": t("sc.alpha.col_item_total_corr"),
            "Alpha nếu loại biến": t("sc.alpha.col_alpha_if_deleted"),
        })
        c1, c2 = st.columns([1, 3])
        c1.metric("Cronbach's Alpha", f"{alpha:.3f}")
        c1.caption(t("sc.alpha.n_caption", n=n_obs, k=len(items)))
        c1.info(t(alpha_interpretation_key(alpha)))

        st.markdown(f"##### {t('sc.alpha.item_stats_title')}")
        st.dataframe(item_stats.round(3), width="stretch", hide_index=True)

        weak_items = item_stats[item_stats[t("sc.alpha.col_item_total_corr")] < 0.3][t("home.var_name")].tolist()
        if weak_items:
            st.warning(t("sc.alpha.weak_items_warn", vars=", ".join(weak_items)))
        else:
            st.success(t("sc.alpha.all_good"))

        if alpha_add_report:
            add_report_entry(
                f"{t('sc.alpha.tab')} — {', '.join(items)}",
                [
                    ("text", f"Cronbach's Alpha = {alpha:.3f} (N={n_obs}, k={len(items)})"),
                    ("table", item_stats.round(3)),
                ],
            )
            st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# EFA
# ----------------------------------------------------------------------------
with tab_efa:
    st.caption(t("sc.efa.caption"))
    try:
        from factor_analyzer import FactorAnalyzer
        from factor_analyzer.factor_analyzer import calculate_kmo, calculate_bartlett_sphericity
    except ImportError:
        st.error(t("sc.efa.need_lib"))
        st.stop()

    items = st.multiselect(t("sc.efa.items_select"), numeric_columns(df), key="efa_items")

    c1, c2 = st.columns(2)
    rotation_options = ["varimax", "promax", "oblimin", "quartimax", t("sc.efa.no_rotation")]
    rotation_label = c1.selectbox(t("sc.efa.rotation_label"), rotation_options, key="efa_rotation")
    n_factor_mode_options = [t("sc.efa.mode_auto"), t("sc.efa.mode_manual")]
    n_factor_mode = c2.radio(t("sc.efa.n_factors_label"), n_factor_mode_options, key="efa_nfactor_mode")
    n_factor_manual = None
    if n_factor_mode == t("sc.efa.mode_manual"):
        n_factor_manual = st.number_input(t("sc.efa.n_factors_label"), min_value=1, max_value=max(len(items) - 1, 1), value=2, step=1)

    efa_add_report = st.checkbox(t("report.add_checkbox"), key="efa_add_report")

    if len(items) < 3:
        st.info(t("sc.efa.warn_min_items"))
    elif st.button(t("sc.efa.run_btn"), key="btn_efa"):
        data_efa = df[items].dropna()
        if len(data_efa) < len(items) + 2:
            st.error(t("sc.efa.warn_too_few_obs"))
            st.stop()

        kmo_all, kmo_model = calculate_kmo(data_efa)
        chi2_b, p_b = calculate_bartlett_sphericity(data_efa)

        st.markdown(f"##### {t('sc.efa.kmo_bartlett_title')}")
        k1, k2 = st.columns(2)
        k1.metric(t("sc.efa.kmo_metric"), f"{kmo_model:.3f}")
        k2.write(f"{t('sc.efa.bartlett_label')}: χ² = {chi2_b:.3f}, p-value = {p_b:.4f}")
        if kmo_model < 0.5:
            st.error(t("sc.efa.kmo_bad"))
        elif kmo_model < 0.6:
            st.warning(t("sc.efa.kmo_marginal"))
        else:
            st.success(t("sc.efa.kmo_good"))
        if p_b >= 0.05:
            st.warning(t("sc.efa.bartlett_nonsig"))

        fa_check = FactorAnalyzer(rotation=None)
        fa_check.fit(data_efa)
        ev, _ = fa_check.get_eigenvalues()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(1, len(ev) + 1)), y=ev, mode="lines+markers", name="Eigenvalue"))
        fig.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Eigenvalue = 1")
        fig.update_layout(title=t("sc.efa.scree_title"), xaxis_title=t("sc.efa.factor_axis"), yaxis_title="Eigenvalue")
        st.plotly_chart(fig, width="stretch")

        if n_factor_mode == t("sc.efa.mode_auto"):
            n_factors = int((ev > 1).sum())
            n_factors = max(n_factors, 1)
            n_factors = min(n_factors, len(items) - 1)
        else:
            n_factors = int(n_factor_manual)

        rotation_param = None if rotation_label == t("sc.efa.no_rotation") else rotation_label
        fa = FactorAnalyzer(n_factors=n_factors, rotation=rotation_param)
        fa.fit(data_efa)

        factor_cols = [t("sc.efa.factor_col", i=i + 1) for i in range(n_factors)]
        loadings = pd.DataFrame(fa.loadings_, index=items, columns=factor_cols)
        st.markdown(f"##### {t('sc.efa.loadings_title', n=n_factors)}")

        def _highlight(v):
            return "font-weight: bold; color: #d62728" if abs(v) >= 0.5 else ""

        st.dataframe(loadings.style.format("{:.3f}").map(_highlight), width="stretch")

        communalities = pd.Series(fa.get_communalities(), index=items, name="Communality")
        st.markdown(f"##### {t('sc.efa.communalities_title')}")
        st.dataframe(communalities.round(3).to_frame(), width="stretch")

        var_expl = fa.get_factor_variance()
        var_df = pd.DataFrame(
            var_expl,
            index=[t("sc.efa.row_eigenvalue"), t("sc.efa.row_var_explained"), t("sc.efa.row_cum_var")],
            columns=factor_cols,
        )
        var_df.loc[[t("sc.efa.row_var_explained"), t("sc.efa.row_cum_var")]] *= 100
        st.markdown(f"##### {t('sc.efa.variance_title')}")
        st.dataframe(var_df.round(3), width="stretch")

        total_var = var_df.loc[t("sc.efa.row_cum_var")].iloc[-1]
        if total_var >= 50:
            st.success(t("sc.efa.variance_ok", pct=f"{total_var:.1f}"))
        else:
            st.warning(t("sc.efa.variance_low", pct=f"{total_var:.1f}"))

        if efa_add_report:
            add_report_entry(
                f"{t('sc.efa.tab')} — {', '.join(items)}",
                [
                    ("text", f"KMO = {kmo_model:.3f}; Bartlett's χ² = {chi2_b:.3f}, p = {p_b:.4f}; {n_factors} factor(s)"),
                    ("table", loadings.round(3).reset_index().rename(columns={"index": t("home.var_name")})),
                    ("table", communalities.round(3).to_frame().reset_index().rename(columns={"index": t("home.var_name")})),
                    ("table", var_df.round(3).reset_index().rename(columns={"index": ""})),
                ],
            )
            st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# CFA
# ----------------------------------------------------------------------------
with tab_cfa:
    st.caption(t("sc.cfa.caption"))
    try:
        import semopy
    except ImportError:
        st.error(t("sc.cfa.need_lib"))
        st.stop()

    n_factors_cfa = st.number_input(
        t("sc.cfa.n_factors_label"), min_value=1, max_value=10, value=2, step=1, key="cfa_n_factors",
    )

    factor_specs = []
    for i in range(int(n_factors_cfa)):
        c1, c2 = st.columns([1, 3])
        fname = c1.text_input(t("sc.cfa.factor_name_label", i=i + 1), value=f"F{i + 1}", key=f"cfa_fname_{i}")
        fname = (fname or "").strip() or f"F{i + 1}"
        fitems = c2.multiselect(t("sc.cfa.factor_items_label", name=fname), numeric_columns(df), key=f"cfa_items_{i}")
        factor_specs.append((fname, fitems))

    estimator_choice = st.radio(
        t("sc.cfa.estimator_label"),
        [t("sc.cfa.estimator_ml"), t("sc.cfa.estimator_dwls")],
        key="cfa_estimator", horizontal=True,
    )
    use_dwls = estimator_choice == t("sc.cfa.estimator_dwls")
    if use_dwls:
        st.caption(t("sc.cfa.estimator_dwls_note"))

    cfa_add_report = st.checkbox(t("report.add_checkbox"), key="cfa_add_report")

    if st.button(t("sc.cfa.run_btn"), key="btn_cfa"):
        names = [f[0] for f in factor_specs]
        errors = []
        if len(set(names)) != len(names):
            errors.append(t("sc.cfa.warn_duplicate_names"))
        for name, fitems in factor_specs:
            if len(fitems) < 2:
                errors.append(t("sc.cfa.warn_min_items_per_factor", name=name))

        if errors:
            for e in errors:
                st.error(e)
        else:
            all_items = []
            for _, fitems in factor_specs:
                for it in fitems:
                    if it not in all_items:
                        all_items.append(it)

            cfa_data = df[all_items].dropna()
            if len(cfa_data) < len(all_items) + 5:
                st.error(t("sc.cfa.warn_too_few_obs"))
                st.stop()

            model_desc = "\n".join(f"{name} =~ " + " + ".join(fitems) for name, fitems in factor_specs)
            st.markdown(f"##### {t('sc.cfa.model_spec_title')}")
            st.code(model_desc, language="text")

            if use_dwls:
                many_cats = [it for it in all_items if cfa_data[it].nunique() > 15]
                if many_cats:
                    st.warning(t("sc.cfa.warn_many_categories", vars=", ".join(many_cats)))

            try:
                model = semopy.Model(model_desc)
                if use_dwls:
                    with st.spinner(t("sc.cfa.computing_polychoric")):
                        poly_cov = polychoric_cov(cfa_data, all_items)
                    model.fit(data=cfa_data, cov=poly_cov, obj="DWLS")
                else:
                    model.fit(cfa_data)
                ins = model.inspect(std_est=True)
                stats_df = semopy.calc_stats(model)
            except Exception as e:
                st.error(t("sc.cfa.fit_error", error=str(e)))
                st.stop()

            # ---- Fit indices ----
            st.markdown(f"##### {t('sc.cfa.fit_indices_title')}")
            stats_row = stats_df.iloc[0]
            chi2 = float(stats_row.get("chi2", np.nan))
            dof = float(stats_row.get("DoF", np.nan))
            chi2_p = float(stats_row.get("chi2 p-value", np.nan))
            cfi = float(stats_row.get("CFI", np.nan))
            tli = float(stats_row.get("TLI", np.nan))
            rmsea = float(stats_row.get("RMSEA", np.nan))
            chi2_df_ratio = chi2 / dof if dof else np.nan

            fit_table = pd.DataFrame({
                t("sc.cfa.col_metric"): [
                    "χ²", "df", "p-value", t("sc.cfa.chi2_df_label"), "CFI", "TLI", "RMSEA",
                    "GFI", "AGFI", "NFI", "AIC", "BIC",
                ],
                t("sc.cfa.col_value"): [
                    chi2, dof, chi2_p, chi2_df_ratio, cfi, tli, rmsea,
                    stats_row.get("GFI", np.nan), stats_row.get("AGFI", np.nan),
                    stats_row.get("NFI", np.nan), stats_row.get("AIC", np.nan), stats_row.get("BIC", np.nan),
                ],
            })
            st.dataframe(fit_table.round(3), width="stretch", hide_index=True)

            f1, f2, f3 = st.columns(3)
            if cfi >= 0.95:
                f1.success(t("sc.cfa.interp.cfi_excellent"))
            elif cfi >= 0.90:
                f1.warning(t("sc.cfa.interp.cfi_acceptable"))
            else:
                f1.error(t("sc.cfa.interp.cfi_poor"))

            if tli >= 0.90:
                f2.success(t("sc.cfa.interp.tli_acceptable"))
            else:
                f2.error(t("sc.cfa.interp.tli_poor"))

            if rmsea <= 0.05:
                f3.success(t("sc.cfa.interp.rmsea_good"))
            elif rmsea <= 0.08:
                f3.warning(t("sc.cfa.interp.rmsea_acceptable"))
            else:
                f3.error(t("sc.cfa.interp.rmsea_poor"))

            # ---- Standardized loadings ----
            factor_names_set = set(names)
            loadings_raw = ins[
                (ins["op"] == "~") & (ins["rval"].isin(factor_names_set)) & (ins["lval"].isin(all_items))
            ].copy()
            loadings_raw = loadings_raw.rename(columns={
                "rval": t("sc.cfa.col_factor"),
                "lval": t("sc.cfa.col_item"),
                "Estimate": t("sc.cfa.col_estimate"),
                "Est. Std": t("sc.cfa.col_std_estimate"),
                "Std. Err": t("sc.cfa.col_se"),
                "z-value": t("sc.cfa.col_z"),
                "p-value": t("sc.cfa.col_p"),
            })
            col_factor, col_item = t("sc.cfa.col_factor"), t("sc.cfa.col_item")
            col_est, col_std = t("sc.cfa.col_estimate"), t("sc.cfa.col_std_estimate")
            col_se, col_z, col_p = t("sc.cfa.col_se"), t("sc.cfa.col_z"), t("sc.cfa.col_p")
            loadings_display = loadings_raw[[col_factor, col_item, col_est, col_std, col_se, col_z, col_p]]

            def _fmt(v):
                return f"{v:.3f}" if isinstance(v, (int, float, np.floating)) else str(v)

            def _highlight_loading(v):
                try:
                    return "font-weight: bold; color: #d62728" if abs(float(v)) >= 0.5 else ""
                except (TypeError, ValueError):
                    return ""

            # Pre-format to strings: these columns mix floats with the literal "-"
            # marker semopy uses for fixed reference-indicator rows, which breaks
            # Arrow serialization if left as a mixed-dtype object column.
            loadings_fmt = loadings_display.copy()
            for col in (col_est, col_std, col_se, col_z, col_p):
                loadings_fmt[col] = loadings_fmt[col].apply(_fmt)

            st.markdown(f"##### {t('sc.cfa.loadings_title')}")
            styled = loadings_fmt.style.map(_highlight_loading, subset=[col_std])
            st.dataframe(styled, width="stretch", hide_index=True)

            weak = loadings_raw[loadings_raw[col_std].abs() < 0.5][col_item].tolist()
            if weak:
                st.warning(t("sc.cfa.weak_loadings_warn", vars=", ".join(weak)))
            else:
                st.success(t("sc.cfa.all_loadings_good"))

            # ---- Composite Reliability & AVE ----
            st.markdown(f"##### {t('sc.cfa.cr_ave_title')}")
            cr_ave_rows = []
            ave_by_factor = {}
            for name, _fitems in factor_specs:
                std_loads = loadings_raw.loc[loadings_raw[col_factor] == name, col_std].astype(float).values
                cr_val, ave_val = cr_ave(std_loads)
                ave_by_factor[name] = ave_val
                cr_ave_rows.append({col_factor: name, t("sc.cfa.col_cr"): cr_val, t("sc.cfa.col_ave"): ave_val})
            cr_ave_df = pd.DataFrame(cr_ave_rows)
            st.dataframe(cr_ave_df.round(3), width="stretch", hide_index=True)

            low_cr = cr_ave_df[cr_ave_df[t("sc.cfa.col_cr")] < 0.7][col_factor].tolist()
            low_ave = cr_ave_df[cr_ave_df[t("sc.cfa.col_ave")] < 0.5][col_factor].tolist()
            if low_cr:
                st.warning(t("sc.cfa.cr_low_warn", factors=", ".join(low_cr)))
            if low_ave:
                st.warning(t("sc.cfa.ave_low_warn", factors=", ".join(low_ave)))
            if not low_cr and not low_ave:
                st.success(t("sc.cfa.convergent_ok"))

            # ---- Factor correlations & discriminant validity ----
            fl_mat = None
            if len(names) >= 2:
                corr_mat = pd.DataFrame(np.eye(len(names)), index=names, columns=names)
                cov_rows = ins[
                    (ins["op"] == "~~") & (ins["lval"].isin(factor_names_set))
                    & (ins["rval"].isin(factor_names_set)) & (ins["lval"] != ins["rval"])
                ]
                for _, r in cov_rows.iterrows():
                    corr_mat.loc[r["lval"], r["rval"]] = r["Est. Std"]
                    corr_mat.loc[r["rval"], r["lval"]] = r["Est. Std"]

                st.markdown(f"##### {t('sc.cfa.corr_title')}")
                st.dataframe(corr_mat.round(3), width="stretch")

                st.markdown(f"##### {t('sc.cfa.discriminant_title')}")
                st.caption(t("sc.cfa.discriminant_note"))
                fl_mat = corr_mat.copy()
                for name in names:
                    fl_mat.loc[name, name] = np.sqrt(ave_by_factor[name])
                st.dataframe(fl_mat.round(3), width="stretch")

                fail_pairs = []
                for idx_i, ni in enumerate(names):
                    for nj in names[idx_i + 1:]:
                        if corr_mat.loc[ni, nj] >= min(np.sqrt(ave_by_factor[ni]), np.sqrt(ave_by_factor[nj])):
                            fail_pairs.append(f"{ni}–{nj}")
                if fail_pairs:
                    st.warning(t("sc.cfa.discriminant_fail", pairs=", ".join(fail_pairs)))
                else:
                    st.success(t("sc.cfa.discriminant_ok"))

            # ---- Path diagram (AMOS-style) ----
            st.markdown(f"##### {t('sc.cfa.diagram_title')}")
            gfi_val = float(stats_row.get("GFI", np.nan))
            summary_line = (
                f"Chi-square={chi2:.3f} ; df={dof:.0f} ; P={chi2_p:.3f} ; "
                f"Chi-square/df={chi2_df_ratio:.3f} ; GFI={gfi_val:.3f} ; TLI={tli:.3f} ; "
                f"CFI={cfi:.3f} ; RMSEA={rmsea:.3f}"
            )
            st.code(summary_line, language="text")
            diagram_mode = st.radio(
                t("sc.cfa.diagram_mode_label"),
                [t("sc.cfa.diagram_mode_unstd"), t("sc.cfa.diagram_mode_std")],
                key="cfa_diagram_mode", horizontal=True,
            )
            diagram_std = diagram_mode == t("sc.cfa.diagram_mode_std")
            fig_diagram = draw_cfa_diagram(factor_specs, ins, standardized=diagram_std)
            st.pyplot(fig_diagram)
            st.caption(t("sc.cfa.diagram_caption"))
            diagram_png = io.BytesIO()
            fig_diagram.savefig(diagram_png, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig_diagram)

            if cfa_add_report:
                blocks = [
                    ("text", f"Model: {model_desc}"),
                    ("text", f"Estimator: {'DWLS + Polychoric' if use_dwls else 'ML'}"),
                    (
                        "text",
                        f"χ²({dof:.0f}) = {chi2:.3f}, p = {chi2_p:.4f}; "
                        f"CFI = {cfi:.3f}; TLI = {tli:.3f}; RMSEA = {rmsea:.3f}",
                    ),
                    ("table", fit_table.round(3)),
                    ("table", loadings_fmt),
                    ("table", cr_ave_df.round(3)),
                ]
                if fl_mat is not None:
                    blocks.append(("table", fl_mat.round(3).reset_index().rename(columns={"index": ""})))
                blocks.append(("text", summary_line))
                blocks.append(("image", diagram_png.getvalue()))
                add_report_entry(f"{t('sc.cfa.tab')} — {', '.join(names)}", blocks)
                st.toast(t("report.added_toast"))

render_footer()
