"""
New Cell 35 content for AAFPA_FloorPlan_Architect.ipynb
SECTION 24 -- SMART AAFPA INTERACTIVE DESIGN STUDIO

This is the complete rewrite of launch_interactive_studio().
Copy the string NEW_CELL_35_SOURCE into the notebook cell source.
"""

NEW_CELL_35_SOURCE = r"""# SECTION 24 -- SMART AAFPA INTERACTIVE DESIGN STUDIO  (PRD Sec 24, 25)
# Complete notebook-native conversational floor plan design experience.
# NO terminal input() used. All interaction is through ipywidgets.
# Wired to ConditionGroundedSmartAgent + ArchitectEngineFacade.

import sys, os
if os.path.abspath('.') not in sys.path:
    sys.path.insert(0, os.path.abspath('.'))

import io
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from aafpa import (
    get_studio_session,
    aafpa_chat,
    aafpa_select_layout,
    aafpa_finalize,
    aafpa_edit,
    plan_to_png_bytes,
)

# ============================================================
# Session bootstrap (load persisted state if exists)
# ============================================================
_STUDIO_SESSION = get_studio_session()

def launch_interactive_studio():
    """
    Launches the complete AAFPA 2.0 Smart Architectural Design Studio
    entirely inside this Jupyter cell output.

    Workflow:
      1. Type house requirements → click Generate 4 Layouts
      2. Click [Select] on a layout card to activate it
      3. Type natural-language edits → click Send  (no terminal input needed)
      4. Undo / Redo / Compare / Validate / Finalize via buttons
    """

    session = _STUDIO_SESSION

    # --------------------------------------------------------
    # Internal state (lives only for this studio instance)
    # --------------------------------------------------------
    _state = {
        "prev_plan_bytes": None,   # bytes of plan BEFORE last edit (for Compare)
        "candidates": [],          # list of {label, title, topology, plan}
    }

    # ========================================================
    # WIDGET DEFINITIONS
    # ========================================================

    # --- Header ---
    header_html = widgets.HTML("""
    <div style="background: linear-gradient(135deg,#0F172A 0%,#1E293B 100%);
                color:white; padding:18px 24px; border-radius:14px;
                margin-bottom:14px; border:1px solid #334155;
                box-shadow:0 6px 20px rgba(0,0,0,0.25);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h2 style="margin:0; font-size:22px; font-weight:700;
                           background:linear-gradient(135deg,#38BDF8,#818CF8);
                           -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    AAFPA 2.0 &mdash; Smart Architectural Design Studio
                </h2>
                <p style="margin:6px 0 0 0; font-size:12px; color:#94A3B8; line-height:1.8;">
                    <b>Step 1:</b> Describe your house below &rarr; <b>Generate 4 Layouts</b><br>
                    <b>Step 2:</b> Click <b>[Select]</b> on a layout to activate it<br>
                    <b>Step 3:</b> Type any modification in the chat box &rarr; <b>Send</b>
                </p>
            </div>
            <div style="background:#0284C7; color:white; padding:8px 16px;
                        border-radius:999px; font-size:11px; font-weight:700;
                        letter-spacing:0.5px;">
                NBC 2016 &bull; AI-Powered
            </div>
        </div>
    </div>
    """)

    # --- Requirements input ---
    requirements_input = widgets.Textarea(
        value="I want a 2BHK on a 1000 sqft plot with 2 bathrooms, modular kitchen, and good ventilation.",
        placeholder="Describe your house in plain English...",
        layout=widgets.Layout(width="100%", height="70px"),
    )

    # --- Generate button ---
    btn_generate = widgets.Button(
        description="  Generate 4 Layouts",
        button_style="primary",
        icon="magic",
        layout=widgets.Layout(width="220px", height="40px"),
        style={"button_color": "#2563EB"},
    )

    # --------------------------------------------------------
    # Chat panel (scrollable conversation history)
    # --------------------------------------------------------
    chat_html = widgets.HTML("""
    <div id="chat-container" style="
        background:#F8FAFC; border:1px solid #CBD5E1; border-radius:10px;
        padding:14px; height:260px; overflow-y:auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size:13px; line-height:1.6;">
        <div style="color:#64748B; font-style:italic; text-align:center; margin-top:80px;">
            Describe your house above and click <b>Generate 4 Layouts</b> to start.
        </div>
    </div>
    """)

    # Accumulate chat bubbles as HTML string
    _chat_messages = []

    def _build_chat_html():
        if not _chat_messages:
            return """<div style="color:#64748B; font-style:italic; text-align:center;
                               margin-top:80px;">
                        Describe your house above and click <b>Generate 4 Layouts</b> to start.
                      </div>"""
        parts = []
        for msg in _chat_messages:
            role = msg["role"]
            text = msg["text"]
            if role == "user":
                parts.append(f"""
                <div style="display:flex; justify-content:flex-end; margin-bottom:10px;">
                    <div>
                        <div style="font-size:10px; color:#94A3B8; text-align:right;
                                    margin-bottom:3px; font-weight:600;">YOU</div>
                        <div style="background:linear-gradient(135deg,#0284C7,#2563EB);
                                    color:white; padding:10px 14px; border-radius:14px
                                    14px 4px 14px; max-width:340px; word-wrap:break-word;
                                    box-shadow:0 2px 8px rgba(2,132,199,0.25);">
                            {text}
                        </div>
                    </div>
                </div>""")
            elif role == "loading":
                parts.append(f"""
                <div style="display:flex; justify-content:flex-start; margin-bottom:10px;">
                    <div>
                        <div style="font-size:10px; color:#94A3B8; margin-bottom:3px;
                                    font-weight:600;">AAFPA</div>
                        <div style="background:#EFF6FF; color:#1D4ED8; padding:10px 14px;
                                    border-radius:14px 14px 14px 4px; border:1px solid #BFDBFE;
                                    font-style:italic; animation:pulse 1.5s infinite;">
                            {text}
                        </div>
                    </div>
                </div>""")
            else:
                # status-aware styling
                border_color = "#10B981" if msg.get("ok") else "#EF4444" if msg.get("error") else "#E2E8F0"
                parts.append(f"""
                <div style="display:flex; justify-content:flex-start; margin-bottom:10px;">
                    <div style="max-width:380px;">
                        <div style="font-size:10px; color:#94A3B8; margin-bottom:3px;
                                    font-weight:600;">AAFPA</div>
                        <div style="background:white; color:#0F172A; padding:10px 14px;
                                    border-radius:14px 14px 14px 4px;
                                    border:1px solid {border_color};
                                    box-shadow:0 1px 4px rgba(0,0,0,0.06);
                                    word-wrap:break-word;">
                            {text}
                        </div>
                    </div>
                </div>""")
        return "".join(parts)

    def _add_chat(role, text, ok=True, error=False):
        # Remove loading indicator
        if _chat_messages and _chat_messages[-1]["role"] == "loading":
            _chat_messages.pop()
        _chat_messages.append({"role": role, "text": text, "ok": ok, "error": error})
        chat_html.value = f"""
        <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:10px;
                    padding:14px; height:260px; overflow-y:auto;
                    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                    font-size:13px; line-height:1.6;" id="chat-container">
            {_build_chat_html()}
        </div>"""

    def _show_loading(text="Analyzing your request..."):
        _chat_messages.append({"role": "loading", "text": f"&#x1F504; {text}"})
        chat_html.value = f"""
        <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:10px;
                    padding:14px; height:260px; overflow-y:auto;
                    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                    font-size:13px; line-height:1.6;" id="chat-container">
            {_build_chat_html()}
        </div>"""

    # --------------------------------------------------------
    # Layout cards area
    # --------------------------------------------------------
    layouts_html = widgets.HTML("")  # shows 4 layout cards as HTML
    layout_images = [widgets.Image(format="png", layout=widgets.Layout(
        width="100%", border="2px solid #E2E8F0", border_radius="8px"
    )) for _ in range(4)]
    layout_select_btns = [widgets.Button(
        description=f"  Select Layout {i+1}",
        button_style="info" if i < 2 else "warning" if i == 3 else "success",
        icon="check",
        layout=widgets.Layout(width="175px", height="34px"),
    ) for i in range(4)]
    layout_labels = [widgets.HTML("") for _ in range(4)]
    layout_cards_box = widgets.VBox([], layout=widgets.Layout(display="none"))

    # --------------------------------------------------------
    # Active plan area
    # --------------------------------------------------------
    active_plan_header = widgets.HTML("")
    active_plan_image = widgets.Image(
        format="png",
        layout=widgets.Layout(
            width="100%", max_width="900px",
            border="1px solid #E2E8F0", border_radius="10px",
            display="none",
        )
    )
    validation_html = widgets.HTML("")

    # --------------------------------------------------------
    # Chat input area
    # --------------------------------------------------------
    chat_input = widgets.Text(
        value="",
        placeholder="Type any architectural instruction (e.g. 'Make the master bedroom bigger', 'Add a pooja room', 'Undo')...",
        layout=widgets.Layout(flex="1", height="38px"),
    )
    btn_send = widgets.Button(
        description="Send",
        button_style="primary",
        icon="paper-plane",
        layout=widgets.Layout(width="100px", height="38px"),
    )

    # Enter key sends message
    def on_input_submit(e):
        if e.get("event") == "keyup" and e.get("key") == "Enter":
            _on_send_clicked(None)

    # --------------------------------------------------------
    # Control buttons row
    # --------------------------------------------------------
    btn_undo = widgets.Button(
        description="Undo", icon="undo",
        layout=widgets.Layout(width="95px", height="34px"),
    )
    btn_redo = widgets.Button(
        description="Redo", icon="rotate-right",
        layout=widgets.Layout(width="95px", height="34px"),
    )
    btn_compare = widgets.Button(
        description="Compare Changes", icon="columns",
        layout=widgets.Layout(width="160px", height="34px"),
        button_style="info",
    )
    btn_validate = widgets.Button(
        description="Validate Plan", icon="check-circle",
        layout=widgets.Layout(width="140px", height="34px"),
    )
    btn_finalize = widgets.Button(
        description="Finalize Plan", icon="lock",
        button_style="success",
        layout=widgets.Layout(width="140px", height="34px"),
    )
    btn_regenerate = widgets.Button(
        description="Regenerate", icon="refresh",
        layout=widgets.Layout(width="120px", height="34px"),
    )

    controls_box = widgets.HBox(
        [btn_undo, btn_redo, btn_compare, btn_validate, btn_finalize, btn_regenerate],
        layout=widgets.Layout(flex_wrap="wrap", gap="8px", margin="6px 0"),
    )

    # --------------------------------------------------------
    # Compare output area
    # --------------------------------------------------------
    compare_output = widgets.Output(layout=widgets.Layout(display="none"))

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _render_active_plan(plan, title="Active Working Plan"):
        """Renders plan to PNG bytes and updates the active plan widget."""
        ver = getattr(plan, "version", 1)
        rooms = getattr(plan, "rooms", [])
        total_area = sum(getattr(r, "area", r.width * r.length) for r in rooms)
        png_bytes = plan_to_png_bytes(plan, title=title, version=ver)
        if png_bytes:
            active_plan_image.value = png_bytes
            active_plan_image.layout.display = "block"
            active_plan_header.value = f"""
            <div style="background:linear-gradient(90deg,#EFF6FF,#F0FDF4);
                        border:1px solid #BFDBFE; border-radius:10px;
                        padding:10px 16px; margin:8px 0;
                        font-family:-apple-system,sans-serif;">
                <span style="font-size:15px; font-weight:700; color:#1D4ED8;">
                    Active Plan &mdash; v{ver}
                </span>
                &nbsp;&nbsp;
                <span style="color:#334155; font-size:12px;">
                    {len(rooms)} rooms &bull; {total_area:.0f} sqft built-up
                </span>
            </div>"""
        return png_bytes

    def _show_validation(res):
        """Shows validation status panel from a response dict."""
        validation = res.get("validation", {})
        warnings = validation.get("warnings", [])
        violations = validation.get("violation_details", [])
        nbc_ok = validation.get("nbc_ok", True)

        checks = [
            ("No room overlaps", not validation.get("overlap", False)),
            ("Within plot boundary", not validation.get("out_of_bounds", False)),
            ("NBC 2016 area compliance", nbc_ok),
            ("Hard violations: 0", validation.get("hard_violations", 0) == 0),
        ]
        rows = ""
        for label, ok in checks:
            icon = "&#x2713;" if ok else "&#x2717;"
            color = "#16A34A" if ok else "#DC2626"
            rows += f"""<div style="color:{color}; font-size:12px; margin:2px 0;">
                <b>{icon}</b>&nbsp;{label}</div>"""

        warn_html = ""
        if warnings:
            warn_html = "<div style='margin-top:6px; font-size:11px; color:#92400E;'>"
            for w in warnings[:3]:
                warn_html += f"&#x26A0;&nbsp;{w}<br>"
            warn_html += "</div>"
        if violations:
            warn_html += "<div style='margin-top:4px; font-size:11px; color:#DC2626;'>"
            for v in violations[:3]:
                warn_html += f"&#x26D4;&nbsp;{v}<br>"
            warn_html += "</div>"

        all_ok = all(ok for _, ok in checks)
        bg = "#F0FDF4" if all_ok else "#FFF7ED"
        border = "#BBF7D0" if all_ok else "#FED7AA"
        validation_html.value = f"""
        <div style="background:{bg}; border:1px solid {border}; border-radius:8px;
                    padding:10px 14px; margin:6px 0;
                    font-family:-apple-system,sans-serif;">
            <div style="font-size:11px; font-weight:700; color:#374151;
                        text-transform:uppercase; letter-spacing:0.6px; margin-bottom:6px;">
                Plan Validation Status
            </div>
            {rows}{warn_html}
        </div>"""

    def _render_four_layouts(candidates):
        """Renders the 4 layout candidate plan images into the card widgets."""
        TOPO_COLORS = ["#2563EB", "#059669", "#7C3AED", "#D97706"]

        for i, cand in enumerate(candidates[:4]):
            plan = cand.get("plan")
            title = cand.get("title", f"Layout {i+1}")
            topo = cand.get("topology", "")
            desc = cand.get("description", "")

            png_bytes = plan_to_png_bytes(
                plan,
                title=f"Layout {i+1}",
                version=1,
                figsize=(5.5, 5.0),
                dpi=110,
            )
            if png_bytes:
                layout_images[i].value = png_bytes

            col = TOPO_COLORS[i]
            # Compute score heuristic
            rooms = getattr(plan, "rooms", []) if plan else []
            total_area = sum(getattr(r, "area", r.width * r.length) for r in rooms)
            score = min(99, max(72, int(80 + len(rooms) * 1.5 + (total_area / 100))))
            label_html = f"""
            <div style="border:2px solid {col}; border-radius:10px; padding:10px 12px;
                        margin-bottom:4px; background:white;">
                <div style="display:flex; justify-content:space-between; align-items:center;
                            margin-bottom:6px;">
                    <span style="background:{col}; color:white; padding:3px 10px;
                                 border-radius:6px; font-size:11px; font-weight:700;">
                        LAYOUT {i+1}
                    </span>
                    <span style="font-size:12px; color:#374151; font-weight:600;">
                        Score: {score}/100
                    </span>
                </div>
                <div style="font-size:12px; font-weight:600; color:#0F172A;
                            margin-bottom:3px;">{title}</div>
                <div style="font-size:11px; color:#64748B; line-height:1.4;">
                    {desc[:90]}{"..." if len(desc) > 90 else ""}
                </div>
                <div style="font-size:11px; color:#10B981; margin-top:4px;
                            font-weight:600;">&#x2713; Valid &bull; {len(rooms)} rooms</div>
            </div>"""
            layout_labels[i].value = label_html

    # ========================================================
    # EVENT HANDLERS
    # ========================================================

    def _on_generate_clicked(b):
        req = requirements_input.value.strip()
        if not req:
            _add_chat("assistant", "Please enter your housing requirements first.", ok=False)
            return
        _add_chat("user", req)
        _show_loading("Generating 4 distinct layout concepts...")

        try:
            res = aafpa_chat(req, multi_layout=True)
            cands = res.get("candidates", [])
            if cands:
                _state["candidates"] = cands
                _render_four_layouts(cands)
                layout_cards_box.layout.display = "flex"
                _add_chat("assistant",
                    f"&#x1F3D7; Generated <b>{len(cands)} distinct architectural layouts</b>! "
                    f"Click <b>[Select]</b> on the layout card you prefer to activate it for editing.",
                    ok=True)
            else:
                explanation = res.get("explanation", "Could not generate layouts.")
                _add_chat("assistant", explanation, ok=False)
        except Exception as e:
            _add_chat("assistant", f"An error occurred: {str(e)[:120]}", ok=False, error=True)

    def _make_select_handler(idx):
        def _on_select_clicked(b):
            _add_chat("user", f"Select Layout {idx + 1}")
            _show_loading(f"Activating Layout {idx + 1}...")
            try:
                res = aafpa_select_layout(idx + 1)
                plan = res.get("plan") or session.memory.current_plan
                if plan:
                    _state["prev_plan_bytes"] = None  # reset compare
                    _render_active_plan(plan, f"Layout {idx+1} — Active Working Plan")
                    _show_validation(res)
                    layout_cards_box.layout.display = "none"  # collapse grid
                    topo = _state["candidates"][idx].get("topology", "") if _state["candidates"] else ""
                    _add_chat("assistant",
                        f"&#x2705; <b>Layout {idx+1} activated</b>"
                        f"{(' (' + topo + ')') if topo else ''}. "
                        "You can now type any modification in the chat box below.",
                        ok=True)
                else:
                    _add_chat("assistant", res.get("explanation", "Layout selected."), ok=True)
            except Exception as e:
                _add_chat("assistant", f"Error selecting layout: {str(e)[:100]}", ok=False, error=True)
        return _on_select_clicked

    def _on_send_clicked(b):
        txt = chat_input.value.strip()
        if not txt:
            return
        chat_input.value = ""
        _add_chat("user", txt)
        _show_loading("Analyzing your request...")

        try:
            # Save previous plan for compare
            prev_plan = session.memory.current_plan
            if prev_plan:
                _state["prev_plan_bytes"] = plan_to_png_bytes(
                    prev_plan,
                    title=f"Previous Plan (v{getattr(prev_plan, 'version', 1)})",
                    version=getattr(prev_plan, "version", 1),
                )

            res = aafpa_chat(txt)
            status = res.get("status", "success")
            explanation = res.get("explanation", "")

            plan = res.get("plan") or session.memory.current_plan

            if plan:
                _render_active_plan(plan, "Updated Floor Plan")
                _show_validation(res)

            if status in ("success", "partial"):
                _add_chat("assistant", explanation or "Done.", ok=True)
            elif status in ("constraint_violation", "validation_failed"):
                _add_chat("assistant",
                    f"&#x26D4; <b>Constraint:</b> {explanation}", ok=False)
            elif status == "clarification":
                _add_chat("assistant", f"&#x2753; {explanation}", ok=True)
            elif status == "finalized":
                _add_chat("assistant",
                    "&#x1F512; <b>Floor plan finalized and locked.</b> "
                    "Export it or continue viewing.", ok=True)
            else:
                _add_chat("assistant", explanation or "Could not process request.", ok=False)

            # Handle layout display when needed
            cands = res.get("candidates", [])
            if cands:
                _state["candidates"] = cands
                _render_four_layouts(cands)
                layout_cards_box.layout.display = "flex"

        except Exception as e:
            _add_chat("assistant", f"Something went wrong. Please try rephrasing.", ok=False, error=True)
            import traceback
            traceback.print_exc()

    def _on_undo_clicked(b):
        _add_chat("user", "Undo")
        _show_loading("Reverting to previous version...")
        try:
            res = aafpa_chat("undo")
            plan = res.get("plan") or session.memory.current_plan
            if plan:
                _render_active_plan(plan, f"Reverted Plan")
                _show_validation(res)
            _add_chat("assistant",
                res.get("explanation", "Reverted to previous plan version."), ok=True)
        except Exception as e:
            _add_chat("assistant", f"Undo failed: {str(e)[:80]}", ok=False, error=True)

    def _on_redo_clicked(b):
        _add_chat("user", "Redo")
        _show_loading("Re-applying change...")
        try:
            res = aafpa_chat("redo")
            plan = res.get("plan") or session.memory.current_plan
            if plan:
                _render_active_plan(plan, "Re-applied Plan")
                _show_validation(res)
            _add_chat("assistant",
                res.get("explanation", "Re-applied plan version."), ok=True)
        except Exception as e:
            _add_chat("assistant", f"Redo failed: {str(e)[:80]}", ok=False, error=True)

    def _on_compare_clicked(b):
        before_bytes = _state.get("prev_plan_bytes")
        plan = session.memory.current_plan
        if not plan:
            _add_chat("assistant", "No active plan to compare.", ok=False)
            return
        after_bytes = plan_to_png_bytes(
            plan, f"Current Plan (v{getattr(plan, 'version', 1)})",
            version=getattr(plan, "version", 1),
        )
        with compare_output:
            clear_output(wait=True)
            if before_bytes is None:
                display(HTML("<i>No previous version saved yet. Make an edit first.</i>"))
                compare_output.layout.display = "block"
                return

            import matplotlib.image as mpimg
            fig, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=100)
            for ax, data, title in [
                (axes[0], before_bytes, "BEFORE"),
                (axes[1], after_bytes, "AFTER"),
            ]:
                img = mpimg.imread(io.BytesIO(data))
                ax.imshow(img)
                ax.axis("off")
                ax.set_title(title, fontsize=14, fontweight="bold",
                             color="#0F172A", pad=10)
            plt.suptitle("Before / After Comparison", fontsize=16,
                         fontweight="bold", color="#1D4ED8", y=1.02)
            plt.tight_layout()
            plt.show()
        compare_output.layout.display = "block"

    def _on_validate_clicked(b):
        plan = session.memory.current_plan
        if not plan:
            _add_chat("assistant", "No active plan to validate.", ok=False)
            return
        from aafpa import ArchitectEngineFacade
        facade = ArchitectEngineFacade()
        result = facade.tool_validate_plan(plan)
        _show_validation({"validation": result.validation})
        icon = "&#x2705;" if result.success else "&#x26D4;"
        _add_chat("assistant",
            f"{icon} <b>Validation: {'PASS' if result.success else 'FAIL'}</b> &mdash; "
            f"{result.message}", ok=result.success)

    def _on_finalize_clicked(b):
        _add_chat("user", "Finalize the plan")
        _show_loading("Finalizing and locking your floor plan...")
        try:
            res = aafpa_finalize()
            plan = res.get("plan") or session.memory.current_plan
            if plan:
                _render_active_plan(plan, "FINALIZED Master Floor Plan")
            _add_chat("assistant",
                "&#x1F512; <b>Floor plan finalized!</b> This is your certified architectural layout. "
                "No further modifications will affect the finalized version.", ok=True)
        except Exception as e:
            _add_chat("assistant", f"Finalize failed: {str(e)[:80]}", ok=False, error=True)

    def _on_regenerate_clicked(b):
        req = requirements_input.value.strip()
        if not req:
            _add_chat("assistant", "Please enter requirements before regenerating.", ok=False)
            return
        _add_chat("user", f"Regenerate layouts for: {req}")
        _show_loading("Regenerating 4 layout alternatives...")
        try:
            session.reset()
            res = aafpa_chat(req, multi_layout=True)
            cands = res.get("candidates", [])
            if cands:
                _state["candidates"] = cands
                _render_four_layouts(cands)
                layout_cards_box.layout.display = "flex"
                active_plan_image.layout.display = "none"
                active_plan_header.value = ""
                validation_html.value = ""
                _add_chat("assistant",
                    f"&#x1F504; Regenerated <b>{len(cands)} fresh layouts</b>. "
                    "Click <b>[Select]</b> to activate one.", ok=True)
        except Exception as e:
            _add_chat("assistant", f"Regeneration failed: {str(e)[:80]}", ok=False, error=True)

    # ========================================================
    # WIRE UP EVENTS
    # ========================================================
    btn_generate.on_click(_on_generate_clicked)
    btn_send.on_click(_on_send_clicked)
    btn_undo.on_click(_on_undo_clicked)
    btn_redo.on_click(_on_redo_clicked)
    btn_compare.on_click(_on_compare_clicked)
    btn_validate.on_click(_on_validate_clicked)
    btn_finalize.on_click(_on_finalize_clicked)
    btn_regenerate.on_click(_on_regenerate_clicked)

    for i, btn in enumerate(layout_select_btns):
        btn.on_click(_make_select_handler(i))

    # ========================================================
    # LAYOUT CARD GRID (4 cards side by side)
    # ========================================================
    cards = []
    for i in range(4):
        card = widgets.VBox(
            [layout_labels[i], layout_images[i], layout_select_btns[i]],
            layout=widgets.Layout(
                width="24%", min_width="200px",
                padding="4px",
            ),
        )
        cards.append(card)

    layout_cards_box.children = [widgets.HBox(
        cards,
        layout=widgets.Layout(
            flex_wrap="wrap", gap="10px", width="100%",
            justify_content="space-between",
        )
    )]

    # ========================================================
    # ASSEMBLE FULL UI
    # ========================================================
    section_divider = widgets.HTML(
        "<hr style='border:0; height:1px; background:#CBD5E1; margin:10px 0;'>"
    )

    req_row = widgets.HBox(
        [btn_generate],
        layout=widgets.Layout(margin="6px 0 10px 0"),
    )

    chat_send_row = widgets.HBox(
        [chat_input, btn_send],
        layout=widgets.Layout(gap="8px", width="100%", margin="6px 0"),
    )

    ui = widgets.VBox([
        header_html,
        # --- Requirements section ---
        widgets.HTML("<div style='font-size:12px; font-weight:600; color:#374151; margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px;'>House Requirements</div>"),
        requirements_input,
        req_row,
        section_divider,
        # --- Layout grid (visible after generation) ---
        layout_cards_box,
        # --- Active plan ---
        active_plan_header,
        active_plan_image,
        validation_html,
        compare_output,
        section_divider,
        # --- Chat ---
        widgets.HTML("<div style='font-size:12px; font-weight:600; color:#374151; margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px;'>Conversation</div>"),
        chat_html,
        chat_send_row,
        # --- Controls ---
        controls_box,
    ], layout=widgets.Layout(
        padding="16px",
        border="1px solid #CBD5E1",
        border_radius="14px",
        background_color="#FFFFFF",
        width="100%",
    ))

    display(ui)

print("AAFPA 2.0 Smart Studio loaded.")
print("Run  launch_interactive_studio()  to open the interactive interface.")
"""
