#!/usr/bin/env python3
"""Generate HTML report from ranked jobs API data."""

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
        1: "AI Agent Architecture",
        2: "LLM/Prompt Engineering",
        3: "Data Processing",
        4: "Backend Systems",
        5: "Frontend/Web",
        6: "DevOps/Infrastructure",
        7: "Voice & Real-Time AI",
        8: "Testing",
    }


def format_budget(budget):
    """Format budget for display."""
    if budget is None:
        return "Hourly"
    return f"${budget:,.0f}"


def format_duration(weeks):
    """Format duration for display."""
    if weeks is None:
        return "N/A"
    if weeks == 1:
        return "1 week"
    return f"{weeks} weeks"


def generate_expertise_badges(ids):
    """Generate HTML badges for expertise areas."""
    mapping = expertise_map()
    badges = []
    for eid in sorted(ids):
        name = mapping.get(eid, f"ID {eid}")
        badges.append(f'<span class="badge badge-expertise" style="background-color: {get_expertise_color(eid)};">{name}</span>')
    return " ".join(badges)


def get_expertise_color(eid):
    """Get color code for expertise ID."""
    colors = {
        1: "#4f46e5",  # AI Agent - indigo
        2: "#7c3aed",  # LLM - violet
        3: "#059669",  # Data Processing - emerald
        4: "#0891b2",  # Backend - cyan
        5: "#db2777",  # Frontend - pink
        6: "#ea580c",  # DevOps - orange
        7: "#16a34a",  # Voice - green
        8: "#6366f1",  # Testing - indigo-light
    }
    return colors.get(eid, "#6b7280")


def get_priority_color(priority):
    """Get color for priority badge."""
    colors = {
        "High": "#dc2626",      # red
        "Medium": "#f59e0b",    # amber
        "Low": "#16a34a",       # green
    }
    return colors.get(priority, "#6b7280")


def format_client_info(job):
    """Get HTML for client info section."""
    parts = []

    if job.get("client_payment_verified"):
        parts.append('<span class="badge badge-verified">✓ Payment Verified</span>')

    if job.get("client_rating"):
        rating = job["client_rating"]
        stars = "★" * min(5, int(rating))
        parts.append(f'<span class="badge badge-rating">{stars} {rating}</span>')

    if job.get("client_hire_rate"):
        parts.append(f'<span class="badge badge-rate">Hire Rate: {job["client_hire_rate"]}%</span>')

    if job.get("client_total_paid"):
        parts.append(f'<span class="badge badge-paid">Spent: ${job["client_total_paid"]:,.0f}</span>')

    return " ".join(parts) if parts else '<span class="text-muted">No client info available</span>'


def format_urls(urls):
    """Get HTML for URLs with security warning."""
    if not urls:
        return ""

    html = '<div class="urls-section">'
    html += '<div class="urls-warning">⚠️ External links - verify before visiting</div>'
    html += '<ul class="urls-list">'
    for url in urls:
        html += f'<li><code>{url}</code></li>'
    html += '</ul></div>'
    return html


