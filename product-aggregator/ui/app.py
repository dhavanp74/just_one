import os
import sys
from typing import List

import pandas as pd
import streamlit as st


# Ensure the package directory (product-aggregator) is on sys.path so imports
# like `from core.aggregator import fetch_combined` work when Streamlit runs
# this file from the repository root or other working directories.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def try_import_aggregator():
    try:
        from core.aggregator import fetch_combined

        return fetch_combined
    except Exception as e:
        # Return a stub that raises a clear error when called
        def _stub(*args, **kwargs):
            raise RuntimeError(
                "Aggregator not available. Check your environment and scraper dependencies. Original error: %s" % e
            )

        return _stub


fetch_combined = try_import_aggregator()


st.set_page_config(page_title="Product Aggregator", layout="wide")


def _ensure_session_state():
    if "last_df" not in st.session_state:
        st.session_state.last_df = pd.DataFrame()
    if "compare_selected" not in st.session_state:
        st.session_state.compare_selected = []


def _get_row_id(row: pd.Series, idx: int) -> str:
    if "id" in row and pd.notna(row.get("id")):
        return str(row.get("id"))
    return f"idx_{idx}"


def main():
    _ensure_session_state()

    MAX_COMPARE = 4

    st.title("Product Aggregator")

    with st.sidebar.form(key="search_form"):
        query = st.text_input("Search product", value="", placeholder="e.g. iPhone 14")
        sites = st.multiselect(
            "Sites", ["Amazon", "Flipkart", "JioMart", "Snapdeal"], default=["Amazon", "Flipkart", "JioMart", "Snapdeal"]
        )
        max_per_site = st.slider("Max results per site", 1, 50, 10)
        headless = st.checkbox("Headless (Selenium)", value=True)
        save_snapshot = st.checkbox("Save snapshot to DB", value=False)
        submit = st.form_submit_button("Search")

    # Demo data helper so users can exercise UI without scrapers
    if st.sidebar.button("Load demo data"):
        demo = pd.DataFrame([
            {
                "title": "Demo Phone X",
                "description": "Demo description for Phone X",
                "price": "₹49,999",
                "currency": "INR",
                "link": "https://example.com/product/demo-phone-x",
                "image": "https://via.placeholder.com/300x200.png?text=Demo+Phone+X",
                "source": "DemoStore",
            },
            {
                "title": "Demo Laptop Y",
                "description": "Demo description for Laptop Y",
                "price": "₹74,990",
                "currency": "INR",
                "link": "https://example.com/product/demo-laptop-y",
                "image": "https://via.placeholder.com/300x200.png?text=Demo+Laptop+Y",
                "source": "DemoStore",
            },
        ])
        st.session_state.last_df = demo
        st.success("Demo data loaded — try the Preview & Compare section")

    # Snapshot management (M3)
    with st.sidebar.expander("Saved snapshots", expanded=False):
        try:
            from database.db_helper import load_snapshots, delete_snapshot

            q_filter = query.strip() if isinstance(query, str) and query.strip() else None
            _snapshots = load_snapshots(query=q_filter)
        except Exception:
            _snapshots = []

        snap_options = ["-- none --"] + [f"{s['id']} | {s['query']} | {s['created_at']}" for s in _snapshots]
        sel = st.selectbox("Select a snapshot", snap_options, key="snap_select")

        if sel and sel != "-- none --":
            try:
                sid = int(sel.split("|")[0].strip())
            except Exception:
                sid = None

            snap = None
            if sid is not None:
                for s in _snapshots:
                    if s.get("id") == sid:
                        snap = s
                        break

            if snap is not None:
                st.write(f"**Snapshot {snap['id']}** — Query: {snap['query']}")
                st.write(f"Saved at: {snap['created_at']}")
                try:
                    preview_df = snap.get("df")
                    if preview_df is None or getattr(preview_df, "empty", True):
                        st.info("Snapshot has no data.")
                    else:
                        st.dataframe(preview_df.head(20))
                except Exception:
                    st.info("Unable to preview snapshot data.")

                cols_snap = st.columns([1, 1, 1])
                with cols_snap[0]:
                    if st.button("Load into results", key=f"load_snap_{sid}"):
                        try:
                            st.session_state.last_df = snap["df"].reset_index(drop=True)
                            st.success("Snapshot loaded into results")
                        except Exception:
                            st.error("Failed to load snapshot into results")
                with cols_snap[1]:
                    try:
                        df_export = snap.get("df")
                        if df_export is not None and not getattr(df_export, "empty", True):
                            csv_bytes = df_export.to_csv(index=False).encode("utf-8")
                            st.download_button("Export CSV", csv_bytes, file_name=f"snapshot_{sid}.csv", key=f"dl_csv_{sid}", mime="text/csv")
                            json_bytes = df_export.to_json(orient="records", force_ascii=False).encode("utf-8")
                            st.download_button("Export JSON", json_bytes, file_name=f"snapshot_{sid}.json", key=f"dl_json_{sid}", mime="application/json")
                        else:
                            st.write("No data to export")
                    except Exception:
                        st.write("Export unavailable")
                with cols_snap[2]:
                    if st.button("Delete snapshot", key=f"del_snap_{sid}"):
                        try:
                            ok = delete_snapshot(sid)
                            if ok:
                                st.success("Snapshot deleted")
                                st.experimental_rerun()
                            else:
                                st.error("Snapshot not deleted")
                        except Exception as e:
                            st.error(f"Failed to delete snapshot: {e}")

    # Handle search submission
    if st.sidebar.button("Clear results"):
        st.session_state.last_df = pd.DataFrame()

    if "last_df" not in st.session_state:
        st.session_state.last_df = pd.DataFrame()

    # If user submitted the search form (use the submit from the form), the variable 'submit' exists
    try:
        submitted = submit
    except NameError:
        submitted = False

    if submitted and isinstance(query, str) and query.strip():
        q = query.strip()
        with st.spinner(f"Searching for '{q}' across sites..."):
            try:
                df = fetch_combined(q, max_per_site, sources=sites, headless=headless, save_snapshot_to_db=save_snapshot)
            except Exception as e:
                st.error(f"Search failed: {e}")
                df = pd.DataFrame()

        if df is None or (hasattr(df, "__len__") and len(df) == 0):
            st.info("No results found.")
            st.session_state.last_df = pd.DataFrame()
        else:
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            st.session_state.last_df = df.reset_index(drop=True)
            st.success(f"Found {len(df)} results")

    df = st.session_state.get("last_df")
    if df is None or df.empty:
        st.info("Enter a query in the sidebar and press Search to begin, or click 'Load demo data'.")
        return

    # Summary table
    st.subheader("Results")
    display_cols = [c for c in ("source", "title", "price", "link") if c in df.columns]
    st.dataframe(df[display_cols].reset_index(drop=True))

    # Card grid with compare checkboxes and detail expander
    st.markdown("---")
    st.subheader("Preview & Compare")

    cols = st.columns(3)
    for idx, row in df.iterrows():
        col = cols[idx % 3]
        with col:
            rid = _get_row_id(row, idx)
            current_selected: List[str] = list(st.session_state.compare_selected)
            checked = rid in current_selected
            cb = st.checkbox("Compare", value=checked, key=f"cb_{rid}")
            if cb and rid not in current_selected:
                if len(current_selected) >= MAX_COMPARE:
                    st.warning(f"You can compare at most {MAX_COMPARE} items. Clear selection to add more.")
                    st.session_state[f"cb_{rid}"] = False
                else:
                    current_selected.append(rid)
            if (not cb) and rid in current_selected:
                current_selected.remove(rid)
            st.session_state.compare_selected = current_selected

            img = row.get("image")
            if img:
                try:
                    st.image(img, use_column_width=True)
                except Exception:
                    st.write("[image]")

            st.markdown(f"**{row.get('title','')}**")
            st.markdown(f"**{row.get('source','')}** — {row.get('price','')}")

            with st.expander("Details"):
                desc = row.get("description") or row.get("title") or ""
                st.write(desc)
                if "rating" in row and pd.notna(row.get("rating")):
                    st.write(f"Rating: {row.get('rating')}")
                if "link" in row and row.get("link"):
                    st.markdown(f"[Open product]({row.get('link')})")

    # Compare selected panel
    st.markdown("---")
    st.subheader("Compare Selected")
    selected = st.session_state.compare_selected
    st.write(f"Selected for compare: {len(selected)} / {MAX_COMPARE}")
    if st.button("Clear selection") and selected:
        for s in list(selected):
            key = f"cb_{s}"
            if key in st.session_state:
                st.session_state[key] = False
        st.session_state.compare_selected = []
        st.experimental_rerun()

    selected_rows = []
    for sel in selected:
        if isinstance(sel, str) and sel.startswith("idx_"):
            try:
                ridx = int(sel.split("_")[1])
                if 0 <= ridx < len(df):
                    selected_rows.append((sel, df.iloc[ridx]))
            except Exception:
                continue
        else:
            matches = df[df.get("id") == sel]
            if not matches.empty:
                selected_rows.append((sel, matches.iloc[0]))

    if len(selected_rows) < 2:
        st.info("Select at least two items to compare using the 'Compare' checkbox on cards.")
    else:
        cols_cmp = st.columns(len(selected_rows))
        for i, (_rid, r) in enumerate(selected_rows):
            with cols_cmp[i]:
                if r.get("image"):
                    try:
                        st.image(r.get("image"), width=200)
                    except Exception:
                        st.write("[image]")
                st.markdown(f"### {r.get('title','')}")
                st.markdown(f"**Source:** {r.get('source','')}")
                st.markdown(f"**Price:** {r.get('price','')}")
                st.write(r.get('description',''))
                if r.get('link'):
                    st.markdown(f"[Open product]({r.get('link')})")


