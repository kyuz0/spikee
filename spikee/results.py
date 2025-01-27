import json
import os
import pandas as pd  # Required for Excel conversion
from collections import defaultdict
from tabulate import tabulate
import html

def read_jsonl_file(file_path):
    """Reads a JSONL file and returns a list of dictionaries."""
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]

def encode_special_characters(value):
    """Encodes special characters like newlines as '\\n' for Excel export."""
    if isinstance(value, str):
        return value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return value  # If not a string, return as-is

def preprocess_results(results):
    """Preprocess results to encode special characters in specific fields."""
    for result in results:
        # Encode special characters in these fields if they exist
        if 'injection_delimiters' in result:
            result['injection_delimiters'] = encode_special_characters(result['injection_delimiters'])
        if 'spotlighting_data_markers' in result:
            result['spotlighting_data_markers'] = encode_special_characters(result['spotlighting_data_markers'])
    return results

def convert_results_to_excel(args):
    result_file = args.result_file

    # Read results
    results = read_jsonl_file(result_file)

    # Preprocess results to encode special characters
    results = preprocess_results(results)

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Output Excel file
    output_file = os.path.splitext(result_file)[0] + ".xlsx"
    df.to_excel(output_file, index=False)

    print(f"Results successfully converted to Excel: {output_file}")

def escape_special_chars(text):
    """Escapes special characters for console output."""
    if text is None:
        return 'None'
    return repr(text)

def analyze_results(args):
    result_file = args.result_file
    output_format = args.output_format

    # Load the results data
    results = read_jsonl_file(result_file)

    total_entries = len(results)
    total_successes = sum(1 for entry in results if entry.get('success'))
    total_errors = sum(1 for entry in results if entry.get('error') not in [None, "No response received"])
    total_failures = total_entries - total_successes - total_errors

    attack_success_rate = (total_successes / total_entries) * 100 if total_entries else 0

    # Print general statistics
    print("\n=== General Statistics ===")
    print(f"Total Entries: {total_entries}")
    print(f"Successful Attacks: {total_successes}")
    print(f"Failed Attacks: {total_failures}")
    print(f"Errors: {total_errors}")
    print(f"Attack Success Rate: {attack_success_rate:.2f}%\n")

    # Initialize counters for breakdowns
    breakdown_fields = [
        'jailbreak_type',
        'instruction_type',
        'task_type',
        'position',
        'spotlighting_data_markers',
        'injection_delimiters',
        'lang',
        'suffix_id',
        'plugin'  
    ]

    breakdowns = {field: defaultdict(lambda: {'total': 0, 'successes': 0}) for field in breakdown_fields}

    # Initialize combination counters
    combination_counts = defaultdict(lambda: {'total': 0, 'successes': 0})

    for entry in results:
        success = entry.get('success', False)

        # Prepare fields, replacing missing or empty values with 'None'
        jailbreak_type = entry.get('jailbreak_type') or 'None'
        instruction_type = entry.get('instruction_type') or 'None'
        lang = entry.get('lang') or 'None'
        suffix_id = entry.get('suffix_id') or 'None'
        plugin = entry.get('plugin') or 'None'

        # Update combination counts
        combo_key = (jailbreak_type, instruction_type, lang, suffix_id, plugin)
        combination_counts[combo_key]['total'] += 1
        if success:
            combination_counts[combo_key]['successes'] += 1

        # Update breakdowns
        for field in breakdown_fields:
            value = entry.get(field, 'None') or 'None'
            breakdowns[field][value]['total'] += 1
            if success:
                breakdowns[field][value]['successes'] += 1

    # Function to print breakdowns
    def print_breakdown(field_name, data):
        print(f"=== Breakdown by {field_name.replace('_', ' ').title()} ===")
        table = []
        for value, stats in data.items():
            total = stats['total']
            successes = stats['successes']
            success_rate = (successes / total) * 100 if total else 0
            escaped_value = escape_special_chars(value)
            table.append([escaped_value, total, successes, f"{success_rate:.2f}%"])
        # Sort the table by success rate descending
        table.sort(key=lambda x: float(x[3].strip('%')), reverse=True)
        headers = [field_name.title(), 'Total', 'Successes', 'Success Rate']
        print(tabulate(table, headers=headers))
        print()

    # Print breakdowns
    for field in breakdown_fields:
        data = breakdowns[field]
        if data:
            print_breakdown(field, data)

    # Analyze combinations
    # Calculate success rates for each combination
    combination_stats = []
    for combo, stats in combination_counts.items():
        total = stats['total']
        successes = stats['successes']
        success_rate = (successes / total) * 100 if total else 0
        combination_stats.append({
            'jailbreak_type': combo[0],
            'instruction_type': combo[1],
            'lang': combo[2],
            'suffix_id': combo[3],
            'plugin': combo[4],
            'total': total,
            'successes': successes,
            'success_rate': success_rate
        })

    # Sort combinations by success rate
    combination_stats_sorted = sorted(combination_stats, key=lambda x: x['success_rate'], reverse=True)

    # Get top 10 most successful combinations
    top_10 = combination_stats_sorted[:10]

    # Get bottom 10 least successful combinations (excluding combinations with zero total)
    bottom_10 = [combo for combo in combination_stats_sorted if combo['total'] > 0][-10:]

    # Function to print combination stats
    def print_combination_stats(title, combo_list):
        print(f"\n=== {title} ===")
        table = []
        for combo in combo_list:
            jailbreak_type = escape_special_chars(combo['jailbreak_type'])
            instruction_type = escape_special_chars(combo['instruction_type'])
            lang = escape_special_chars(combo['lang'])
            suffix_id = escape_special_chars(combo['suffix_id'])
            plugin = escape_special_chars(combo['plugin'])
            total = combo['total']
            successes = combo['successes']
            success_rate = f"{combo['success_rate']:.2f}%"
            table.append([jailbreak_type, instruction_type, lang, suffix_id, plugin, total, successes, success_rate])
        headers = ['Jailbreak Type', 'Instruction Type', 'Language', 'Suffix ID', 'Plugin', 'Total', 'Successes', 'Success Rate']
        print(tabulate(table, headers=headers))
        print()

    # Print top 10 and bottom 10 combinations
    print_combination_stats("Top 10 Most Successful Combinations", top_10)
    print_combination_stats("Top 10 Least Successful Combinations", bottom_10)

    # Optionally, generate HTML output
    if output_format == 'html':
        generate_html_report(result_file, results, total_entries, total_successes, total_failures, total_errors, attack_success_rate, breakdowns, combination_stats_sorted)

