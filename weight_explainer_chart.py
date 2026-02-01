"""
Weight Explainer Chart Generator

Creates an animated horizontal bar chart from a pandas Series,
showing multiplicative (log scale) or additive (linear scale) factors
that explain weight changes.
"""

import math
import os
import pandas as pd
from pathlib import Path


# Path to the HTML template
TEMPLATE_PATH = Path(__file__).parent / "weight_explainer_template.html"


def _load_template() -> str:
    """Load the HTML template file."""
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def generate_weight_explainer_chart(
    factors: pd.Series,
    w_idx: float,
    w_mcap: float,
    title: str = "",
    animation_duration: float = 3.0,
    log_scale: bool = True,
) -> str:
    """
    Generate an animated HTML bar chart showing weight factors.

    Parameters
    ----------
    factors : pd.Series
        Series with factor names as index and factor values as values.
        - If log_scale=True: values are multipliers (e.g., 1.05 means x1.05)
        - If log_scale=False: values are additive changes (e.g., 0.005 means +0.5%)
    w_idx : float
        The index weight (starting point), shown at the top.
    w_mcap : float
        The market cap weight (ending point), shown at the bottom.
    title : str
        Chart title (optional).
    animation_duration : float
        Total animation duration in seconds (default 3.0).
    log_scale : bool
        If True, factors are multiplicative (default). If False, factors are additive.

    Returns
    -------
    str
        Complete HTML document as a string.
    """

    n_factors = len(factors)
    if n_factors == 0:
        raise ValueError("factors Series must not be empty")

    # Calculate animation delay per bar (animate bottom to top)
    delay_per_bar = animation_duration / n_factors

    # Adjust row height based on number of factors (3-12 range)
    if n_factors <= 4:
        row_height = 44
        bar_height = 28
        margin_bottom = 8
    elif n_factors <= 6:
        row_height = 38
        bar_height = 26
        margin_bottom = 6
    elif n_factors <= 9:
        row_height = 34
        bar_height = 24
        margin_bottom = 5
    else:
        row_height = 30
        bar_height = 22
        margin_bottom = 4

    # Build bar data based on scale type
    current_pos = w_idx
    bar_data = []

    for label, factor in factors.items():
        if log_scale:
            next_pos = current_pos * factor
        else:
            next_pos = current_pos + factor

        bar_data.append({
            'label': label,
            'factor': factor,
            'start': current_pos,
            'end': next_pos,
        })
        current_pos = next_pos

    # Find the range for scaling
    all_positions = [w_idx, w_mcap] + [b['start'] for b in bar_data] + [b['end'] for b in bar_data]
    min_val = min(all_positions)
    max_val = max(all_positions)

    # Add padding to range
    range_span = max_val - min_val
    min_val = min_val - range_span * 0.1
    max_val = max_val + range_span * 0.1

    # Define position conversion function
    if log_scale and min_val > 0:
        log_min = math.log(min_val)
        log_max = math.log(max_val)

        def to_pct(val):
            return ((math.log(val) - log_min) / (log_max - log_min)) * 100
    else:
        def to_pct(val):
            return ((val - min_val) / (max_val - min_val)) * 100

    # Generate bar HTML
    bars_html_parts = []
    for i, bar in enumerate(bar_data):
        delay = (n_factors - 1 - i) * delay_per_bar

        if log_scale:
            is_positive = bar['factor'] >= 1
        else:
            is_positive = bar['factor'] >= 0

        bar_color = '#2563eb' if is_positive else '#6b7280'

        start_pct = to_pct(bar['start'])
        end_pct = to_pct(bar['end'])

        left_pct = min(start_pct, end_pct)
        width_pct = abs(end_pct - start_pct)

        if width_pct < 0.4:
            width_pct = 0.4

        # Format factor text
        if log_scale:
            if bar['factor'] == 1:
                factor_text = "x1"
            else:
                factor_text = f"x{bar['factor']:.2f}".rstrip('0').rstrip('.')
        else:
            if bar['factor'] == 0:
                factor_text = "+0%"
            elif bar['factor'] > 0:
                factor_text = f"+{bar['factor']:.2%}"
            else:
                factor_text = f"{bar['factor']:.2%}"

        text_left = max(start_pct, end_pct) + 1

        bars_html_parts.append(f'''
        <div class="bar-row" style="animation-delay: {delay:.3f}s;">
            <div class="bar-label">{bar['label']}</div>
            <div class="bar-container">
                <div class="bar" style="left: {left_pct}%; width: {width_pct}%; background-color: {bar_color};"></div>
                <div class="bar-value" style="left: {text_left}%; color: {bar_color};">{factor_text}</div>
            </div>
        </div>''')

    # Calculate reference line positions
    idx_line_pct = to_pct(w_idx)
    mcap_line_pct = to_pct(w_mcap)

    # Generate axis ticks
    if log_scale and min_val > 0:
        tick_interval = (max_val - min_val) / 5
        tick_interval = round(tick_interval * 100) / 100
        if tick_interval < 0.005:
            tick_interval = 0.005
        first_tick = math.ceil(min_val / tick_interval) * tick_interval
        tick_values = []
        tick_val = first_tick
        while tick_val <= max_val:
            tick_values.append(tick_val)
            tick_val += tick_interval
    else:
        range_val = max_val - min_val
        tick_interval = 0.01
        if range_val < 0.03:
            tick_interval = 0.005
        elif range_val > 0.1:
            tick_interval = 0.02

        first_tick = math.ceil(min_val / tick_interval) * tick_interval
        tick_values = []
        tick_val = first_tick
        while tick_val <= max_val:
            tick_values.append(tick_val)
            tick_val += tick_interval

    ticks_html = ''.join([
        f'<div class="tick" style="left: {to_pct(v)}%;">{v:.0%}</div>'
        for v in tick_values
    ])

    # Prepare template data
    title_html = f'<div class="chart-title">{title}</div>' if title else ''

    template_data = {
        'page_title': title or "Weight Explainer",
        'title_html': title_html,
        'row_height': row_height,
        'bar_height': bar_height,
        'margin_bottom': margin_bottom,
        'idx_line_pct': idx_line_pct,
        'mcap_line_pct': mcap_line_pct,
        'w_idx_formatted': f"{w_idx:.3%}",
        'w_mcap_formatted': f"{w_mcap:.3%}",
        'bars_html': ''.join(bars_html_parts),
        'ticks_html': ticks_html,
    }

    # Load template and substitute placeholders
    template = _load_template()
    for key, value in template_data.items():
        template = template.replace('{{' + key + '}}', str(value))

    return template