if __name__ == "__main__":
    main()
import os
import sys
import streamlit as st
import pandas as pd

# Ensure the package directory (product-aggregator) is on sys.path so imports like
# `from core.aggregator import fetch_combined` work when Streamlit runs this file
# from the repository root or other working directories.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.aggregator import fetch_combined


st.set_page_config(page_title="Product Aggregator", layout="wide")


def main():
    st.title("Product Aggregator")

    with st.sidebar.form(key="search_form"):
        query = st.text_input("Search product", value="", placeholder="e.g. iPhone 14")
        sites = st.multiselect("Sites", ["Amazon", "Flipkart", "JioMart", "Snapdeal"], default=["Amazon", "Flipkart", "JioMart", "Snapdeal"])
        max_per_site = st.slider("Max results per site", 1, 50, 10)
        headless = st.checkbox("Headless (Selenium)", value=True)
        save_snapshot = st.checkbox("Save snapshot to DB", value=False)
        submit = st.form_submit_button("Search")

    # Preserve last results in session state so users can navigate UI without re-searching
    if "last_df" not in st.session_state:
        st.session_state.last_df = None

    if submit and query.strip():
        q = query.strip()
        with st.spinner(f"Searching for '{q}' across sites..."):
            try:
                # Pass sources and headless to aggregator so scrapers can be limited and run headless when applicable
                df = fetch_combined(q, max_per_site, sources=sites, headless=headless, save_snapshot_to_db=save_snapshot)
            except Exception as e:
                st.error(f"Search failed: {e}")
                df = pd.DataFrame()

        if df is None or (hasattr(df, "__len__") and len(df) == 0):
            st.info("No results found.")
            st.session_state.last_df = pd.DataFrame()
        else:
            # ensure DataFrame
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            st.session_state.last_df = df
            st.success(f"Found {len(df)} results")

    # Show last results if available
    df = st.session_state.get("last_df")
    if df is None:
        st.info("Enter a query in the sidebar and press Search to begin.")
        return

    if df.empty:
        st.info("No results to show.")
        return

    import os
    import sys
    import streamlit as st
    import pandas as pd

    # Ensure the package directory (product-aggregator) is on sys.path so imports like
    # `from core.aggregator import fetch_combined` work when Streamlit runs this file
    # from the repository root or other working directories.
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    from core.aggregator import fetch_combined


    st.set_page_config(page_title="Product Aggregator", layout="wide")


    def _ensure_session_state():
        if "last_df" not in st.session_state:
            st.session_state.last_df = pd.DataFrame()
        if "compare_selected" not in st.session_state:
            st.session_state.compare_selected = []


    # UX config: max items that can be compared at once
    MAX_COMPARE = 4


    def _get_row_id(row, idx):
        # Use explicit id column when present, otherwise fallback to index
        if "id" in row and pd.notna(row.get("id")):
            return row.get("id")
        return f"idx_{idx}"


    def main():
        _ensure_session_state()

        st.title("Product Aggregator")

        with st.sidebar.form(key="search_form"):
            query = st.text_input("Search product", value="", placeholder="e.g. iPhone 14")
            sites = st.multiselect("Sites", ["Amazon", "Flipkart", "JioMart", "Snapdeal"], default=["Amazon", "Flipkart", "JioMart", "Snapdeal"])
            max_per_site = st.slider("Max results per site", 1, 50, 10)
            headless = st.checkbox("Headless (Selenium)", value=True)
            save_snapshot = st.checkbox("Save snapshot to DB", value=False)
            submit = st.form_submit_button("Search")

        # Demo data helper: load a small sample dataset into the UI so users
        # can preview the full app without network or scraper dependencies.
        if st.sidebar.button("Load demo data"):
            demo = pd.DataFrame([
                {
                    "title": "Demo Phone X",
                    "description": "Demo description for Phone X",
                    "price": "₹49,999",
                    "currency": "INR",
                    "link": "https://example.com/product/demo-phone-x",
                    "image": "https://via.placeholder.com/300x200.png?text=Demo+Phone+X",
                    "source": "DemoStore",
                },
                {
                    "title": "Demo Laptop Y",
                    "description": "Demo description for Laptop Y",
                    "price": "₹74,990",
                    "currency": "INR",
                    "link": "https://example.com/product/demo-laptop-y",
                    "image": "https://via.placeholder.com/300x200.png?text=Demo+Laptop+Y",
                    "source": "DemoStore",
                },
            ])
            st.session_state.last_df = demo
            st.success("Demo data loaded — try the Preview & Compare section")

        # Snapshot management (M3): list, preview, load, export and delete saved snapshots
        with st.sidebar.expander("Saved snapshots", expanded=False):
            try:
                from database.db_helper import load_snapshots, delete_snapshot

                # If the user has entered a query in the search form, show only
                # snapshots that match that query by default. Otherwise list all.
                q_filter = query.strip() if isinstance(query, str) and query.strip() else None
                _snapshots = load_snapshots(query=q_filter)
            except Exception:
                _snapshots = []

            snap_options = ["-- none --"] + [f"{s['id']} | {s['query']} | {s['created_at']}" for s in _snapshots]
            sel = st.selectbox("Select a snapshot", snap_options, key="snap_select")

            if sel and sel != "-- none --":
                try:
                    sid = int(sel.split("|")[0].strip())
                except Exception:
                    sid = None

                snap = None
                if sid is not None:
                    for s in _snapshots:
                        if s.get("id") == sid:
                            snap = s
                            break

                if snap is not None:
                    st.write(f"**Snapshot {snap['id']}** — Query: {snap['query']}")
                    st.write(f"Saved at: {snap['created_at']}")

                    # Preview small table
                    try:
                        preview_df = snap.get("df")
                        if preview_df is None or getattr(preview_df, "empty", True):
                            st.info("Snapshot has no data.")
                        else:
                            st.dataframe(preview_df.head(20))
                    except Exception:
                        st.info("Unable to preview snapshot data.")

                    # Actions: load into results, export, delete
                    cols_snap = st.columns([1, 1, 1])
                    with cols_snap[0]:
                        if st.button("Load into results", key=f"load_snap_{sid}"):
                            try:
                                st.session_state.last_df = snap['df'].reset_index(drop=True)
                                st.success("Snapshot loaded into results")
                            except Exception:
                                st.error("Failed to load snapshot into results")
                    with cols_snap[1]:
                        try:
                            df_export = snap.get('df')
                            if df_export is not None and not getattr(df_export, "empty", True):
                                csv_bytes = df_export.to_csv(index=False).encode('utf-8')
                                st.download_button("Export CSV", csv_bytes, file_name=f"snapshot_{sid}.csv", key=f"dl_csv_{sid}", mime='text/csv')
                                json_bytes = df_export.to_json(orient='records', force_ascii=False).encode('utf-8')
                                st.download_button("Export JSON", json_bytes, file_name=f"snapshot_{sid}.json", key=f"dl_json_{sid}", mime='application/json')
                            else:
                                st.write("No data to export")
                        except Exception:
                            st.write("Export unavailable")
                    with cols_snap[2]:
                        if st.button("Delete snapshot", key=f"del_snap_{sid}"):
                            try:
                                ok = delete_snapshot(sid)
                                if ok:
                                    st.success("Snapshot deleted")
                                    st.experimental_rerun()
                                else:
                                    st.error("Snapshot not deleted")
                            except Exception as e:
                                st.error(f"Failed to delete snapshot: {e}")

        if submit and query.strip():
            q = query.strip()
            with st.spinner(f"Searching for '{q}' across sites..."):
                try:
                    df = fetch_combined(q, max_per_site, sources=sites, headless=headless, save_snapshot_to_db=save_snapshot)
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    df = pd.DataFrame()

            if df is None or (hasattr(df, "__len__") and len(df) == 0):
                st.info("No results found.")
                st.session_state.last_df = pd.DataFrame()
            else:
                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame(df)
                st.session_state.last_df = df.reset_index(drop=True)
                st.success(f"Found {len(df)} results")

        df = st.session_state.get("last_df")
        if df is None or df.empty:
            st.info("Enter a query in the sidebar and press Search to begin.")
            return

        # Summary table
        st.subheader("Results")
        display_cols = [c for c in ("source", "title", "price", "link") if c in df.columns]
        st.dataframe(df[display_cols].reset_index(drop=True))

        # Card grid with compare checkboxes and detail expander
        st.markdown("---")
        st.subheader("Preview & Compare")

        cols = st.columns(3)
        for idx, row in df.iterrows():
            col = cols[idx % 3]
            with col:
                rid = _get_row_id(row, idx)
                # checkbox for compare
                # Manage compare selection with a limit
                current_selected = list(st.session_state.compare_selected)
                checked = rid in current_selected
                cb = st.checkbox("Compare", value=checked, key=f"cb_{rid}")
                if cb and rid not in current_selected:
                    if len(current_selected) >= MAX_COMPARE:
                        st.warning(f"You can compare at most {MAX_COMPARE} items. Clear selection to add more.")
                        # uncheck the checkbox programmatically
                        st.session_state[f"cb_{rid}"] = False
                    else:
                        current_selected.append(rid)
                if (not cb) and rid in current_selected:
                    current_selected.remove(rid)
                st.session_state.compare_selected = current_selected

                # image
                img = row.get("image")
                if img:
                    try:
                        st.image(img, use_column_width=True)
                    except Exception:
                        st.write("[image]")

                st.markdown(f"**{row.get('title','')}**")
                st.markdown(f"**{row.get('source','')}** — {row.get('price','')}")

                # detail expander
                with st.expander("Details"):
                    desc = row.get("description") or row.get("title") or ""
                    st.write(desc)
                    if "rating" in row and pd.notna(row.get("rating")):
                        st.write(f"Rating: {row.get('rating')}")
                    if "link" in row and row.get("link"):
                        st.markdown(f"[Open product]({row.get('link')})")

        # Compare selected panel
        st.markdown("---")
        st.subheader("Compare Selected")
        selected = st.session_state.compare_selected
        st.write(f"Selected for compare: {len(selected)} / {MAX_COMPARE}")
        if st.button("Clear selection") and selected:
            # clear compare flags and list
            for s in list(selected):
                key = f"cb_{s}"
                if key in st.session_state:
                    st.session_state[key] = False
            st.session_state.compare_selected = []
            # Refresh UI to reflect cleared checkboxes
            st.experimental_rerun()
        # Map selected ids back to rows
        selected_rows = []
        for sel in selected:
            if isinstance(sel, str) and sel.startswith("idx_"):
                try:
                    ridx = int(sel.split("_")[1])
                    if 0 <= ridx < len(df):
                        selected_rows.append((sel, df.iloc[ridx]))
                except Exception:
                    continue
            else:
                # try to find by id column
                matches = df[df.get("id") == sel]
                if not matches.empty:
                    selected_rows.append((sel, matches.iloc[0]))

        if len(selected_rows) < 2:
            st.info("Select at least two items to compare using the 'Compare' checkbox on cards.")
        else:
            cols_cmp = st.columns(len(selected_rows))
            for i, (_rid, r) in enumerate(selected_rows):
                with cols_cmp[i]:
                    if r.get("image"):
                        try:
                            st.image(r.get("image"), width=200)
                        except Exception:
                            st.write("[image]")
                    st.markdown(f"### {r.get('title','')}")
                    st.markdown(f"**Source:** {r.get('source','')}")
                    st.markdown(f"**Price:** {r.get('price','')}")
                    st.write(r.get('description',''))
                    if r.get('link'):
                        st.markdown(f"[Open product]({r.get('link')})")


    if __name__ == "__main__":
        main()
cd /d D:\Projects\just_one

# is this a git repo (prints repo root) or errors if not
git rev-parse --show-toplevel

# quick status (uncommitted changes)
git status --porcelain

# does .git exist?
Test-Path -Path .git

# remote URLs
git remote -v

# current local branch
git branch --show-current

# remote branches that exist
git fetch origin
git branch -r

# last local commit
git log -1 --oneline

# check if your branch exists on origin (replace name if different)
git ls-remote --heads origin kiran-final-streamlit