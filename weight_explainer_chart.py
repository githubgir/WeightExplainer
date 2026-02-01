"""
Weight Explainer Chart Generator

Creates an animated horizontal bar chart from a pandas Series,
showing multiplicative factors that explain weight changes.
"""

import pandas as pd
from typing import Optional


def generate_weight_explainer_chart(
    factors: pd.Series,
    w_idx: float,
    w_mcap: float,
    title: str = "",
    animation_duration: float = 3.0,
) -> str:
    """
    Generate an animated HTML bar chart showing weight factors.

    Parameters
    ----------
    factors : pd.Series
        Series with factor names as index and multiplier values as values.
        Values > 1 indicate positive contribution, < 1 indicate negative.
    w_idx : float
        The index weight (starting point), shown at the top.
    w_mcap : float
        The market cap weight (ending point), shown at the bottom.
    title : str
        Chart title (optional).
    animation_duration : float
        Total animation duration in seconds (default 3.0).

    Returns
    -------
    str
        Complete HTML document as a string.
    """

    # Calculate animation delay per bar (animate bottom to top)
    n_factors = len(factors)
    delay_per_bar = animation_duration / n_factors if n_factors > 0 else 0

    # Build the bars HTML
    bars_html = []

    # Calculate positions - we need to track cumulative position
    # Start from w_idx and multiply through to get to w_mcap
    current_pos = w_idx

    # Store bar data for rendering
    bar_data = []
    for i, (label, multiplier) in enumerate(factors.items()):
        next_pos = current_pos * multiplier
        bar_data.append({
            'label': label,
            'multiplier': multiplier,
            'start': current_pos,
            'end': next_pos,
        })
        current_pos = next_pos

    # Find the range for scaling - include both w_idx and w_mcap
    all_positions = [w_idx, w_mcap] + [b['start'] for b in bar_data] + [b['end'] for b in bar_data]
    min_val = min(all_positions) * 0.85
    max_val = max(all_positions) * 1.15

    # Generate bar HTML (reversed order for bottom-to-top animation)
    for i, bar in enumerate(bar_data):
        # Animation delay: bottom bars animate first
        delay = (n_factors - 1 - i) * delay_per_bar

        # Determine color based on multiplier
        is_positive = bar['multiplier'] >= 1
        bar_color = '#2563eb' if is_positive else '#6b7280'  # Blue for positive, gray for negative

        # Calculate positions as percentages
        start_pct = ((bar['start'] - min_val) / (max_val - min_val)) * 100
        end_pct = ((bar['end'] - min_val) / (max_val - min_val)) * 100

        left_pct = min(start_pct, end_pct)
        width_pct = abs(end_pct - start_pct)

        # For very small bars (x1), show a thin line
        min_width = 0.3  # minimum visual width
        if width_pct < min_width:
            width_pct = min_width

        # Format multiplier text
        mult_text = f"x{bar['multiplier']:.2f}" if bar['multiplier'] != 1 else "x1"
        # Remove trailing zeros for cleaner display
        if mult_text.endswith('0') and '.' in mult_text:
            mult_text = mult_text.rstrip('0').rstrip('.')
            if mult_text == 'x1':
                mult_text = 'x1'

        # Text position - to the right of the bar for positive, left for negative
        text_left = max(start_pct, end_pct) + 1

        # Text color matches bar color
        text_color = bar_color

        bars_html.append(f'''
        <div class="bar-row" style="animation-delay: {delay:.3f}s;">
            <div class="bar-label">{bar['label']}</div>
            <div class="bar-container">
                <div class="bar" style="
                    left: {left_pct}%;
                    width: {width_pct}%;
                    background-color: {bar_color};
                "></div>
                <div class="bar-value" style="left: {text_left}%; color: {text_color};">{mult_text}</div>
            </div>
        </div>
        ''')

    # Calculate reference line positions
    idx_line_pct = ((w_idx - min_val) / (max_val - min_val)) * 100
    mcap_line_pct = ((w_mcap - min_val) / (max_val - min_val)) * 100

    # Generate axis ticks - nice round percentages
    import math
    range_val = max_val - min_val
    # Find a nice tick interval
    tick_interval = 0.01  # 1%
    if range_val > 0.05:
        tick_interval = 0.01
    elif range_val > 0.02:
        tick_interval = 0.005

    first_tick = math.ceil(min_val / tick_interval) * tick_interval
    ticks = []
    tick_val = first_tick
    while tick_val <= max_val:
        ticks.append(tick_val)
        tick_val += tick_interval

    ticks_html = ''.join([
        f'<div class="tick" style="left: {((v - min_val) / (max_val - min_val)) * 100}%;">{v:.0%}</div>'
        for v in ticks
    ])

    # Title HTML if provided
    title_html = f'<div class="chart-title">{title}</div>' if title else ''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title or "Weight Explainer"}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f0f0f0;
            padding: 40px;
            min-height: 100vh;
        }}

        .chart-container {{
            background: #e8e8e8;
            border-radius: 4px;
            padding: 30px 40px 20px 40px;
            max-width: 900px;
            margin: 0 auto;
        }}

        .chart-title {{
            text-align: center;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #333;
        }}

        .chart-area {{
            position: relative;
            padding-top: 35px;
            padding-bottom: 45px;
            margin-left: 220px;
        }}

        .bars-wrapper {{
            position: relative;
        }}

        .reference-line {{
            position: absolute;
            top: 0;
            bottom: 35px;
            width: 1px;
            background: #333;
            z-index: 10;
        }}

        .reference-line::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -3px;
            width: 7px;
            height: 1px;
            background: #333;
        }}

        .reference-label {{
            position: absolute;
            top: -25px;
            transform: translateX(-50%);
            font-size: 13px;
            font-weight: 400;
            font-style: italic;
            white-space: nowrap;
            color: #333;
        }}

        .reference-label-bottom {{
            position: absolute;
            bottom: 0;
            transform: translateX(-50%);
            font-size: 13px;
            font-weight: 400;
            font-style: italic;
            white-space: nowrap;
            color: #333;
        }}

        .bar-row {{
            display: flex;
            align-items: center;
            height: 32px;
            margin-bottom: 4px;
            opacity: 0;
            animation: fadeInSlide 0.4s ease-out forwards;
        }}

        @keyframes fadeInSlide {{
            from {{
                opacity: 0;
                transform: translateY(15px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .bar-label {{
            position: absolute;
            left: -220px;
            width: 210px;
            text-align: right;
            padding-right: 15px;
            font-size: 13px;
            color: #333;
            flex-shrink: 0;
        }}

        .bar-container {{
            flex: 1;
            position: relative;
            height: 100%;
        }}

        .bar {{
            position: absolute;
            height: 22px;
            top: 50%;
            transform: translateY(-50%);
            border-radius: 3px;
            min-width: 2px;
        }}

        .bar-value {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            font-size: 13px;
            font-weight: 600;
            white-space: nowrap;
        }}

        .x-axis {{
            position: relative;
            height: 25px;
            border-top: 1px solid #999;
            margin-top: 5px;
        }}

        .tick {{
            position: absolute;
            top: 8px;
            transform: translateX(-50%);
            font-size: 12px;
            color: #555;
        }}

        .idx-line {{
            left: {idx_line_pct}%;
        }}

        .mcap-line {{
            left: {mcap_line_pct}%;
        }}
    </style>
</head>
<body>
    <div class="chart-container">
        {title_html}
        <div class="chart-area">
            <!-- Reference lines -->
            <div class="reference-line idx-line">
                <div class="reference-label">W<sub>idx</sub> = {w_idx:.3%}</div>
            </div>
            <div class="reference-line mcap-line">
                <div class="reference-label-bottom">W<sub>mcap</sub> = {w_mcap:.3%}</div>
            </div>

            <!-- Bars -->
            <div class="bars-wrapper">
                {''.join(bars_html)}
            </div>

            <!-- X-axis -->
            <div class="x-axis">
                {ticks_html}
            </div>
        </div>
    </div>
</body>
</html>'''

    return html


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
        Series with factor names as index and multiplier values as values.
    w_idx : float
        The index weight (starting point).
    w_mcap : float
        The market cap weight (ending point).
    filepath : str
        Output file path.
    **kwargs
        Additional arguments passed to generate_weight_explainer_chart.

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
    # Sample data matching the image
    factors = pd.Series({
        'Min Weight': 1.05,
        'Turnover': 1.0,
        'Capacity Ratio': 1.23,
        'Industry / Country': 0.77,
        'Beta': 1.0,
        'High Impact Sector (HIS)': 1.01,
        'TPI MQ Score': 0.79,
        'TPI CP 2050 Alignment': 0.96,
        'TPI CP 2050 Not Aligned Penalty': 1.04,
        'FTSE Green Revenues': 0.58,
        'Fossil Fuel Reserves Intensity': 1.0,
        'Emissions Intensity Scope 3': 1.32,
        'Emissions Intensity Scope 1&2': 1.09,
        'Exclusions': 1.05,
    })

    # Generate and save the chart
    save_chart(
        factors=factors,
        w_idx=0.03446,  # 3.446%
        w_mcap=0.05029,  # 5.029%
        filepath="weight_explainer.html",
        title="Weight Explainer",
        animation_duration=3.0,
    )
    print("Chart saved to weight_explainer.html")
