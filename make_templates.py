import re
import math

def get_ascii():
    with open(r'C:/Users/Jeremy yosep pohar/.gemini/antigravity-cli/brain/4f1b2980-852e-4d03-9b61-a1df23aaa5ad/.system_generated/tasks/task-48.log', 'r') as f:
        log_content = f.read()

    ascii_lines = []
    in_art = False
    for line in log_content.split('\n'):
        if '<!-- IMAGE BEGINS HERE -->' in line:
            in_art = True
            continue
        if '<!-- IMAGE ENDS HERE -->' in line:
            in_art = False
            continue
        if in_art:
            match = re.search(r'>(.*?)<', line)
            if match:
                text = match.group(1)
            elif line.startswith('<pre'):
                text = line.split('>', 1)[1]
            elif line.endswith('</pre>'):
                text = line.rsplit('<', 1)[0]
            else:
                text = line
            if re.match(r'^\d+: ', text):
                text = text.split(' ', 1)[1]
            if text.strip() or text.startswith('@'):
                 ascii_lines.append(text)

    ascii_clean = []
    for line in ascii_lines:
        if re.match(r'^\d+: ', line):
            line = line.split(' ', 1)[1]
        line = line.replace('&amp;', '&').replace('&', '&amp;')
        if len(line) > 10:
            ascii_clean.append(line)
    return ascii_clean

ascii_art = get_ascii()

# Layout parameters
width = 1160
height = 578
# Monospace font dimensions (approximate)
char_width = 8.4 # 14px font width
right_col_x = 520
max_right_x = 1130

# Colors for Dark Theme (Tokyo Night / Neofetch inspired)
dark_bg = "#161b22"
dark_avatar = "#bec5ce"
dark_label = "#ffa657"  # Orange
dark_value = "#a5d6ff"  # Light blue
dark_header = "#bec5ce" # Light gray/blue
dark_dots = "#474d55"

# Colors for Light Theme
light_bg = "#f6f8fa"
light_avatar = "#24292e"
light_label = "#d73a49" # Red
light_value = "#0366d6" # Blue
light_header = "#24292e"
light_dots = "#d1d5da"

def make_svg(mode):
    bg = dark_bg if mode == 'dark' else light_bg
    avatar_color = dark_avatar if mode == 'dark' else light_avatar
    label_color = dark_label if mode == 'dark' else light_label
    value_color = dark_value if mode == 'dark' else light_value
    header_color = dark_header if mode == 'dark' else light_header
    dots_color = dark_dots if mode == 'dark' else light_dots
    
    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
<style>
.avatar {{ font-family: "Courier New", monospace; font-size: 7.2px; fill: {avatar_color}; white-space: pre; }}
.header {{ font-family: "Consolas", "Courier New", monospace; font-size: 14px; font-weight: 700; fill: {header_color}; }}
.label {{ font-family: "Consolas", "Courier New", monospace; font-size: 14px; fill: {label_color}; }}
.value {{ font-family: "Consolas", "Courier New", monospace; font-size: 14px; fill: {value_color}; }}
.dots {{ font-family: "Consolas", "Courier New", monospace; font-size: 14px; fill: {dots_color}; }}
</style>
<rect x="0.5" y="0.5" rx="10" width="{width-1}" height="{height-1}" fill="{bg}" stroke="{dots_color}" stroke-width="1"/>
'''
    
    # Insert Avatar
    y = 20
    for a_line in ascii_art:
        svg += f'<text x="20" y="{y:.1f}" class="avatar" xml:space="preserve">{a_line}</text>\n'
        y += 11.2
        
    # Divider line
    svg += f'<line x1="490" y1="20" x2="490" y2="558" stroke="{dots_color}" stroke-width="1" stroke-dasharray="4,4"/>\n'
    
    # Right panel elements
    # Helper to generate a line with dots and a value
    lines = []
    
    def add_line(y_pos, label, value=""):
        dots_count = max(0, 68 - len(label) - len(value))
        dots = "." * dots_count
        lines.append(f'<text x="{right_col_x}" y="{y_pos}" class="label">. {label}</text>')
        lines.append(f'<text x="{right_col_x + (len(label)+2)*char_width}" y="{y_pos}" class="dots"> {dots} </text>')
        if value:
            lines.append(f'<text x="{max_right_x}" y="{y_pos}" class="value" text-anchor="end">{value}</text>')

    def add_header(y_pos, title):
        dashes = "-" * (68 - len(title))
        lines.append(f'<text x="{right_col_x}" y="{y_pos}" class="header">{title} {dashes}</text>')
        
    # Fill data
    y_idx = 40
    add_header(y_idx, "jeremy@pohar"); y_idx += 22
    add_line(y_idx, "OS:", "Windows 10"); y_idx += 22
    add_line(y_idx, "Uptime:", "4+ Years"); y_idx += 22
    add_line(y_idx, "Host:", "Creativeans"); y_idx += 22
    add_line(y_idx, "Kernel:", "Fullstack Developer Intern"); y_idx += 22
    add_line(y_idx, "IDE:", "VSCode, Android Studio"); y_idx += 30
    
    add_line(y_idx, "Languages.Programming:", "Python, JS, TS, Kotlin, Java, PHP, C#"); y_idx += 22
    add_line(y_idx, "Languages.Computer:", "SQL, HTML, CSS"); y_idx += 22
    add_line(y_idx, "Languages.Real:", "English, Indonesian"); y_idx += 30
    
    add_line(y_idx, "Hobbies.Tech:", "Cybersecurity, PC Building, Keyboards"); y_idx += 22
    add_line(y_idx, "Hobbies.Personal:", "Boxing, Movies, Learning"); y_idx += 30
    
    add_header(y_idx, "- Contact"); y_idx += 22
    add_line(y_idx, "Email:", "jeremy.yosep@gmail.com"); y_idx += 22
    add_line(y_idx, "LinkedIn:", "linkedin.com/in/jeremyjosephpohar"); y_idx += 22
    add_line(y_idx, "Instagram:", "@jeremyjpohar"); y_idx += 30
    
    add_header(y_idx, "- GitHub Stats"); y_idx += 22
    
    # Custom for github stats (they have two columns per line sometimes, but let's stick to simple layout)
    # The reference image has 2 columns: Repos ... 95 | Stars ... 342
    # We will do 1 column for simplicity or just format it carefully. Let's do 1 column, it looks cleaner and doesn't break with variables.
    add_line(y_idx, "Repos:", "{{ repos }}"); y_idx += 22
    add_line(y_idx, "Stars:", "{{ stars }}"); y_idx += 22
    add_line(y_idx, "Commits:", "{{ commits }}"); y_idx += 22
    add_line(y_idx, "Followers:", "{{ followers }}"); y_idx += 22
    
    # "Lines of Code on GitHub: . 446,276 ( 523,178++, 76,902-- )"
    # For this one, the string has multiple variables, so we will just put it all in the value
    add_line(y_idx, "Lines of Code:", "{{ loc }} ( {{ loc_added }}++, {{ loc_deleted }}-- )"); y_idx += 22
    
    svg += '\n'.join(lines)
    svg += '\n</svg>'
    
    with open(f'{mode}_mode_template.svg', 'w') as f:
        f.write(svg)

make_svg('light')
make_svg('dark')
print("Templates generated.")
