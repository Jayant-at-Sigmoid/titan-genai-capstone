from matplotlib.pyplot import margins
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AnalyticsDashboard:
    @staticmethod
    def render_overview_charts(scans: List[Dict[str, Any]], violations: List[Dict[str, Any]], model_metrics: List[Dict[str, Any]]):
        """Renders the executive compliance command center analytics widgets."""
        if not scans:
            st.info("No compliance scan logs available yet in database.")
            return

        df_scans = pd.DataFrame(scans)
        df_scans["created_at"] = pd.to_datetime(df_scans["created_at"])
        df_scans = df_scans.sort_values(by="created_at")

        # Premium GRC Colors
        colors_map = {
            "LOW": "#10B981",       # Emerald Green
            "MEDIUM": "#F59E0B",    # Amber/Yellow
            "HIGH": "#EF4444",      # Crimson Red
            "CRITICAL": "#991B1B"   # Deep Dark Red
        }

        # ----------------- SECTION 2 & 3: Risk and Category Distribution -----------------
        st.write("### Risk Distribution and Category Breakdown")
        col_risk, col_cat = st.columns(2)
        
        with col_risk:
            with st.container(border=True):
                st.write("#### Risk Distribution")
                # Count risk levels in scans
                risk_counts = df_scans["overall_risk"].value_counts().reset_index()
                risk_counts.columns = ["Risk Rating", "Count"]
                
                fig_pie = px.pie(
                    risk_counts,
                    values="Count",
                    names="Risk Rating",
                    color="Risk Rating",
                    color_discrete_map=colors_map,
                    hole=0.55
                )
                fig_pie.update_traces(
                    textinfo="percent+value",
                    textposition="outside",
                    marker=dict(line=dict(color="#FFFFFF", width=2))
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, system-ui, sans-serif", size=11, color="#1E293B"),
                    margin=dict(t=30, b=30, l=10, r=10),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=11)
                    )
                )
                st.plotly_chart(fig_pie, width='stretch')

        with col_cat:
            with st.container(border=True):
                st.write("#### Violation Category Analysis")
                if violations:
                    df_viols = pd.DataFrame(violations)
                    cat_counts = df_viols["category"].value_counts().reset_index()
                    cat_counts.columns = ["Category", "Count"]
                    
                    fig_bar = px.bar(
                        cat_counts,
                        x="Category",
                        y="Count",
                        color="Category",
                        color_discrete_sequence=["#3B82F6", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"]
                    )
                    fig_bar.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Inter, system-ui, sans-serif", size=11, color="#1E293B"),
                        xaxis=dict(showgrid=False, title="", tickangle=0),
                        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Count"),
                        margin=dict(t=30, b=10, l=10, r=10),
                        showlegend=False
                    )
                    fig_bar.update_traces(
                        marker=dict(line=dict(width=0)),
                        width=0.4
                    )
                    st.plotly_chart(fig_bar, width='stretch')
                else:
                    st.info("No compliance violations logs found.")

        # ----------------- SECTION 4 & 5: Compliance and Risk Score Trend -----------------
        st.write("### Historical Compliance Trends")
        col_trend, col_score = st.columns(2)
        
        with col_trend:
            with st.container(border=True):
                st.write("#### Document Scan Volume Trend")
                # Group scans by date (Daily)
                df_scans["date"] = df_scans["created_at"].dt.date
                scan_volume = df_scans.groupby("date").size().reset_index(name="Scan Count")
                
                fig_volume = px.line(
                    scan_volume,
                    x="date",
                    y="Scan Count",
                    markers=True
                )
                fig_volume.update_traces(
                    line=dict(color="#2563EB", width=3),
                    marker=dict(size=8, color="#2563EB", line=dict(color="#FFFFFF", width=2))
                )
                fig_volume.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, system-ui, sans-serif", size=11, color="#1E293B"),
                    xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Date"),
                    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Scans"),
                    margin=dict(t=30, b=10, l=10, r=10)
                )
                st.plotly_chart(fig_volume, width='stretch')

        with col_score:
            with st.container(border=True):
                st.write("#### Risk Score Trend Analysis")
                # Filter selection
                time_filter = st.selectbox(
                    "Trend Window",
                    ["Last 7 days", "Last 30 days", "Last 90 days"],
                    key="trend_window_sel"
                )
                
                days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
                limit_date = datetime.now() - timedelta(days=days_map[time_filter])
                
                df_filtered = df_scans[df_scans["created_at"] >= limit_date]
                
                if df_filtered.empty:
                    st.info("No scan records matched the selected timeline filter.")
                else:
                    df_filtered["date"] = df_filtered["created_at"].dt.date
                    avg_scores = df_filtered.groupby("date")["compliance_score"].mean().reset_index()
                    
                    fig_score_trend = px.line(
                        avg_scores,
                        x="date",
                        y="compliance_score",
                        markers=True,
                        labels={"compliance_score": "Average Compliance Score"}
                    )
                    fig_score_trend.update_traces(
                        line=dict(color="#2563EB", width=3),
                        marker=dict(size=8, color="#10B981", line=dict(color="#FFFFFF", width=2))
                    )
                    fig_score_trend.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Inter, system-ui, sans-serif", size=11, color="#1E293B"),
                        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Date"),
                        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", range=[0, 105], title="Compliance %"),
                        margin=dict(t=30, b=10, l=10, r=10)
                    )
                    st.plotly_chart(fig_score_trend, width='stretch')

        # ----------------- SECTION 6 & 7: Top Policies & Review Queue -----------------
        st.write("### Policies and Queue Analytics")
        col_policies, col_queue = st.columns(2)
        
        with col_policies:
            with st.container(border=True):
                st.write("#### Top Policy Violations")
                if violations:
                    # Get standard list of categories
                    df_viols = pd.DataFrame(violations)
                    viol_categories = df_viols["category"].value_counts().reset_index()
                    viol_categories.columns = ["Category", "Occurrences"]
                    
                    fig_horiz = px.bar(
                        viol_categories,
                        x="Occurrences",
                        y="Category",
                        orientation="h",
                        color="Category",
                        color_discrete_sequence=["#3B82F6", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"]
                    )
                    fig_horiz.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Inter, system-ui, sans-serif", size=11, color="#1E293B"),
                        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Occurrences"),
                        yaxis=dict(showgrid=False, title=""),
                        margin=dict(t=30, b=10, l=10, r=10),
                        showlegend=False
                    )
                    fig_horiz.update_traces(
                        marker=dict(line=dict(width=0)),
                        width=0.4
                    )
                    st.plotly_chart(fig_horiz, width='stretch')
                else:
                    st.info("No policy breaches logged.")

        with col_queue:
            with st.container(border=True):
                st.write("#### Review Queue Status")
                if violations:
                    df_viols = pd.DataFrame(violations)
                    # Get reviews status counts
                    status_counts = df_viols["review_status"].value_counts().reset_index()
                    status_counts.columns = ["Status", "Count"]
                    
                    queue_colors = {
                        "Approved": "#10B981",
                        "Rejected": "#EF4444",
                        "Pending": "#64748B",
                        "Needs Review": "#F59E0B"
                    }
                    
                    fig_donut = px.pie(
                        status_counts,
                        values="Count",
                        names="Status",
                        color="Status",
                        color_discrete_map=queue_colors,
                        hole=0.55
                    )
                    fig_donut.update_traces(
                        textinfo="percent+value",
                        textposition="outside",
                        marker=dict(line=dict(color="#FFFFFF", width=2))
                    )
                    fig_donut.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Inter, system-ui, sans-serif", size=11, color="#1E293B"),
                        margin=dict(t=30, b=30, l=10, r=10),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=11)
                        )
                    )
                    st.plotly_chart(fig_donut, width='stretch')
                else:
                    st.info("No compliance cases pending review.")

        # ----------------- SECTION 8: Model Performance Dashboard -----------------
        st.write("### Model Performance and Latency Analytics")
        if model_metrics:
            df_metrics = pd.DataFrame(model_metrics)
            
            # KPI stats
            lite_calls = len(df_metrics[df_metrics["model_name"].str.contains("Lite|Sonnet", case=False, na=False)])
            micro_calls = len(df_metrics[df_metrics["model_name"].str.contains("Micro|Haiku", case=False, na=False)])
            avg_latency = df_metrics["latency"].mean()
            total_cost = df_metrics["estimated_cost"].sum()
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Nova Lite Calls</div><div class="metric-val">{lite_calls}</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Nova Micro Calls</div><div class="metric-val">{micro_calls}</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Avg Latency</div><div class="metric-val">{avg_latency:.2f}s</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Estimated Cost</div><div class="metric-val">${total_cost:.4f}</div></div>', unsafe_allow_html=True)
                
            # Line graph for average latency over time
            df_metrics["timestamp"] = pd.to_datetime(df_metrics["timestamp"])
            df_metrics = df_metrics.sort_values(by="timestamp")
            
            with st.container(border=True):
                st.write("#### API Execution Latency Timeline")
                fig_latency = px.scatter(
                    df_metrics,
                    x="timestamp",
                    y="latency",
                    color="model_name",
                    trendline="lowess",
                    color_discrete_sequence=["#3B82F6", "#8B5CF6"],
                    labels={"latency": "Latency (sec)", "timestamp": "API Call Timestamp"}
                )
                fig_latency.update_traces(marker=dict(size=6, opacity=0.8))
                fig_latency.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, system-ui, sans-serif", size=11, color="#1E293B"),
                    xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Timestamp"),
                    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Latency (sec)"),
                    margin=dict(t=30, b=60, l=10, r=10),
                    legend=dict(
                        title=dict(text=""),
                        orientation="h",
                        yanchor="top",
                        y=-0.3,
                        xanchor="center",
                        x=0.5,
                        font=dict()
                    )
                )
                st.plotly_chart(fig_latency, width='stretch')
        else:
            st.info("No model API performance metrics indexed yet.")

        # ----------------- SECTION 9: Compliance Heatmap -----------------
        st.write("### Document Compliance Heatmap")
        if violations:
            # Pivot table showing scan document name vs violation category counts
            df_viols = pd.DataFrame(violations)
            
            # Join with scans to get filenames
            df_scans_flat = pd.DataFrame(scans)[["id", "filename"]].rename(columns={"id": "scan_id"})
            df_joined = df_viols.merge(df_scans_flat, on="scan_id", how="inner")
            
            heatmap_data = df_joined.groupby(["filename", "category"]).size().unstack(fill_value=0).reset_index()
            
            # Transform to long format or draw directly using go.Heatmap
            filenames = heatmap_data["filename"].tolist()
            categories = [c for c in heatmap_data.columns if c != "filename"]
            
            z_values = heatmap_data[categories].values.tolist()
            
            if filenames and categories:
                with st.container(border=True):
                    st.write("#### Document vs Violation Density Map")
                    fig_heatmap = go.Figure(data=go.Heatmap(
                        z=z_values,
                        x=categories,
                        y=filenames,
                        colorscale="Blues",
                        hoverongaps=False
                    ))
                    fig_heatmap.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Inter, system-ui, sans-serif", size=11, color="#1E293B"),
                        margin=dict(t=30, b=10, l=10, r=10),
                        xaxis=dict(color="#64748B"),
                        yaxis=dict(color="#64748B")
                    )
                    st.plotly_chart(fig_heatmap, width='stretch')
            else:
                st.info("Insufficient data for density heatmap compilation.")
        else:
            st.info("No violations logged for heatmap compilation.")

# Global dashboard reference
analytics_dashboard = AnalyticsDashboard()