def generate_html_report(result_file, results, total_entries, total_successes, total_failures, total_errors, attack_success_rate, breakdowns, combination_stats_sorted):
    import os
    from jinja2 import Template

    # Prepare data for the template
    template_data = {
        'result_file': result_file,
        'total_entries': total_entries,
        'total_successes': total_successes,
        'total_failures': total_failures,
        'total_errors': total_errors,
        'attack_success_rate': f"{attack_success_rate:.2f}%",
        'breakdowns': {},
        'top_combinations': combination_stats_sorted[:10],
        'bottom_combinations': [combo for combo in combination_stats_sorted if combo['total'] > 0][-10:]
    }

    # Prepare breakdown data
    for field, data in breakdowns.items():
        breakdown_list = []
        for value, stats in data.items():
            total = stats['total']
            successes = stats['successes']
            success_rate = (successes / total) * 100 if total else 0
            escaped_value = html.escape(str(value)) if value else 'None'
            # Replace newlines and tabs with visible representations
            escaped_value = escaped_value.replace('\n', '\\n').replace('\t', '\\t')
            breakdown_list.append({
                'value': escaped_value,
                'total': total,
                'successes': successes,
                'success_rate': f"{success_rate:.2f}%"
            })
        # Sort by success rate descending
        breakdown_list.sort(key=lambda x: float(x['success_rate'].strip('%')), reverse=True)
        template_data['breakdowns'][field] = breakdown_list

    # Load HTML template
    html_template = """
    <html>
    <head>
        <title>Results Analysis Report</title>
        <style>
            body { font-family: Arial, sans-serif; }
            h1, h2 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:hover { background-color: #f5f5f5; }
            pre { margin: 0; }
        </style>
    </head>
    <body>
        <h1>Results Analysis Report</h1>
        <p><strong>Result File:</strong> {{ result_file }}</p>
        <h2>General Statistics</h2>
        <ul>
            <li>Total Entries: {{ total_entries }}</li>
            <li>Successful Attacks: {{ total_successes }}</li>
            <li>Failed Attacks: {{ total_failures }}</li>
            <li>Errors: {{ total_errors }}</li>
            <li>Attack Success Rate: {{ attack_success_rate }}</li>
        </ul>
        {% for field, breakdown in breakdowns.items() %}
            <h2>Breakdown by {{ field.replace('_', ' ').title() }}</h2>
            <table>
                <tr>
                    <th>{{ field.title() }}</th>
                    <th>Total</th>
                    <th>Successes</th>
                    <th>Success Rate</th>
                </tr>
                {% for item in breakdown %}
                <tr>
                    <td><pre>{{ item.value }}</pre></td>
                    <td>{{ item.total }}</td>
                    <td>{{ item.successes }}</td>
                    <td>{{ item.success_rate }}</td>
                </tr>
                {% endfor %}
            </table>
        {% endfor %}
        <h2>Top 10 Most Successful Combinations</h2>
        <table>
            <tr>
                <th>Jailbreak Type</th>
                <th>Instruction Type</th>
                <th>Language</th>
                <th>Suffix ID</th>
                <th>Plugin<th>
                <th>Total</th>
                <th>Successes</th>
                <th>Success Rate</th>
            </tr>
            {% for combo in top_combinations %}
            <tr>
                <td>{{ combo.jailbreak_type }}</td>
                <td>{{ combo.instruction_type }}</td>
                <td>{{ combo.lang }}</td>
                <td>{{ combo.suffix_id }}</td>
                <td>{{ combo.plugin }}</td>
                <td>{{ combo.total }}</td>
                <td>{{ combo.successes }}</td>
                <td>{{ "%.2f%%" % combo.success_rate }}</td>
            </tr>
            {% endfor %}
        </table>
        <h2>Top 10 Least Successful Combinations</h2>
        <table>
            <tr>
                <th>Jailbreak Type</th>
                <th>Instruction Type</th>
                <th>Language</th>
                <th>Suffix ID</th>
                <th>Plugin<th>
                <th>Total</th>
                <th>Successes</th>
                <th>Success Rate</th>
            </tr>
            {% for combo in bottom_combinations %}
            <tr>
                <td>{{ combo.jailbreak_type }}</td>
                <td>{{ combo.instruction_type }}</td>
                <td>{{ combo.lang }}</td>
                <td>{{ combo.suffix_id }}</td>
                <td>{{ combo.plugin }}</td>
                <td>{{ combo.total }}</td>
                <td>{{ combo.successes }}</td>
                <td>{{ "%.2f%%" % combo.success_rate }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    # Render template
    template = Template(html_template)
    html_content = template.render(template_data)

    # Write to HTML file
    output_file = os.path.splitext(result_file)[0] + "_analysis.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML report generated: {output_file}")