def save_chart(
    factors: pd.Series,
    w_idx: float,
    w_mcap: float,
    filepath: str = "weight_explainer.html",
    **kwargs
) -> str:
    """
    Generate and save the chart to an HTML file.

    Parameters
    ----------
    factors : pd.Series
        Series with factor names as index and factor values as values.
    w_idx : float
        The index weight (starting point).
    w_mcap : float
        The market cap weight (ending point).
    filepath : str
        Output file path.
    **kwargs
        Additional arguments passed to generate_weight_explainer_chart.
        Including: title, animation_duration, log_scale

    Returns
    -------
    str
        The filepath where the chart was saved.
    """
    html = generate_weight_explainer_chart(factors, w_idx, w_mcap, **kwargs)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filepath


# Example usage
if __name__ == "__main__":
    # Example with 8 factors (multiplicative/log scale)
    factors_log = pd.Series({
        'Min Weight': 1.05,
        'Capacity Ratio': 1.23,
        'Industry / Country': 0.77,
        'High Impact Sector (HIS)': 1.01,
        'TPI MQ Score': 0.79,
        'FTSE Green Revenues': 0.58,
        'Emissions Intensity Scope 3': 1.32,
        'Exclusions': 1.05,
    })

    # Generate log scale chart (multiplicative)
    save_chart(
        factors=factors_log,
        w_idx=0.03446,
        w_mcap=0.05029,
        filepath="weight_explainer_log.html",
        title="Weight Explainer (Log Scale)",
        animation_duration=3.0,
        log_scale=True,
    )
    print("Log scale chart saved to weight_explainer_log.html")

    # Example with additive factors (linear scale)
    factors_linear = pd.Series({
        'Min Weight': 0.002,
        'Capacity Ratio': 0.008,
        'Industry / Country': -0.012,
        'High Impact Sector (HIS)': 0.001,
        'TPI MQ Score': -0.007,
        'FTSE Green Revenues': -0.015,
        'Emissions Intensity Scope 3': 0.010,
        'Exclusions': 0.003,
    })

    save_chart(
        factors=factors_linear,
        w_idx=0.03446,
        w_mcap=0.02446,
        filepath="weight_explainer_linear.html",
        title="Weight Explainer (Linear Scale)",
        animation_duration=3.0,
        log_scale=False,
    )
    print("Linear scale chart saved to weight_explainer_linear.html")