def generate_html(jobs):
    """Generate HTML report."""
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.5;
            color: #1f2937;
            background: #f9fafb;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
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
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            text-align: center;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #4f46e5;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #6b7280;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .jobs-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 25px;
        }}
        @media (max-width: 768px) {{
            .jobs-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .job-card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }}
        .job-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
        }}
        .job-card.expanded {{
            cursor: default;
            transform: none;
        }}
        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 20px;
            background: #f8fafc;
            border-bottom: 1px solid #e5e7eb;
        }}
        .job-title {{
            flex: 1;
            padding-right: 15px;
        }}
        .job-title a {{
            color: #1f2937;
            text-decoration: none;
            font-size: 1.1rem;
            font-weight: 600;
            line-height: 1.3;
        }}
        .job-title a:hover {{
            color: #4f46e5;
        }}
        .job-meta {{
            text-align: right;
            min-width: 120px;
        }}
        .score {{
            font-size: 2rem;
            font-weight: 800;
            color: #4f46e5;
            line-height: 1;
        }}
        .priority {{
            margin-top: 5px;
            font-size: 0.85rem;
            font-weight: 600;
            padding: 2px 10px;
            border-radius: 12px;
            display: inline-block;
            color: white;
        }}
        .job-details {{
            padding: 20px;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            font-size: 0.9rem;
        }}
        .detail-label {{
            color: #6b7280;
            font-weight: 500;
        }}
        .detail-value {{
            color: #1f2937;
            font-weight: 500;
        }}
        .tech-stack {{
            margin: 15px 0;
        }}
        .tech-stack-label {{
            font-size: 0.85rem;
            color: #6b7280;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .tech-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .tech-tag {{
            background: #f3f4f6;
            color: #374151;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        .expertise-section {{
            margin: 15px 0;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
        }}
        .expertise-label {{
            font-size: 0.85rem;
            color: #6b7280;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            color: white;
        }}
        .badge-expertise {{
            font-weight: 500;
        }}
        .expand-toggle {{
            display: inline-block;
            margin-left: 10px;
            font-size: 0.75rem;
            color: #6b7280;
            background: #f3f4f6;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .job-details {{
            padding: 20px;
            display: none;
        }}
        .job-details.full {{
            display: block;
        }}
        .job-description {{
            display: none;
            margin: 15px 0;
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
            border-left: 3px solid #4f46e5;
            font-size: 0.9rem;
            line-height: 1.6;
            white-space: pre-wrap;
        }}
        .job-description.active {{
            display: block;
        }}
        .badge-verified {{
            background: #16a34a;
        }}
        .badge-rating {{
            background: #f59e0b;
        }}
        .badge-rate {{
            background: #4f46e5;
        }}
        .badge-paid {{
            background: #0891b2;
        }}
        .client-info {{
            margin-top: 15px;
            padding: 12px;
            background: #eff6ff;
            border-radius: 8px;
            border-left: 3px solid #4f46e5;
        }}
        .client-info-title {{
            font-size: 0.8rem;
            color: #6b7280;
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .client-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .urls-section {{
            margin-top: 15px;
            padding: 12px;
            background: #fef3c7;
            border-radius: 8px;
            border-left: 3px solid #f59e0b;
        }}
        .urls-warning {{
            font-size: 0.8rem;
            color: #d97706;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .urls-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .urls-list li {{
            padding: 4px 0;
            font-size: 0.8rem;
        }}
        .urls-list code {{
            background: #fffbeb;
            color: #d97706;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.75rem;
            word-break: break-all;
        }}
        .competition-info {{
            display: flex;
            justify-content: space-between;
            margin: 12px 0;
            padding: 10px;
            background: #f8fafc;
            border-radius: 8px;
        }}
        .competition-item {{
            text-align: center;
        }}
        .competition-value {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #1f2937;
        }}
        .competition-label {{
            font-size: 0.75rem;
            color: #6b7280;
            margin-top: 2px;
        }}
        .job-age {{
            display: inline-block;
            padding: 3px 8px;
            background: #e0e7ff;
            color: #4f46e5;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .text-muted {{
            color: #9ca3af;
            font-size: 0.8rem;
            font-style: italic;
        }}
        .click-hint {{
            font-size: 0.7rem;
            color: #9ca3af;
            text-align: right;
            margin-top: 5px;
        }}
    </style>
    <script>
        function toggleJobDetail(jobId) {{
            const card = document.getElementById('job-' + jobId);
            card.classList.toggle('expanded');
            const details = card.querySelector('.job-details');
            details.classList.toggle('full');
            const desc = card.querySelector('.job-description');
            desc.classList.toggle('active');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI Jobs Evaluation Report</h1>
            <div class="meta">
                Generated: {now} | Total Ranked Jobs: {len(jobs)}
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(jobs)}</div>
                <div class="stat-label">Total Ranked Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(1 for j in jobs if j["priority"] == "High")}</div>
                <div class="stat-label">High Priority</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(1 for j in jobs if 50 <= j["score_total"] < 80)}</div>
                <div class="stat-label">Medium Priority</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(1 for j in jobs if j.get("description_urls", []))}</div>
                <div class="stat-label">Jobs with URLs</div>
            </div>
        </div>

        <div class="jobs-grid">
    """

    for job in jobs:
        priority_color = get_priority_color(job["priority"])
        expertise_badges = generate_expertise_badges(job["matched_expertise_ids"])
        tech_tags = " ".join(
            f'<span class="tech-tag">{tech}</span>' for tech in job.get("tech_stack", [])
        )
        client_info = format_client_info(job)
        urls_html = format_urls(job.get("description_urls", []))

        job_age_hours = job.get("job_age_hours", 0)
        job_age_display = job.get("job_age_string", "Unknown")

        html += f"""
            <div class="job-card" id="job-{job['job_id']}" onclick="event.preventDefault(); toggleJobDetail('{job['job_id']}')">
                <div class="job-header">
                    <div class="job-title">
                        <a href="{job["url"]}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();">{job["title"]}</a>
                        <div class="click-hint">Click to expand</div>
                    </div>
                    <div class="job-meta">
                        <div class="score">{job["score_total"]}</div>
                        <span class="priority" style="background-color: {priority_color};">{job["priority"]}</span>
                    </div>
                </div>

                <div class="job-details">
                    <div class="detail-row">
                        <span class="detail-label">Posted:</span>
                        <span class="job-age">🕐 {job_age_display}</span>
                    </div>

                    <div class="competition-info">
                        <div class="competition-item">
                            <div class="competition-value">{job.get("applicant_count", 0)}</div>
                            <div class="competition-label">Applicants</div>
                        </div>
                        <div class="competition-item">
                            <div class="competition-value">{job.get("interviewing_count", 0)}</div>
                            <div class="competition-label">Interviewing</div>
                        </div>
                        <div class="competition-item">
                            <div class="competition-value">{'✓' if job.get("invite_only") else '✗'}</div>
                            <div class="competition-label">Invite Only</div>
                        </div>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">Budget:</span>
                        <span class="detail-value">{format_budget(job["budget"])}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Duration:</span>
                        <span class="detail-value">{format_duration(job.get("duration_weeks"))}</span>
                    </div>

                    <div class="client-info">
                        <div class="client-info-title">Client Information</div>
                        <div class="client-badges">{client_info}</div>
                    </div>

                    {urls_html}

                    <div class="tech-stack">
                        <div class="tech-stack-label">Tech Stack</div>
                        <div class="tech-tags">{tech_tags}</div>
                    </div>

                    <div class="expertise-section">
                        <div class="expertise-label">Matched Expertise Areas</div>
                        <div class="badges">{expertise_badges}</div>
                    </div>

                    <div class="job-description" id="desc-{job['job_id']}">
                        <strong>Job Description:</strong><br>
                        {job.get('description', 'No description available')}
                    </div>
                </div>
            </div>
        """

    html += """
        </div>
    </div>
</body>
</html>
    """

    return html


def main():
    """Main function."""
    print("Fetching jobs data from API...")
    jobs = fetch_jobs_data(limit=60)

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