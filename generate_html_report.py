#!/usr/bin/env python3
"""Generate HTML table report from ranked jobs API data with filters."""

import json
import urllib.request
from datetime import datetime
from pathlib import Path


def fetch_jobs_data(limit=60):
    """Fetch ranked jobs from API."""
    url = f"http://localhost:8001/jobs/ranked?limit={limit}"
    try:
        with urllib.request.urlopen(url) as response:
            return json.load(response)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def expertise_map():
    """Map expertise IDs to names."""
    return {
        1: "AI Agent",
        2: "LLM/Prompt",
        3: "Data Processing",
        4: "Backend",
        5: "Frontend",
        6: "DevOps",
        7: "Voice AI",
        8: "Testing",
    }


def format_budget(budget):
    """Format budget for display."""
    if budget is None:
        return "Hourly"
    return f"${budget:,.0f}"


def generate_html(jobs):
    """Generate HTML table report with filters."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Jobs Evaluation Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.5;
            color: #1f2937;
            background: #f9fafb;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 30px;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(79, 70, 229, 0.2);
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .header .meta {{
            opacity: 0.9;
            font-size: 0.9rem;
        }}
        .filters {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        .filter-group label {{
            font-size: 0.8rem;
            font-weight: 600;
            color: #6b7280;
        }}
        .filter-group select,
        .filter-group input {{
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 0.9rem;
            min-width: 150px;
        }}
        .filter-group input[type="number"] {{
            min-width: 100px;
        }}
        .filter-group input[type="checkbox"] {{
            width: auto;
            min-width: auto;
        }}
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .btn-reset {{
            background: #6b7280;
            color: white;
            margin-top: 20px;
        }}
        .btn-reset:hover {{
            background: #4b5563;
        }}
        .data-warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            font-size: 0.9rem;
            color: #92400e;
        }}
        .table-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}
        thead {{
            background: #f8fafc;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        th {{
            padding: 12px 10px;
            text-align: left;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid #e2e8f0;
            white-space: nowrap;
            cursor: pointer;
            user-select: none;
        }}
        th:hover {{
            background: #f1f5f9;
        }}
        th.sorted::after {{
            content: " ↕";
            opacity: 0.5;
        }}
        th.sorted.asc::after {{
            content: " ↑";
            opacity: 1;
        }}
        th.sorted.desc::after {{
            content: " ↓";
            opacity: 1;
        }}
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: middle;
        }}
        tr:hover {{
            background: #f8fafc;
        }}
        tr.expanded {{
            background: #f0f9ff;
        }}
        .job-title {{
            max-width: 250px;
            font-weight: 600;
        }}
        .job-title a {{
            color: #1f2937;
            text-decoration: none;
        }}
        .job-title a:hover {{
            color: #4f46e5;
            text-decoration: underline;
        }}
        .score {{
            text-align: center;
            font-weight: 700;
            font-size: 1.1rem;
        }}
        .score-high {{ color: #dc2626; }}
        .score-medium {{ color: #f59e0b; }}
        .score-low {{ color: #16a34a; }}
        .priority {{
            text-align: center;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.75rem;
            color: white;
        }}
        .priority-high {{ background: #dc2626; }}
        .priority-medium {{ background: #f59e0b; }}
        .priority-low {{ background: #16a34a; }}
        .job-age {{
            font-size: 0.8rem;
            color: #4b5563;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.7rem;
            font-weight: 600;
            background: #e5e7eb;
            color: #374151;
            margin: 1px;
        }}
        .badge-verified {{
            background: #dcfce7;
            color: #166534;
        }}
        .tech-tag {{
            display: inline-block;
            background: #f3f4f6;
            color: #374151;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.7rem;
            margin: 1px;
        }}
        .expand-toggle {{
            cursor: pointer;
            color: #4f46e5;
            font-weight: 600;
            font-size: 0.8rem;
            user-select: none;
        }}
        .expand-toggle:hover {{
            text-decoration: underline;
        }}
        .detail-row {{
            display: none;
            background: #f8fafc;
            border-left: 3px solid #4f46e5;
        }}
        .detail-row.active {{
            display: table-row;
        }}
        .detail-content {{
            padding: 15px;
            font-size: 0.85rem;
        }}
        .detail-content h4 {{
            color: #4f46e5;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }}
        .detail-content p {{
            margin-bottom: 15px;
            line-height: 1.6;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }}
        .reasoning-section {{
            margin-top: 15px;
            padding: 12px;
            background: #f0f9ff;
            border-radius: 6px;
            border-left: 3px solid #0ea5e9;
        }}
        .reasoning-section h5 {{
            color: #0369a1;
            margin-bottom: 8px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .reasoning-item {{
            margin-bottom: 10px;
            font-size: 0.85rem;
            line-height: 1.5;
        }}
        .reasoning-item:last-child {{
            margin-bottom: 0;
        }}
        .competition-cell {{
            text-align: center;
            font-size: 0.8rem;
        }}
        .no-jobs {{
            text-align: center;
            padding: 40px;
            color: #6b7280;
            font-size: 1.1rem;
        }}
        .col-score {{ width: 70px; }}
        .col-age {{ width: 120px; }}
        .col-priority {{ width: 80px; }}
        .col-budget {{ width: 80px; }}
        .col-applicants {{ width: 80px; }}
        .col-client {{ width: 70px; }}
        .col-reasoning {{ width: 200px; }}
        .col-actions {{ width: 80px; }}
    </style>
    <script>
        let allJobs = {json.dumps(jobs)};
        let sortColumn = 'job_age_hours';
        let sortDirection = 'asc';

        function renderTable(jobsToRender) {{
            const tbody = document.getElementById('jobs-table-body');
            tbody.innerHTML = '';

            if (jobsToRender.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="13" class="no-jobs">No jobs match your filters</td></tr>';
                return;
            }}

            jobsToRender.forEach((job, index) => {{
                const row = document.createElement('tr');
                row.id = 'job-' + job.job_id;
                row.className = 'job-row';

                const scoreClass = job.score_total >= 80 ? 'score-high' : (job.score_total >= 50 ? 'score-medium' : 'score-low');
                const priorityClass = job.priority === 'High' ? 'priority-high' : (job.priority === 'Medium' ? 'priority-medium' : 'priority-low');
                const clientBadge = job.client_payment_verified ? '<span class="badge badge-verified">✓</span>' : '-';

                let techTags = '';
                if (job.tech_stack && job.tech_stack.length > 0) {{
                    techTags = job.tech_stack.map(tech => `<span class="tech-tag">${{tech}}</span>`).join('');
                }}

                let reasoningSummary = job.reasoning_summary || 'No reasoning available';
                reasoningSummary = reasoningSummary.replace(/Budget:|Tech Fit:|Clarity:/g, '<strong>$&</strong>');

                row.innerHTML = `
                    <td><span class="expand-toggle" onclick="toggleDetail('${{job.job_id}}')">[+]</span></td>
                    <td class="job-title"><a href="${{job.url}}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">${{job.title}}</a></td>
                    <td class="score ${{scoreClass}}">${{job.score_total}}</td>
                    <td class="job-age"><small style="color: #9ca3af">${{job.job_age_hours}}h</small><br>${{job.job_age_string}}</td>
                    <td class="priority ${{priorityClass}}">${{job.priority}}</td>
                    <td>${{formatBudget(job.budget)}}</td>
                    <td class="reasoning-cell"><small>${{reasoningSummary}}</small></td>
                    <td><small>${{techTags}}</small></td>
                    <td class="competition-cell">${{job.applicant_count}}</td>
                    <td>${{clientBadge}}</td>
                `;

                tbody.appendChild(row);

                const detailRow = document.createElement('tr');
                detailRow.id = 'detail-' + job.job_id;
                detailRow.className = 'detail-row';

                let reasoningHtml = '<div class="reasoning-section">';
                reasoningHtml += '<h5>AI Evaluation Reasoning</h5>';

                if (job.reason_budget) {{
                    reasoningHtml += `<div class="reasoning-item"><strong>Budget Assessment:</strong> ${{job.reason_budget}}</div>`;
                }}
                if (job.reason_tech_fit) {{
                    reasoningHtml += `<div class="reasoning-item"><strong>Tech Stack Fit:</strong> ${{job.reason_tech_fit}}</div>`;
                }}
                if (job.reason_clarity) {{
                    reasoningHtml += `<div class="reasoning-item"><strong>Requirements Clarity:</strong> ${{job.reason_clarity}}</div>`;
                }}
                if (job.reason_client) {{
                    reasoningHtml += `<div class="reasoning-item"><strong>Client Reliability:</strong> ${{job.reason_client}}</div>`;
                }}
                if (job.reason_timeline) {{
                    reasoningHtml += `<div class="reasoning-item"><strong>Timeline Assessment:</strong> ${{job.reason_timeline}}</div>`;
                }}

                reasoningHtml += '</div>';

                detailRow.innerHTML = `
                    <td colspan="9">
                        <div class="detail-content">
                            <h4>Job Description</h4>
                            <p>${{(job.description || 'No description available').replace(/</g, '&lt;').replace(/>/g, '&gt;')}}</p>
                            ${{reasoningHtml}}
                        </div>
                    </td>
                `;
                tbody.appendChild(detailRow);
            }});
        }}

        function toggleDetail(jobId) {{
            const row = document.getElementById('job-' + jobId);
            const detailRow = document.getElementById('detail-' + jobId);
            const toggle = row.querySelector('.expand-toggle');
            
            if (detailRow.classList.contains('active')) {{
                detailRow.classList.remove('active');
                row.classList.remove('expanded');
                toggle.textContent = '[+]';
            }} else {{
                detailRow.classList.add('active');
                row.classList.add('expanded');
                toggle.textContent = '[-]';
            }}
        }}

        function applyFilters() {{
            const minScore = parseInt(document.getElementById('filter-min-score').value) || 0;
            const maxAgeHours = parseInt(document.getElementById('filter-max-age').value) || 999999;
            const minBudget = parseInt(document.getElementById('filter-min-budget').value) || 0;
            const priority = document.getElementById('filter-priority').value;
            const applicantsMax = parseInt(document.getElementById('filter-applicants').value) || 999;
            const clientVerifiedOnly = document.getElementById('filter-client-verified').checked;

            let filtered = allJobs.filter(job => {{
                if (job.score_total < minScore) return false;
                if (job.job_age_hours > maxAgeHours) return false;
                if (job.budget !== null && job.budget < minBudget) return false;
                if (priority !== 'all' && job.priority !== priority) return false;
                if (job.applicant_count > applicantsMax) return false;
                if (clientVerifiedOnly && !job.client_payment_verified) return false;
                return true;
            }});

            filtered.sort((a, b) => {{
                let aVal = a[sortColumn];
                let bVal = b[sortColumn];
                if (typeof aVal === 'string') aVal = aVal.toLowerCase();
                if (typeof bVal === 'string') bVal = bVal.toLowerCase();
                if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
                return 0;
            }});

            renderTable(filtered);
            document.getElementById('results-count').textContent = filtered.length;
        }}

        function resetFilters() {{
            document.getElementById('filter-min-score').value = '';
            document.getElementById('filter-max-age').value = '';
            document.getElementById('filter-min-budget').value = '';
            document.getElementById('filter-priority').value = 'all';
            document.getElementById('filter-applicants').value = '';
            document.getElementById('filter-client-verified').checked = false;
            applyFilters();
        }}

        function sortTable(column) {{
            if (sortColumn === column) {{
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            }} else {{
                sortColumn = column;
                sortDirection = 'asc';
            }}

            document.querySelectorAll('th').forEach(th => th.classList.remove('sorted', 'asc', 'desc'));
            const th = document.querySelector(`th[onclick="sortTable('${{column}}')"]`);
            if (th) {{
                th.classList.add('sorted', sortDirection);
            }}

            applyFilters();
        }}

        function formatBudget(budget) {{
            if (budget === null) return 'Hourly';
            return '$' + budget.toLocaleString();
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            document.getElementById('filter-min-score').addEventListener('change', applyFilters);
            document.getElementById('filter-max-age').addEventListener('input', applyFilters);
            document.getElementById('filter-min-budget').addEventListener('input', applyFilters);
            document.getElementById('filter-priority').addEventListener('change', applyFilters);
            document.getElementById('filter-applicants').addEventListener('input', applyFilters);
            document.getElementById('filter-client-verified').addEventListener('change', applyFilters);

            renderTable(allJobs);
            document.getElementById('total-jobs').textContent = allJobs.length;
            document.getElementById('results-count').textContent = allJobs.length;
        }});
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI Jobs Evaluation Report</h1>
            <div class="meta">
                Generated: {now} | Total Jobs: <span id="total-jobs">0</span> | Showing: <span id="results-count">0</span>
            </div>
        </div>

        <div class="data-warning">
            <strong>Data Notice:</strong> Applicant counts and client metrics show as 0 because the Apify dataset
            does not include this data when scraping. These fields are populated only when jobs are scraped with a custom solution.
            Job ages are calculated dynamically and represent time since posting.
        </div>

        <div class="filters">
            <div class="filter-group">
                <label>Min Score</label>
                <input type="number" id="filter-min-score" placeholder="50" min="0" max="100">
            </div>
            <div class="filter-group">
                <label>Max Age (hours)</label>
                <input type="number" id="filter-max-age" placeholder="168 (1 week)" min="0">
            </div>
            <div class="filter-group">
                <label>Min Budget ($)</label>
                <input type="number" id="filter-min-budget" placeholder="500" min="0">
            </div>
            <div class="filter-group">
                <label>Priority</label>
                <select id="filter-priority">
                    <option value="all">All</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Max Applicants</label>
                <input type="number" id="filter-applicants" placeholder="10" min="0">
            </div>
            <div class="filter-group">
                <label>Client Verified</label>
                <input type="checkbox" id="filter-client-verified">
            </div>
            <div>
                <button class="btn btn-reset" onclick="resetFilters()">Reset Filters</button>
            </div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="col-actions"></th>
                        <th onclick="sortTable('title')">Job Title</th>
                        <th class="col-score" onclick="sortTable('score_total')">Score</th>
                        <th class="col-age sorted asc" onclick="sortTable('job_age_hours')">Age</th>
                        <th class="col-priority" onclick="sortTable('priority')">Priority</th>
                        <th class="col-budget" onclick="sortTable('budget')">Budget</th>
                        <th class="col-reasoning">AI Reasoning</th>
                        <th>Tech Stack</th>
                        <th class="col-applicants" onclick="sortTable('applicant_count')">Applicants</th>
                        <th class="col-client">Verified</th>
                    </tr>
                </thead>
                <tbody id="jobs-table-body">
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
    """

    return html


def main():
    print("Fetching jobs data from API...")
    jobs = fetch_jobs_data(limit=100)

    if not jobs:
        print("No jobs data found!")
        return

    print(f"Found {len(jobs)} jobs")
    print("Generating HTML report...")

    html = generate_html(jobs)

    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "evaluation_report.html"
    output_file.write_text(html, encoding="utf-8")

    print(f"Report generated: {output_file.absolute()}")
    print(f"Open in browser: file://{output_file.absolute()}")


if __name__ == "__main__":
    main()