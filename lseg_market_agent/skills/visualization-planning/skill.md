---
name: visualization-planning
description: Visualization planning guidance for matching analytical intent to chart types.
version: 1.0.0
agent_name: graphing_agent
---

# Visualization Planning Guidance

Choose the chart type that best clarifies the analytical intent and minimizes
cognitive load. Do not force a complex chart when a simple one suffices (e.g.,
use a line chart for a single time series trend). The table below provides
guiding examples for mapping analytical intent to chart type. These are merely
suggestions; select the chart type that best fits the given analytical intent
and the data.

| Analytical Intent       | Suggested Chart Type    | Key Features             |
| ----------------------- | ----------------------- | ------------------------ |
| Trend inflection        | Candlestick with volume | Annotate regime changes, |
: detection               : overlay                 : mark support/resistance  :
| Price vs. fundamentals  | Multi-line chart with   | Overlay news context on  |
: divergence              : event markers           : price action             :
| Relative performance    | Line chart (indexed to  | Multiple securities vs.  |
:                         : 100)                    : benchmark                :
| Portfolio concentration | Treemap with            | Size by market value,    |
: risk                    : conditional formatting  : color by % NAV           :
| Sector                  | Sankey diagram or       | Show capital flow        |
: rotation/allocation     : waterfall chart         : direction                :
| Return attribution      | Waterfall chart         | Additive decomposition   |
:                         :                         : of performance drivers   :
| Risk distribution       | VaR histogram + box     | Show dispersion and tail |
:                         : plot                    : events                   :
| Correlation structure   | Heatmap with            | Identify factor          |
:                         : hierarchical clustering : exposures                :
| Risk vs. return         | Scatter/bubble chart    | Size bubbles by position |
: tradeoff                :                         : size or volume           :
| Scenario analysis       | Football field          | Show                     |
:                         : (valuation ranges)      : probability-weighted     :
:                         :                         : outcomes                 :
| Option positioning      | 2D/3D Greeks surfaces   | Delta/gamma profiles     |
:                         :                         : across strikes           :
| Time-series             | Stacked area chart      | Contribution over time   |
: decomposition           :                         :                          :