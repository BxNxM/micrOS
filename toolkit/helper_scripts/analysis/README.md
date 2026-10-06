# Analysis report

Regenerate the PDF from the existing `analysis_workdir` data:

```bash
python3 toolkit/helper_scripts/analysis/visualize_summary.py
```

The script resolves input and output paths relative to itself, so it can also
run from another directory. It uses the existing Matplotlib and packaging
dependencies. `system_report_analysis.bash` collects fresh inputs before
running the same generator.

`timeline_visualization.pdf` uses a uniform 14 x 8.5 inch landscape page size,
a dark theme, and consistent typography. Timeline charts retain every data
point, marking each measurement with a dot while spacing axis labels to fit.
Reference histories use separate
panels; each panel has its own vertical scale.

Tables and file lists wrap and continue onto additional pages without
shrinking text. Commit history retains the latest 60 entries, including full
hashes and messages. Device charts continue after 20 records per page, use
the same scale across continuations, and distinguish missing measurements
from zero. Complete loaded-module lists follow the charts.

PDF readers support page navigation and zoom, but cannot reliably provide
individually scrollable chart widgets. This report uses pagination instead.
Page dimensions, colors, and typography are centralized near the top of
`visualize_summary.py`.
