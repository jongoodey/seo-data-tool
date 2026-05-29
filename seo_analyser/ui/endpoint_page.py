"""Endpoint page: friendly header + auto-form + Run + results + history/presets."""
from __future__ import annotations

import streamlit as st

from seo_analyser.auth import Credentials
from seo_analyser.billing.cost import format_estimate
from seo_analyser.forms.builder import render_form
from seo_analyser.labels import titleize
from seo_analyser.persistence.store import default_store
from seo_analyser.registry import catalogue
from seo_analyser.registry.introspect import EndpointMeta
from seo_analyser.results.detect import parse_response
from seo_analyser.results.render import render_result
from seo_analyser.runner.errors import RunError
from seo_analyser.runner.live import run_live
from seo_analyser.runner.lookups import llm_model_choices
from seo_analyser.runner.tasks import run_task


def _execute(meta: EndpointMeta, payload: dict, creds: Credentials) -> dict:
    if meta.kind == "task":
        return run_task(meta, payload, creds)
    return run_live(meta, payload, creds)


def _run_and_record(meta: EndpointMeta, payload: dict, creds: Credentials) -> None:
    spinner = "Task submitted — polling for results (up to ~2 min)..." if meta.kind == "task" \
        else "Calling DataForSEO..."
    try:
        with st.spinner(spinner):
            result = _execute(meta, payload, creds)
    except RunError as err:
        st.error(str(err))
        return
    parsed = parse_response(result)
    default_store().add_run(meta.name, meta.family, payload, parsed.cost,
                            "ok" if parsed.ok else "error")
    render_result(result, endpoint=meta.name)


def render_endpoint_page(creds: Credentials, family: str, endpoint_name: str) -> None:
    meta = catalogue.find_endpoint(family, endpoint_name)
    if meta is None:
        st.warning("Select an endpoint from the sidebar.")
        return

    st.subheader(titleize(endpoint_name))
    st.caption(f"{titleize(family)}  ·  `{endpoint_name}`")

    if meta.kind == "task":
        st.info("Task-based endpoint: submitting starts a job and polls for results (up to ~2 min).")
    if meta.request_model is None:
        st.warning("This endpoint takes no inputs and isn't runnable yet.")
        _render_history_and_presets(creds)
        return

    dynamic_choices: dict[str, list[str]] = {}
    with st.spinner("Loading model options..."):
        model_choices = llm_model_choices(meta, creds)
    if model_choices:
        dynamic_choices["model_name"] = model_choices

    payload = render_form(
        meta.request_model,
        key_prefix=f"{family}.{endpoint_name}",
        dynamic_choices=dynamic_choices,
    )

    estimate = format_estimate(family)
    if estimate:
        st.caption(estimate)
    run_clicked = st.button("Run", type="primary")
    _render_save_preset(family, endpoint_name, payload)

    if run_clicked:
        if "model_name" in dynamic_choices and not payload.get("model_name"):
            st.warning("Please choose a model from the dropdown before running.")
        else:
            _run_and_record(meta, payload, creds)

    _render_history_and_presets(creds)


def _render_save_preset(family: str, endpoint: str, payload: dict) -> None:
    with st.expander("Save these inputs as a preset"):
        name = st.text_input("Preset name", key=f"preset_name.{family}.{endpoint}")
        if st.button("Save preset", key=f"save_preset.{family}.{endpoint}"):
            if name.strip():
                default_store().save_preset(name.strip(), family, endpoint, payload)
                st.success(f"Saved preset '{name.strip()}'.")
            else:
                st.warning("Give the preset a name first.")


def _render_history_and_presets(creds: Credentials) -> None:
    store = default_store()
    rerun_target: tuple[str, str, dict] | None = None

    with st.expander("Recent runs"):
        runs = store.recent_runs(15)
        if not runs:
            st.caption("No runs yet.")
        for i, r in enumerate(runs):
            cols = st.columns([5, 2, 2])
            stamp = r.created_at.strftime("%H:%M:%S") if r.created_at else ""
            cols[0].write(f"`{r.family} · {r.endpoint}`")
            cols[1].caption(f"{stamp} · ${r.cost:.4f}")
            if cols[2].button("Re-run", key=f"rerun.{i}"):
                rerun_target = (r.family, r.endpoint, r.params)

    with st.expander("Saved presets"):
        presets = store.list_presets()
        if not presets:
            st.caption("No presets yet.")
        for i, p in enumerate(presets):
            cols = st.columns([5, 2, 2])
            cols[0].write(f"**{p.name}** — `{p.endpoint}`")
            if cols[1].button("Run", key=f"runpreset.{i}"):
                rerun_target = (p.family, p.endpoint, p.params)
            if cols[2].button("Delete", key=f"delpreset.{i}"):
                store.delete_preset(p.name)
                st.rerun()

    if rerun_target:
        fam, ep, params = rerun_target
        meta = catalogue.find_endpoint(fam, ep)
        if meta is None:
            st.error(f"Endpoint {fam} · {ep} not found.")
        else:
            st.subheader(f"Re-run: {titleize(ep)}")
            _run_and_record(meta, params, creds)
