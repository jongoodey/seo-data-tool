"""Endpoint page: friendly header + auto-form + Run + results + history/presets."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from seo_analyser.auth import Credentials
from seo_analyser.billing.cost import format_estimate
from seo_analyser.forms.builder import render_form
from seo_analyser.forms.validators import (
    validate_payload, validate_required_fields, validate_required_ids,
)
from seo_analyser.forms.widgets import fields_for
from seo_analyser.labels import family_label, titleize
from seo_analyser.persistence.store import default_store
from seo_analyser.registry import catalogue
from seo_analyser.registry.introspect import EndpointMeta
from seo_analyser.registry.overrides import override_for
from seo_analyser.results.detect import items_table, parse_response
from seo_analyser.results.render import render_result
from seo_analyser.runner.bulk import MAX_ROWS, rows_to_payloads
from seo_analyser.runner.errors import RunError
from seo_analyser.runner.live import run_live
from seo_analyser.runner.lookups import llm_model_choices, models_method_name
from seo_analyser.runner.prereq import (
    Prerequisite, post_prerequisite, prerequisite_for, recent_task_ids,
    wait_until_ready,
)
from seo_analyser.runner.tasks import extract_task_id, fetch_task, run_task, task_not_found
from seo_analyser.ui.home import NAV_KEY
from seo_analyser.ui.share import SHARE_KEY, encode_share


def _go_home() -> None:
    """Reset navigation (runs as an on_click callback, before widgets instantiate)."""
    for key in ("sb.query", "sb.search_pick", "sb.family", "sb.endpoint", NAV_KEY):
        st.session_state.pop(key, None)


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
        if err.kind == "pending" and err.task_id:
            # Keep the id: store a pending run whose response carries it, so the
            # history Fetch button (and the prereq id-harvester) can use it later.
            default_store().add_run(meta.name, meta.family, payload, 0.0, "pending",
                                    response={"tasks": [{"id": err.task_id}]})
            st.info(str(err))
        else:
            st.error(str(err))
        return
    parsed = parse_response(result)
    default_store().add_run(meta.name, meta.family, payload, parsed.cost,
                            "ok" if parsed.ok else "error", response=result)
    render_result(result, endpoint=meta.name)


def render_endpoint_page(creds: Credentials, family: str, endpoint_name: str) -> None:
    meta = catalogue.find_endpoint(family, endpoint_name)
    if meta is None:
        st.warning("Select an endpoint from the sidebar.")
        return

    st.button("← Home", on_click=_go_home, help="Back to the start page")
    override = override_for(family, endpoint_name)
    st.subheader(override.get("title") or titleize(endpoint_name))
    st.caption(f"{family_label(family)}  ·  `{endpoint_name}`")
    if override.get("description"):
        st.write(override["description"])

    if meta.kind == "task":
        st.info("Task-based endpoint: submitting starts a job and polls for results (up to ~2 min).")
    if meta.request_model is None:
        st.warning("This endpoint takes no inputs and isn't runnable yet.")
        _render_history_and_presets(creds)
        return

    key_prefix = f"{family}.{endpoint_name}"
    specs = fields_for(meta.request_model)
    prereq = prerequisite_for(family, specs)
    if prereq:
        _render_prereq_panel(prereq, key_prefix, creds)

    dynamic_choices: dict[str, list[str]] = {}
    with st.spinner("Loading model options..."):
        model_choices = llm_model_choices(meta, creds)
    if model_choices:
        dynamic_choices["model_name"] = model_choices
    elif models_method_name(meta.name):
        st.caption("Couldn't load the model list just now — type a model name "
                   "(e.g. gpt-4.1-mini) or reload the page to retry.")

    payload = render_form(
        meta.request_model,
        key_prefix=key_prefix,
        dynamic_choices=dynamic_choices,
    )

    problems = (validate_payload(payload)
                + validate_required_ids(specs, payload)
                + validate_required_fields(specs, payload))
    for problem in problems:
        st.warning(problem)

    estimate = format_estimate(family)
    if estimate:
        st.caption(estimate)
    run_clicked = st.button("Run", type="primary")
    _render_save_preset(family, endpoint_name, payload)

    if run_clicked:
        if problems:
            st.error("Fix the highlighted field(s) before running — no call was made.")
        elif "model_name" in dynamic_choices and not payload.get("model_name"):
            st.warning("Please choose a model from the dropdown before running.")
        else:
            _run_and_record(meta, payload, creds)

    _render_share(family, endpoint_name, payload)
    _render_bulk(meta, payload, creds)
    _render_history_and_presets(creds)


def _render_prereq_panel(prereq: Prerequisite, key_prefix: str, creds: Credentials) -> None:
    """Get the user a valid task id: pick one from history or start the task here."""
    field_key = f"{key_prefix}.{prereq.id_field}"
    outcome = st.session_state.pop(f"{key_prefix}.prereq_outcome", None)
    if outcome:
        level, message = outcome
        (st.success if level == "ok" else st.warning)(message)
    have_id = bool(st.session_state.get(field_key))
    with st.expander(f"This endpoint reads {prereq.label} — get a task id here",
                     expanded=not have_id):
        ids = recent_task_ids(default_store(), prereq)
        if ids:
            labels = [f"{tid}  ({label})" for tid, label in ids]
            picked = st.selectbox("Recent task ids from your run history", labels,
                                  key=f"{key_prefix}.prereq_pick")
            if st.button("Use this id", key=f"{key_prefix}.prereq_use"):
                st.session_state[field_key] = picked.split("  (")[0]
                st.rerun()
        else:
            st.caption("No matching task ids in your recent run history yet.")

        st.divider()
        if prereq.kind == "onpage_crawl":
            st.caption("Or start a new crawl (the readers below analyse its results):")
            target = st.text_input("Site to crawl (e.g. example.com)",
                                   key=f"{key_prefix}.prereq_target")
            pages = st.number_input("Max pages to crawl", min_value=1, max_value=1000,
                                    value=10, key=f"{key_prefix}.prereq_pages")
            if st.button("Start crawl and wait", key=f"{key_prefix}.prereq_start"):
                if target.strip():
                    payload = {"target": target.strip(), "max_crawl_pages": int(pages)}
                    _start_prereq(prereq, payload, creds, field_key)
                else:
                    st.warning("Enter the site to crawl first.")
        else:
            st.caption("Or create a new SERP task to summarise:")
            kw = st.text_input("Keyword", key=f"{key_prefix}.prereq_keyword")
            col1, col2 = st.columns(2)
            loc = col1.text_input("Location name", value="United Kingdom",
                                  key=f"{key_prefix}.prereq_location")
            lang = col2.text_input("Language name", value="English",
                                   key=f"{key_prefix}.prereq_language")
            if st.button("Create SERP task and wait", key=f"{key_prefix}.prereq_start"):
                if kw.strip():
                    payload = {"keyword": kw.strip(), "location_name": loc.strip(),
                               "language_name": lang.strip()}
                    _start_prereq(prereq, payload, creds, field_key)
                else:
                    st.warning("Enter a keyword first.")


def _start_prereq(prereq: Prerequisite, payload: dict, creds: Credentials,
                  field_key: str) -> None:
    key_prefix = field_key.rsplit(".", 1)[0]
    outcome_key = f"{key_prefix}.prereq_outcome"
    try:
        with st.spinner("Submitting the task..."):
            task_id = post_prerequisite(prereq, payload, creds)
    except RunError as err:
        st.error(str(err))
        return
    # Fill the reader's id field straight away; readiness only affects when Run works.
    st.session_state[field_key] = task_id
    endpoint = "task_post" if prereq.kind == "onpage_crawl" else "google_organic"
    default_store().add_run(endpoint, prereq.family, payload, 0.0, "ok",
                            response={"tasks": [{"id": task_id}]})
    try:
        with st.spinner(f"Task {task_id} submitted — waiting for it to be ready "
                        "(up to ~3 min)..."):
            ready = wait_until_ready(prereq, task_id, creds)
    except RunError as err:
        st.session_state[outcome_key] = (
            "warn", f"Task {task_id} submitted and its id is filled in below, "
                    f"but the readiness check failed: {err}")
        st.rerun()
        return
    if ready:
        st.session_state[outcome_key] = (
            "ok", f"Task {task_id} is ready — its id is filled in below. Hit Run.")
    else:
        st.session_state[outcome_key] = (
            "warn", f"Task {task_id} is still processing — its id is filled in below; "
                    "try Run again in a minute.")
    st.rerun()


def _render_share(family: str, endpoint: str, payload: dict) -> None:
    with st.expander("Share this request"):
        if st.button("Create shareable link", key=f"share.{family}.{endpoint}"):
            st.query_params[SHARE_KEY] = encode_share(family, endpoint, payload)
            st.caption("The link is now in your browser address bar — copy it to share.")


def _render_bulk(meta: EndpointMeta, base_payload: dict, creds: Credentials) -> None:
    if meta.request_model is None:
        return
    with st.expander("Bulk run from CSV"):
        st.caption(
            f"Upload a CSV, choose a column, and run this endpoint for each row "
            f"(up to {MAX_ROWS}). Other inputs above are reused for every row."
        )
        field = st.text_input(
            "Field to fill from the CSV column", value="keyword",
            key=f"bulk_field.{meta.family}.{meta.name}",
        )
        uploaded = st.file_uploader("CSV file", type=["csv"], key=f"bulk_csv.{meta.family}.{meta.name}")
        if uploaded is None:
            return
        df = pd.read_csv(uploaded)
        if df.empty:
            st.warning("That CSV has no rows.")
            return
        column = st.selectbox("Column to use", list(df.columns), key=f"bulk_col.{meta.family}.{meta.name}")
        if st.button("Run bulk", key=f"bulk_run.{meta.family}.{meta.name}"):
            payloads = rows_to_payloads(base_payload, field, df[column].tolist())
            _run_bulk(meta, payloads, creds)


def _run_bulk(meta: EndpointMeta, payloads: list[dict], creds: Credentials) -> None:
    all_rows: list[dict] = []
    total_cost = 0.0
    progress = st.progress(0.0)
    for i, payload in enumerate(payloads):
        try:
            result = _execute(meta, payload, creds)
        except RunError as err:
            st.error(f"Row {i + 1} failed: {err}")
            continue
        parsed = parse_response(result)
        total_cost += parsed.cost
        default_store().add_run(meta.name, meta.family, payload, parsed.cost,
                                "ok" if parsed.ok else "error")
        all_rows.extend(items_table(parsed.items))
        progress.progress((i + 1) / len(payloads))
    st.success(f"Ran {len(payloads)} rows · total cost ${total_cost:.4f}")
    if all_rows:
        st.dataframe(pd.DataFrame(all_rows), use_container_width=True, hide_index=True)


def render_shared_request(creds: Credentials, shared: dict) -> None:
    """Top-of-page banner for a request opened via a shareable link."""
    family, endpoint, params = shared["family"], shared["endpoint"], shared["params"]
    meta = catalogue.find_endpoint(family, endpoint)
    st.info(f"Shared request: **{titleize(endpoint)}** ({titleize(family)})")
    st.json(params, expanded=False)
    if meta is None:
        st.error("That endpoint no longer exists.")
        return
    if st.button("Run shared request", type="primary"):
        _run_and_record(meta, params, creds)


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
    view_target: int | None = None
    fetch_target: tuple[int, str, str] | None = None

    with st.expander("Recent runs"):
        runs = store.recent_runs(15)
        if not runs:
            st.caption("No runs yet.")
        for i, r in enumerate(runs):
            cols = st.columns([5, 2, 1.5, 1.5])
            stamp = r.created_at.strftime("%H:%M:%S") if r.created_at else ""
            cols[0].write(f"`{r.family} · {r.endpoint}`")
            cols[1].caption(f"{stamp} · ${r.cost:.4f}")
            if r.status == "pending":
                if cols[2].button("Fetch", key=f"fetch.{i}",
                                  help="Fetch the finished task's result (no new charge)"):
                    fetch_target = (r.id, r.family, r.endpoint)
            elif cols[2].button("View", key=f"view.{i}", disabled=not r.has_response,
                                help="Show the saved result without re-running"):
                view_target = r.id
            if cols[3].button("Re-run", key=f"rerun.{i}"):
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

    if fetch_target:
        run_id, fam, ep = fetch_target
        saved = store.load_response(run_id) or {}
        pending_id = extract_task_id(saved)
        meta = catalogue.find_endpoint(fam, ep)
        if not (meta and pending_id):
            st.warning("No task id is stored for that run.")
        else:
            try:
                with st.spinner(f"Fetching task {pending_id}..."):
                    result = fetch_task(meta, pending_id, creds)
            except RunError as err:
                st.error(str(err))
                return
            if task_not_found(result):
                st.info("Still processing. Try Fetch again in a minute.")
            else:
                parsed = parse_response(result)
                store.update_run(run_id, cost=parsed.cost,
                                 status="ok" if parsed.ok else "error", response=result)
                st.subheader("Fetched result")
                render_result(result, endpoint=ep)

    if view_target is not None:
        saved = store.load_response(view_target)
        if saved is None:
            st.warning("No saved output for that run — use Re-run.")
        else:
            st.subheader("Saved result")
            render_result(saved, endpoint="saved")

    if rerun_target:
        fam, ep, params = rerun_target
        meta = catalogue.find_endpoint(fam, ep)
        if meta is None:
            st.error(f"Endpoint {fam} · {ep} not found.")
        else:
            st.subheader(f"Re-run: {titleize(ep)}")
            _run_and_record(meta, params, creds)
